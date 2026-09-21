"""Descriptive R15 error, class, work and relevance diagnostics after full audit."""

import argparse
import hashlib
import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def describe(records, receipts, cases, arms):
    index = {(r["id"], r["mode"]): r for r in records}
    by_case = {c["id"]: c for c in cases}
    groups = {}
    for arm in arms:
        cells = {}
        for c in cases:
            row = index.get((c["id"], arm), {})
            good = row.get("status") == "complete" and row.get("label") == c["reference"]
            for key in (
                "all",
                f"depth-{c['depth']}-missing-{c['missing']}",
                f"missing-{c['missing']}",
                c["condition"],
            ):
                cell = cells.setdefault(key, dict(correct=0, total=0))
                cell["correct"] += int(good)
                cell["total"] += 1
        groups[arm] = cells
    contrasts = {}
    for baseline in ("native", "r14", "lexical", "prompt"):
        count = dict(fixes=0, regressions=0, wrong_to_wrong=0, label_changes=0)
        for c in cases:
            old, new = index.get((c["id"], baseline), {}), index.get((c["id"], "r15"), {})
            a, b = old.get("label"), new.get("label")
            ga = old.get("status") == "complete" and a == c["reference"]
            gb = new.get("status") == "complete" and b == c["reference"]
            count["fixes"] += int(gb and not ga)
            count["regressions"] += int(ga and not gb)
            count["label_changes"] += int(a != b)
            count["wrong_to_wrong"] += int(a != b and not ga and not gb)
        contrasts[baseline] = count
    confusion = {str(t): dict(tp=0, fp=0, tn=0, fn=0) for t in (0.5, 0.8)}
    squared = seconds = 0.0
    questions = 0
    usage = dict(input_tokens=0, output_tokens=0)
    for row in receipts:
        if row["status"] != "complete":
            continue
        ev = row["evaluation"]
        seconds += ev["seconds"]
        for key in usage:
            usage[key] += ev[key]
        for value, truth in zip(ev["scores"], by_case[row["id"]]["oracle_scores"], strict=True):
            questions += 1
            squared += (value - truth) ** 2
            for threshold in (0.5, 0.8):
                predicted = value > threshold
                confusion[str(threshold)][
                    ("t" if predicted == bool(truth) else "f") + ("p" if predicted else "n")
                ] += 1
    return dict(
        by_group=groups,
        contrasts=contrasts,
        score_confusion=confusion,
        brier=squared / questions if questions else None,
        score_questions=questions,
        api_seconds=seconds,
        api_usage=usage,
        successful_calls=sum(r["status"] == "complete" for r in receipts),
        failed_calls=sum(r["status"] != "complete" for r in receipts),
        constant_unknown_accuracy=sum(c["reference"] == "UNKNOWN" for c in cases) / len(cases),
        work={
            arm: dict(
                model_seconds=sum(r.get("seconds", 0) for r in records if r["mode"] == arm),
                prefill_tokens=sum(r.get("prefill_tokens", 0) for r in records if r["mode"] == arm),
                generated_tokens=sum(
                    r.get("generated_tokens", 0) for r in records if r["mode"] == arm
                ),
            )
            for arm in arms
        },
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--results", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    data = runpy.run_path(str(ROOT / "research/iterations/evidence_v2/data.py"))
    manifest = json.loads((args.manifest / "manifest.json").read_text())
    result = {}
    inputs = []
    for stage in ("test", "challenge"):
        worlds = args.manifest / f"{stage}.json"
        records = args.results / f"{stage}.jsonl"
        receipts = args.results / f"{stage}-scores.jsonl"
        inputs += [worlds, records, receipts]
        cases = [
            data["context"](w, cond)
            for w in json.loads(worlds.read_text())
            for cond in ("clean", "distracted")
        ]
        result[stage] = describe(load_rows(records), load_rows(receipts), cases, manifest["arms"])
    result["provenance"] = dict(
        scope="Post-hoc descriptive diagnostics; no new inference or hypothesis tests",
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        inputs={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
    )
    with args.output.open("x") as f:
        json.dump(result, f, indent=2, allow_nan=False)
        f.write("\n")
    print(json.dumps({"output": str(args.output), "stages": ["test", "challenge"]}))


if __name__ == "__main__":
    main()
