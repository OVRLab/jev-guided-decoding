"""Post-hoc descriptive R14 diagnostics; run after the independent full audit."""

import argparse
import hashlib
import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def describe(rows, scores, cases):
    if any(r["status"] != "complete" for r in rows + scores):
        raise ValueError("Incomplete cohort: use the primary planned-denominator analysis")
    classes, by_arm = {}, {}
    for row in rows:
        arm, key = row["mode"], row["id"]
        if key in by_arm.setdefault(arm, {}):
            raise ValueError("Duplicate outcome")
        by_arm[arm][key] = row["label"]
        cell = classes.setdefault(arm, {}).setdefault(
            str(cases[key]["missing"]), {"correct": 0, "total": 0}
        )
        cell["total"] += 1
        cell["correct"] += row["label"] == cases[key]["reference"]
    if any(set(values) != set(cases) for values in by_arm.values()):
        raise ValueError("Incomplete arm")
    if len(scores) != len(cases) or {r["id"] for r in scores} != set(cases):
        raise ValueError("Incomplete score cohort")
    fixes = regressions = changes = 0
    for key, case in cases.items():
        native, jev = by_arm["native"][key], by_arm["jev"][key]
        changes += native != jev
        fixes += native != case["reference"] and jev == case["reference"]
        regressions += native == case["reference"] and jev != case["reference"]
    confusion = dict(tp=0, fp=0, tn=0, fn=0)
    squared_error, questions, seconds = 0.0, 0, 0.0
    usage = dict(input_tokens=0, output_tokens=0)
    for row in scores:
        evaluation = row["evaluation"]
        seconds += evaluation["seconds"]
        for key in usage:
            usage[key] += evaluation[key]
        for score, truth in zip(
            evaluation["scores"], cases[row["id"]]["oracle_scores"], strict=True
        ):
            if not 0 <= score <= 1:
                raise ValueError("Invalid relevance probability")
            predicted = score > 0.5
            confusion[("t" if predicted == bool(truth) else "f") + ("p" if predicted else "n")] += 1
            squared_error += (score - truth) ** 2
            questions += 1
    return dict(
        classes=classes,
        test_api_seconds=seconds,
        test_api_usage=usage,
        jev_native_fixes=fixes,
        jev_native_regressions=regressions,
        label_changes=changes,
        noul_questions=questions,
        brier=squared_error / questions,
        span_confusion=confusion,
        constant_unknown_accuracy=sum(c["reference"] == "UNKNOWN" for c in cases.values())
        / len(cases),
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = runpy.run_path(str(ROOT / "research/experiments/evidence_data.py"))
    world_file = args.manifest / "test.json"
    cases = {}
    for world in json.loads(world_file.read_text()):
        for condition in ("clean", "distracted"):
            case = data["context"](world, condition)
            cases[case["id"]] = case
    files = [args.results / name for name in ("test.jsonl", "test-scores.jsonl")]
    result = describe(
        *[[json.loads(line) for line in path.read_text().splitlines()] for path in files], cases
    )
    result["provenance"] = {
        "analysis": "post-hoc descriptive; no new inference or hypothesis test",
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "input_hashes": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [world_file, *files]
        },
        "class_key": "False = answerable; True = missing final containment link",
    }
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"output": str(args.output), "questions": result["noul_questions"]}))


if __name__ == "__main__":
    main()
