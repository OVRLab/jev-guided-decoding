"""Prospective R25 v4 retention replay, including explicit unavailable feedback."""

import argparse
import json
import math
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
C = runpy.run_path(str(Path(__file__).resolve().with_name("common.py")))


def route(probability):
    if probability is None:
        return "native"
    if (
        type(probability) not in (int, float)
        or not math.isfinite(probability)
        or not 0 <= probability <= 1
    ):
        raise ValueError("Invalid probability")
    return "native" if probability >= 0.5 else "repair"


def replay(rows, probabilities, arm):
    indexed = {}
    for row in rows:
        if row["arm"] not in ("native", arm):
            continue
        key = row["id"], row["arm"]
        if key in indexed:
            raise ValueError("Duplicate outcome")
        indexed[key] = row
    if set(indexed) != {(ident, name) for ident in probabilities for name in ("native", arm)}:
        raise ValueError("Missing/extra branch outcome")
    return [
        dict(
            id=ident,
            arm="retained_" + arm,
            correct=indexed[ident, "native" if route(p) == "native" else arm]["correct"],
        )
        for ident, p in sorted(probabilities.items())
    ]


def run(folder, output, primary_path, registration):
    m = C["verify"](folder)
    registered = json.loads(registration.read_text())
    C["C"]["verify_files"](ROOT, registered["sources"])
    if registered["threshold"] != 0.5 or registered["baseline_manifest_sha256"] != C["sha"](
        folder / "manifest.json"
    ):
        raise ValueError("Retention registration mismatch")
    primary = json.loads(primary_path.read_text())
    C["C"]["verify_files"](output, primary["files"])
    cases = [c for c in json.loads((folder / "cases.json").read_text()) if c["split"] == "test"]
    ids = {c["id"] for c in cases}
    jobs = [json.loads(x) for x in (output / "jobs.jsonl").read_text().splitlines()]
    if any(r["at"] <= max(registered["at"], m["at"]) for r in jobs if r["id"] in ids):
        raise ValueError("Supplement not frozen before test")
    probs = {
        r["id"]: r["actual_probability_correct"]
        for r in [
            json.loads(x) for x in (output / "feedback-availability.jsonl").read_text().splitlines()
        ]
        if r["id"] in ids
    }
    if set(probs) != ids or not primary["audited"] or primary["protocol"] != m["protocol"]:
        raise ValueError("Primary/probability coverage mismatch")
    arms = ["blind", "text", "live_mean", "constant_mean"] + [
        f"{mode}/{seed}" for mode in ("live", "constant") for seed in m["seeds"]
    ]
    grades = primary["grades"] + [r for arm in arms for r in replay(primary["grades"], probs, arm)]
    summaries = {}
    effects = {}
    for task in ("all", "gsm8k", "arc"):
        cohort = [c for c in cases if task == "all" or c["task"] == task]
        cohort_ids = {c["id"] for c in cohort}
        group = [r for r in grades if r["id"] in cohort_ids]
        summaries[task] = dict(
            cases=len(cohort),
            repair_cases=sum(route(probs[c["id"]]) == "repair" for c in cohort),
            accuracies={
                arm: sum(r["correct"] for r in group if r["arm"] == arm) / len(cohort)
                for arm in ["native", *["retained_" + a for a in arms]]
            },
        )
        effects[task] = {
            f"live-vs-{base}": C["paired"](cohort, group, "retained_live_mean", base)
            for base in ("native", "retained_constant_mean", "retained_blind", "retained_text")
        }
    return dict(
        offline_replay=True,
        measured_skipped_execution=False,
        jev_calls_saved=0,
        missing_feedback_ids=sorted(ident for ident, p in probs.items() if p is None),
        continuation_manifest_sha256=C["sha"](folder / "manifest.json"),
        threshold=0.5,
        summaries=summaries,
        effects=effects,
        branches={ident: route(p) for ident, p in sorted(probs.items())},
        primary_sha256=C["sha"](primary_path),
        registration_sha256=C["sha"](registration),
        note="Primary full-repair endpoints unchanged; no new model or API inference",
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--freeze", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--primary", type=Path, required=True)
    p.add_argument("--registration", type=Path, required=True)
    p.add_argument("--save", type=Path, required=True)
    a = p.parse_args()
    C["dump"](a.save, run(a.freeze, a.output, a.primary, a.registration))
