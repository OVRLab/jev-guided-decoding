"""Reconcile local-claim development and mechanical evidence without new inference."""

import argparse
import json
import runpy
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FORK = runpy.run_path(str(ROOT / "research/experiments/claim_forks.py"))


def opportunity(rows, *, planned):
    if len(rows) > planned or len({r["id"] for r in rows}) != len(rows):
        raise ValueError("Unexpected or duplicate proposal jobs")
    counts = Counter()
    kinds = Counter()
    for row in rows:
        counts["checkpoints"] += bool(row.get("checkpoint"))
        labels = [
            FORK["grade_claim"](row["case"], c["body"]) if c["body"] else None
            for c in row["candidates"]
        ]
        counts["raw_candidates"] += len(labels)
        assessed = [label for label in labels if label is not None]
        kinds.update(label["kind"] for label in assessed)
        counts["assessed_candidates"] += len(assessed)
        counts["unassessed_candidates"] += len(labels) - len(assessed)
        counts["correct_candidates"] += sum(label["correct"] for label in assessed)
        counts["incorrect_candidates"] += sum(not label["correct"] for label in assessed)
        truths = {label["correct"] for label in assessed}
        counts["worlds_with_correct_candidate"] += True in truths
        counts["any_correct_and_incorrect"] += truths == {True, False}
        counts["fully_assessed_mixed"] += len(assessed) == len(labels) and truths == {True, False}
    return {
        "planned": planned,
        "recorded": len(rows),
        "missing_worlds": planned - len(rows),
        **counts,
        "assessed_claim_kinds": dict(kinds),
        "checkpoint_coverage": counts["checkpoints"] / planned,
        "canonical_coverage": counts["assessed_candidates"] / counts["raw_candidates"]
        if counts["raw_candidates"]
        else 0,
        "interpretation": "Development proposal opportunity only, not completed critic scoring",
    }


def resources(rows):
    totals = Counter()
    for row in rows:
        proposals = [row["proposal"]] if "proposal" in row else row.get("proposals", [])
        for proposal in proposals:
            for key in (
                "generated_tokens",
                "decode_token_slots",
                "prefill_tokens",
                "forced_tokens",
            ):
                totals[key] += proposal.get(key, 0)
        trace = row.get("prefix_trace", [])
        totals["native_prefix_sampled_tokens"] += sum("token" in step for step in trace)
        totals["checkpoint_and_prefix_forwards"] += len(trace)
        totals["checkpoint_and_prefix_prefill_tokens"] += sum(t["prefill_tokens"] for t in trace)
        if "evaluation" in row:
            totals["successful_jev_calls"] += 1
            totals["jev_input_tokens"] += row["evaluation"]["input_tokens"]
            totals["jev_output_tokens"] += row["evaluation"]["output_tokens"]
            totals["jev_seconds"] += row["evaluation"]["seconds"]
        totals["unknown_usage_calls"] += row.get("status") == "scorer_error" and row.get(
            "usage_unknown", False
        )
        totals["job_seconds"] += row.get("seconds", 0)
    return dict(totals)


def read_rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def analyze(folder):
    v1 = read_rows(folder / "development-v1/runs.jsonl")
    v2 = read_rows(folder / "development-v2/runs.jsonl")
    completion = read_rows(folder / "development-v2-proposals/runs.jsonl")
    v1_summary = json.loads((folder / "development-v1/summary.json").read_text())
    v2_summary = json.loads((folder / "development-v2/summary.json").read_text())
    for name, rows, saved in (("v1", v1, v1_summary), ("v2", v2, v2_summary)):
        calculated = (FORK["GATE"]["analyze"] if name == "v1" else FORK["analyze"])(
            rows, planned=60
        )
        if any(saved[k] != v for k, v in calculated.items()):
            raise ValueError(f"Saved {name} aggregation differs")
    joined = v2 + completion
    # This new offline grading also labels the failed-call proposals; old raw is untouched.
    result = {
        "v1_summary_reproduced": True,
        "v2_summary_reproduced": True,
        "v2_full_development_opportunity": opportunity(joined, planned=60),
        "resources": {
            "v1": resources(v1),
            "v2_interrupted": resources(v2),
            "v2_unpaid_completion": resources(completion),
        },
        "gate_worlds_executed": 0,
        "confirmatory_quality_admitted": False,
        "source_hashes": {
            **FORK["source_hashes"](),
            str(Path(__file__).relative_to(ROOT)): FORK["sha"](__file__),
        },
    }
    mechanism_path = folder / "mechanism-v1/runs.jsonl"
    if mechanism_path.exists():
        mechanism = read_rows(mechanism_path)
        result["mechanism"] = {
            "worlds": len(mechanism),
            "complete": sum(r["status"] == "complete" for r in mechanism),
            "per_mode": {},
        }
        for mode in ("native", "zero", "jev", "shuffled", "synthetic"):
            choices = [c for r in mechanism for c in r["modes"] if c["mode"] == mode]
            result["mechanism"]["per_mode"][mode] = {
                "runs": len(choices),
                "nonzero_bias": sum(bool(c["plan"]["bias"]) for c in choices),
                "changed_draws": sum(c.get("changed_draws_of_64", 0) for c in choices),
                "distribution_draws": 64 * len(choices),
                "max_kl": max((c.get("measured_kl", 0) for c in choices), default=0),
                "final_frames_valid": sum(c.get("final_frame_valid", False) for c in choices),
                "actual_tail_generated_tokens": sum(
                    c.get("tail", {}).get("generated_tokens", 0) for c in choices
                ),
                "final_generated_tokens": sum(
                    c.get("final_proposal", {}).get("generated_tokens", 0) for c in choices
                ),
                "tail_and_final_prefill_tokens": sum(
                    c.get("tail", {}).get("prefill_tokens", 0)
                    + c.get("final_proposal", {}).get("prefill_tokens", 0)
                    for c in choices
                ),
                "padded_decode_slots": sum(
                    c.get("tail", {}).get("decode_token_slots", 0)
                    + c.get("final_proposal", {}).get("decode_token_slots", 0)
                    for c in choices
                ),
                "seconds_tail_and_final": sum(
                    c.get("tail", {}).get("seconds", 0)
                    + c.get("final_proposal", {}).get("seconds", 0)
                    for c in choices
                ),
            }
    result["input_hashes"] = {
        str(path.relative_to(folder)): FORK["sha"](path)
        for path in sorted(folder.rglob("*.json*"))
        if path.name in {"runs.jsonl", "summary.json", "metadata.json"}
    }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    FORK["write_json"](args.output, analyze(args.input))


if __name__ == "__main__":
    main()
