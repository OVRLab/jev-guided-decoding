"""Independent offline score reconstruction, with optional upstream IFBench evaluator."""

import argparse
import copy
import importlib.util
import json
import random
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
C = runpy.run_path(str(HERE / "common.py"))


def analyze(folder, output, evaluator):
    cases = json.loads((folder / "cases.json").read_text())
    refs = {r["id"]: r for r in json.loads((folder / "references.json").read_text())}
    m = json.loads((folder / "manifest.json").read_text())
    C["verify_files"](folder, m["datasets"])
    expected = {c["id"]: c for c in cases}
    if set(refs) != set(expected):
        raise ValueError("Reference coverage mismatch")
    spec = importlib.util.spec_from_file_location("ifbench_evaluation", evaluator)
    upstream = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(upstream)
    records = [json.loads(line) for line in (output / "outputs.jsonl").read_text().splitlines()]
    grades, seen = [], set()
    for r in records:
        pair = (r["model"], r["id"])
        if pair in seen or r["model"] not in m["models"]:
            raise ValueError("Duplicate or unexpected generation")
        seen.add(pair)
        case, ref = expected[r["id"]], refs[r["id"]]
        C["verify_readout"](case, r, thinking=m["models"][r["model"]]["thinking"])
        C["bind"](case, ref)
        if (r["task"], r["family"]) != (case["task"], case["family"]):
            raise ValueError("Task binding mismatch")
        text = r.get("final", "")
        if ref["kind"] == "ifbench":

            def score(mode, ref=ref, case=case, text=text):
                inp = upstream.InputExample(
                    key=ref["key"],
                    prompt=case["prompt"],
                    instruction_id_list=ref["instruction_id_list"],
                    kwargs=copy.deepcopy(ref["kwargs"]),
                )
                result = getattr(upstream, "test_instruction_following_" + mode)(
                    inp, {case["prompt"]: text}
                )
                return {
                    "all": bool(result.follow_all_instructions),
                    "instructions": [bool(x) for x in result.follow_instruction_list],
                }

            strict, loose = score("strict"), score("loose")
            g = {
                "correct": strict["all"],
                "parseable": bool(text),
                "strict": strict,
                "loose": loose,
            }
        else:
            g = C["grade"](ref, text)
        grades.append(
            {k: r[k] for k in ("id", "task", "family", "model", "status", "prompt_sha256")}
            | g
            | {
                "finish_reason": r.get("finish_reason"),
                "output_tokens": len(r.get("generated_token_ids", [])),
                "input_tokens": len(r.get("prompt_token_ids", [])),
                "seconds": r.get("seconds", 0),
            }
        )
    summaries = {
        name: C["summarize"](cases, [r for r in grades if r["model"] == name])
        for name in m["models"]
    }
    for name, tasks in summaries.items():
        for task, s in tasks.items():
            rows = [r for r in grades if (r["model"], r["task"]) == (name, task)]
            s.update(
                unparseable=sum(not r["parseable"] for r in rows),
                length_stops=sum(r["finish_reason"] == "length" for r in rows),
                output_tokens=sum(r["output_tokens"] for r in rows),
                generation_seconds=sum(r["seconds"] for r in rows),
            )
            if task == "ifbench":
                s["loose_correct"] = sum(r["loose"]["all"] for r in rows)
    comparisons = {}
    by_pair = {(r["model"], r["id"]): r for r in grades}
    models = list(m["models"])
    for task in summaries[models[0]]:
        ids = [c["id"] for c in cases if c["task"] == task]
        diffs = [
            int(by_pair.get((models[1], i), {}).get("correct", False))
            - int(by_pair.get((models[0], i), {}).get("correct", False))
            for i in ids
        ]
        rng = random.Random(2301)
        boot = sorted(sum(rng.choices(diffs, k=len(diffs))) / len(diffs) for _ in range(10000))
        comparisons[task] = {
            "difference_3b_minus_1b": sum(diffs) / len(diffs),
            "exploratory_95_interval": [boot[249], boot[9749]],
            "problem_count": len(ids),
            "complete_pairs": sum(all((name, i) in by_pair for name in models) for i in ids),
        }
    return {
        "protocol": m["protocol"],
        "summaries": summaries,
        "paired_differences": comparisons,
        "grades": grades,
        "input_files": {p.name: C["sha"](p) for p in sorted(output.iterdir()) if p.is_file()},
        "ifbench_evaluator_sha256": C["sha"](evaluator),
        "score_type": "development diagnostic; not official benchmark or Jev improvement",
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--freeze", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--ifbench-evaluator", type=Path, required=True)
    p.add_argument("--save", type=Path, required=True)
    a = p.parse_args()
    C["dump"](a.save, analyze(a.freeze, a.output, a.ifbench_evaluator))
