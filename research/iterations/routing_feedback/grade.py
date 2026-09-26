"""Independent pinned IFEval grading, admitted only after the R28 integrity audit."""

import argparse
import importlib.metadata
import json
import random
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
C = runpy.run_path(str(HERE / "common.py"))
A = runpy.run_path(str(HERE / "audit.py"))
PRIMARY = [
    ("jev_constant", "random_constant"),
    ("jev_constant", "confidence_constant"),
    ("jev_live", "jev_constant"),
    ("jev_live", "jev_shuffled"),
]


def grade(folder, grading, output, admission, report, private):
    import langdetect
    from langdetect import DetectorFactory

    m = json.loads((folder / "manifest.json").read_text())
    evidence = json.loads(admission.read_text())
    if not evidence["passed"] or evidence["manifest_sha256"] != C["sha"](folder / "manifest.json"):
        raise ValueError("Missing matching integrity admission")
    for name, sha in evidence["artifact_hashes"].items():
        if C["sha"](output / name) != sha:
            raise ValueError("Outputs changed after audit")
    if C["sha"](grading / "references.json") != m["references_sha256"]:
        raise ValueError("Reference binding changed")
    for name, sha in m["evaluator"].items():
        if C["sha"](grading / "instruction_following_eval" / name) != sha:
            raise ValueError("Evaluator binding changed")
    sys.path.insert(0, str(grading.resolve()))
    from instruction_following_eval import evaluation_lib as evaluator

    DetectorFactory.seed = 2800
    refs = {r["id"]: r for r in json.loads((grading / "references.json").read_text())}
    cases = json.loads((folder / "cases.json").read_text())
    if len(refs) != len(cases) or set(refs) != {c["id"] for c in cases}:
        raise ValueError("Reference coverage mismatch")
    for c in cases:
        r = refs[c["id"]]
        if r["prompt"] != c["prompt"] or r["prompt_sha256"] != C["digest"](c["prompt"]):
            raise ValueError("Reference prompt mismatch")
    rows = A["records"](output / "outputs.jsonl")
    grades = {}
    for row in rows:
        ref = refs[row["id"]]
        inp = evaluator.InputExample(
            **{k: ref[k] for k in ("key", "instruction_id_list", "prompt", "kwargs")}
        )
        random.seed(2800)
        strict = evaluator.test_instruction_following_strict(inp, {inp.prompt: row["text"]})
        random.seed(2800)
        loose = evaluator.test_instruction_following_loose(inp, {inp.prompt: row["text"]})
        grades[row["id"], row["arm"]] = dict(
            id=row["id"],
            arm=row["arm"],
            strict=bool(strict.follow_all_instructions),
            loose=bool(loose.follow_all_instructions),
            instruction_strict=[bool(x) for x in strict.follow_instruction_list],
            instruction_loose=[bool(x) for x in loose.follow_instruction_list],
        )
    plan = json.loads((output / "selection.json").read_text())["plan"]
    policies = C["select_outputs"](plan, rows)
    ids = sorted(refs)
    blocks = {i: b["index"] for b in plan["blocks"] for i in b["ids"]}
    block_ids = [blocks[i] for i in ids]
    vectors = {p: [grades[i, plan["policies"][p][i]]["strict"] for i in ids] for p in policies}
    native_by_id = {r["id"]: r for r in rows if r["arm"] == "native"}
    summaries = {}
    for name, selected in policies.items():
        g = [grades[r["id"], r["arm"]] for r in selected]
        repairs = [r for r in selected if r["arm"] != "native"]
        native_seconds = sum(r["work"]["seconds"] for r in native_by_id.values())
        summaries[name] = dict(
            n=len(g),
            strict=sum(x["strict"] for x in g),
            loose=sum(x["loose"] for x in g),
            strict_pct=100 * sum(x["strict"] for x in g) / len(g),
            instruction_strict=sum(sum(x["instruction_strict"]) for x in g),
            instruction_loose=sum(sum(x["instruction_loose"]) for x in g),
            instructions=sum(len(x["instruction_strict"]) for x in g),
            repairs=len(repairs),
            empty=sum(not r["text"].strip() for r in selected),
            length_stops=sum(r["finish_reason"] == "length" for r in selected),
            generated_tokens=sum(len(r["generated_token_ids"]) for r in selected),
            attributed_generation_seconds=native_seconds
            + sum(r["work"]["seconds"] for r in repairs),
            attributed_generated_tokens=sum(
                len(r["generated_token_ids"]) for r in native_by_id.values()
            )
            + sum(len(r["generated_token_ids"]) for r in repairs),
            attributed_processed_slots=sum(
                r["work"]["processed_token_slots"] for r in native_by_id.values()
            )
            + sum(r["work"]["processed_token_slots"] for r in repairs),
            jev_policy_dependency=name.startswith("jev_"),
        )
    contrasts = {}
    pairs = PRIMARY + [(p, "native") for p in policies if p != "native"]
    for p, b in dict.fromkeys(pairs):
        value = C["paired"](vectors[p], vectors[b], block_ids)
        value["primary"] = (p, b) in PRIMARY
        value["practical_success"] = (
            value["ci9875_pp"][0] > 0
            and value["delta_pp"] >= 2
            and all(x > 0 for x in value["block_delta_pp"])
        )
        contrasts[p + "__" + b] = value
    random_scores = []
    for seed in range(2801, 2901):
        chosen = {
            i
            for block in plan["blocks"]
            for i in C["order"](block["ids"], f"random/{seed}")[: len(block["ids"]) // 2]
        }
        random_scores.append(
            sum(grades[i, "constant" if i in chosen else "native"]["strict"] for i in ids)
        )
    sensitivity_ids = [i for i in ids if refs[i]["key"] not in m["overlap"]["near_keys"]]
    sensitivity = {
        p: dict(
            n=len(sensitivity_ids),
            strict=sum(grades[i, plan["policies"][p][i]]["strict"] for i in sensitivity_ids),
        )
        for p in policies
    }
    result = dict(
        protocol=m["protocol"],
        status="completed",
        cases=len(ids),
        upstream_cases=541,
        excluded_checker_keys=[1122, 1129],
        overlap=m["overlap"],
        scores=summaries,
        contrasts=contrasts,
        selection_pass=all(contrasts[p + "__" + b]["practical_success"] for p, b in PRIMARY[:2]),
        feedback_pass=all(contrasts[p + "__" + b]["practical_success"] for p, b in PRIMARY[2:]),
        random_100_seeds=dict(
            min_correct=min(random_scores),
            max_correct=max(random_scores),
            mean_correct=sum(random_scores) / len(random_scores),
        ),
        near_overlap_sensitivity=sensitivity,
        integrity=evidence,
        total_collected_generation_seconds=sum(r["work"]["seconds"] for r in rows),
        dependencies={
            n: importlib.metadata.version(n)
            for n in ("absl-py", "langdetect", "nltk", "immutabledict")
        },
        language_seed=langdetect.DetectorFactory.seed,
        grading_source_sha256=C["sha"](Path(__file__)),
        interpretation=(
            "Fresh shared potential outcomes; no independently measured policy "
            "latency or call savings"
        ),
    )
    C["dump"](private, list(grades.values()))
    private.chmod(0o600)
    C["dump"](report, result)
    print(
        json.dumps(
            {
                "cases": len(ids),
                "scores": {k: v["strict"] for k, v in summaries.items()},
                "selection_pass": result["selection_pass"],
                "feedback_pass": result["feedback_pass"],
            }
        )
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    for flag in ("folder", "grading", "output", "admission", "report", "private"):
        p.add_argument("--" + flag, type=Path, required=True)
    args = p.parse_args()
    grade(**vars(args))
