"""Post-start descriptive R25 feedback agreement, never a generator score."""

import argparse
import json
import math
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
C = runpy.run_path(str(ROOT / "research/iterations/gated_repair_retry/common.py"))


def summarize(rows):
    if len({r["id"] for r in rows}) != len(rows):
        raise ValueError("Duplicate diagnostic case")
    available = []
    for row in rows:
        if type(row["correct"]) is not bool or type(row["parseable"]) is not bool:
            raise ValueError("Invalid native grade")
        p = row["probability"]
        if p is not None:
            if type(p) not in (int, float) or not math.isfinite(p) or not 0 <= p <= 1:
                raise ValueError("Invalid actual feedback")
            available.append(row)
    errors = [r for r in available if not r["correct"]]
    correct = [r for r in available if r["correct"]]
    flagged = sum(r["probability"] < 0.5 for r in errors)
    false_flags = sum(r["probability"] < 0.5 for r in correct)
    return dict(
        cases=len(rows),
        available=len(available),
        missing_feedback=len(rows) - len(available),
        native_errors=len(errors),
        native_correct=len(correct),
        errors_flagged=flagged,
        errors_missed=len(errors) - flagged,
        correct_flagged=false_flags,
        correct_retained=len(correct) - false_flags,
        error_recall=flagged / len(errors) if errors else None,
        false_flag_rate=false_flags / len(correct) if correct else None,
        error_detection_auroc=(
            sum(
                (e["probability"] < c["probability"]) + 0.5 * (e["probability"] == c["probability"])
                for e in errors
                for c in correct
            )
            / (len(errors) * len(correct))
            if errors and correct
            else None
        ),
    )


def run(folder, output, primary_path):
    manifest = C["verify"](folder)
    primary = json.loads(primary_path.read_text())
    if (
        not primary["audited"]
        or not primary["tokenizer_replayed"]
        or primary["protocol"] != manifest["protocol"]
    ):
        raise ValueError("Completed matching primary audit required")
    C["C"]["verify_files"](output, primary["files"])
    cases = [c for c in json.loads((folder / "cases.json").read_text()) if c["split"] == "test"]
    ids = {c["id"] for c in cases}

    def index(rows):
        by_id = {r["id"]: r for r in rows}
        if set(by_id) != ids or len(by_id) != len(rows):
            raise ValueError("Missing, extra or duplicate evidence")
        return by_id

    grades = index([r for r in primary["grades"] if r["arm"] == "native"])
    feedback = index(
        [
            r
            for r in (
                json.loads(x)
                for x in (output / "feedback-availability.jsonl").read_text().splitlines()
            )
            if r["id"] in ids
        ]
    )
    rows = []
    for case in cases:
        ident = case["id"]
        f = feedback[ident]
        p = f["actual_probability_correct"]
        if f["source"] != ("missing_neutral" if p is None else "jev"):
            raise ValueError("Missing feedback was not identified")
        if grades[ident]["task"] != case["task"] or grades[ident]["split"] != "test":
            raise ValueError("Native grade has wrong task or split")
        rows.append(
            dict(
                id=ident,
                task=case["task"],
                correct=grades[ident]["correct"],
                parseable=grades[ident]["parseable"],
                probability=p,
            )
        )
    summaries = {}
    for task in ("all", "gsm8k", "arc"):
        selected = [r for r in rows if task == "all" or r["task"] == task]
        summaries[task] = dict(
            all_available=summarize(selected),
            parseable_native=summarize([r for r in selected if r["parseable"]]),
        )
    return dict(
        post_start_descriptive_supplement=True,
        generator_comparison=False,
        primary_sha256=C["sha"](primary_path),
        source_sha256=C["sha"](Path(__file__)),
        plan_sha256=C["sha"](ROOT / "research/gated-repair-feedback-diagnostic.md"),
        primary_changed=False,
        new_model_or_api_calls=0,
        threshold=0.5,
        summaries=summaries,
        note=(
            "Feedback agreement with the registered native-answer readout, "
            "not semantic adjudication of unparseable outputs or a Jev generator score."
        ),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--primary", type=Path, required=True)
    parser.add_argument("--save", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.freeze, args.output, args.primary)
    with args.save.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
