"""R25 registered recovery/damage and compute summaries from audited outcomes.

This helper adds no grading rules, thresholds, selection or inference.
"""

import argparse
import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
C = runpy.run_path(str(ROOT / "research/iterations/gated_repair_retry/common.py"))
R = runpy.run_path(str(ROOT / "research/iterations/gated_repair_retry/retention.py"))


def summarize(cases, rows, grades, probabilities, components, *, retain=False):
    ids = {c["id"] for c in cases}
    if len(ids) != len(cases) or not ids or set(probabilities) != ids:
        raise ValueError("Case/probability coverage mismatch")
    required = {(ident, arm) for ident in ids for arm in ["native", *components]}

    def index(records):
        selected = [r for r in records if r["id"] in ids and (r["id"], r["arm"]) in required]
        result = {(r["id"], r["arm"]): r for r in selected}
        if len(selected) != len(result) or set(result) != required:
            raise ValueError("Missing or duplicate component coverage")
        return result

    raw, scored = index(rows), index(grades)
    chosen = []
    for ident in sorted(ids):
        use_native = retain and R["route"](probabilities[ident]) == "native"
        for arm in components:
            chosen.append((ident, "native" if use_native else arm))
    divisor = len(components)
    native_correct = sum(scored[ident, "native"]["correct"] for ident in ids)
    correct = sum(scored[k]["correct"] for k in chosen) / divisor
    recovered = (
        sum(
            not scored[ident, "native"]["correct"] and scored[ident, arm]["correct"]
            for ident, arm in chosen
        )
        / divisor
    )
    damaged = (
        sum(
            scored[ident, "native"]["correct"] and not scored[ident, arm]["correct"]
            for ident, arm in chosen
        )
        / divisor
    )
    if correct != native_correct + recovered - damaged:
        raise ValueError("Recovery/damage identity failed")
    return dict(
        cases=len(ids),
        seed_components=components,
        correct=correct,
        accuracy=correct / len(ids),
        native_correct=native_correct,
        native_errors=len(ids) - native_correct,
        recovered=recovered,
        damaged=damaged,
        unparseable=sum(not scored[k]["parseable"] for k in chosen) / divisor,
        length_stops=sum(raw[k]["finish_reason"] == "length" for k in chosen) / divisor,
        changed_token_sequences=sum(
            raw[k]["generated_token_ids"] != raw[k[0], "native"]["generated_token_ids"]
            for k in chosen
        )
        / divisor,
        selected_final_tokens=sum(len(raw[k]["generated_token_ids"]) for k in chosen) / divisor,
        repair_cases=sum(R["route"](probabilities[i]) == "repair" for i in ids)
        if retain
        else len(ids),
        missing_feedback_cases=sum(p is None for p in probabilities.values()),
        offline_retention_replay=retain,
        measured_execution_savings=False,
        actual_native_generation_seconds=sum(raw[i, "native"]["seconds"] for i in ids),
        actual_repair_generation_seconds_seed_mean=sum(
            raw[i, arm]["seconds"] for i in ids for arm in components
        )
        / divisor,
        actual_repair_processed_tokens_seed_mean=sum(
            raw[i, arm]["processed_tokens"] for i in ids for arm in components
        )
        / divisor,
        actual_repair_generated_tokens_seed_mean=sum(
            len(raw[i, arm]["generated_token_ids"]) for i in ids for arm in components
        )
        / divisor,
    )


def run(folder, output, primary_path):
    manifest = C["verify"](folder)
    primary = json.loads(primary_path.read_text())
    if not primary["audited"] or not primary["tokenizer_replayed"]:
        raise ValueError("Completed tokenizer audit required")
    if primary["protocol"] != manifest["protocol"]:
        raise ValueError("Primary protocol mismatch")
    C["C"]["verify_files"](output, primary["files"])
    cases = [c for c in json.loads((folder / "cases.json").read_text()) if c["split"] == "test"]
    ids = {c["id"] for c in cases}

    def read(name):
        return [json.loads(x) for x in (output / name).read_text().splitlines()]

    rows = read("outputs.jsonl")
    availability = [r for r in read("feedback-availability.jsonl") if r["id"] in ids]
    probs = {r["id"]: r["actual_probability_correct"] for r in availability}
    if len(availability) != len(ids) or set(probs) != ids:
        raise ValueError("Availability mismatch")
    arms = {"blind": ["blind"], "text": ["text"]}
    for mode in ["constant", "live", "shuffled", "inverted"]:
        components = [f"{mode}/{seed}" for seed in manifest["seeds"]]
        arms.update({c: [c] for c in components})
        arms[mode + "_mean"] = components
    result = {}
    for task in ["all", "gsm8k", "arc"]:
        cohort = [c for c in cases if task == "all" or c["task"] == task]
        probabilities = {c["id"]: probs[c["id"]] for c in cohort}
        result[task] = {}
        for arm, components in arms.items():
            for retain in (
                [False, True]
                if arm.split("/")[0]
                not in ("shuffled", "inverted", "shuffled_mean", "inverted_mean")
                else [False]
            ):
                result[task][("retained_" if retain else "") + arm] = summarize(
                    cohort, rows, primary["grades"], probabilities, components, retain=retain
                )
    return dict(
        protocol=manifest["protocol"],
        primary_sha256=C["sha"](primary_path),
        source_sha256=C["sha"](Path(__file__)),
        summaries=result,
        note=(
            "Per-case seed means, all planned cases retained; timings exclude API, training "
            "and loading; offline retention does not establish execution savings."
        ),
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--freeze", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--primary", type=Path, required=True)
    p.add_argument("--save", type=Path, required=True)
    a = p.parse_args()
    C["dump"](a.save, run(a.freeze, a.output, a.primary))
