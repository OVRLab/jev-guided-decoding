"""Offline, aggregate-only audit of frozen generated-answer traces; no model calls."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

from jev_guided_decoding.framing import parse_frame


def gate(judgment):
    support, progress = judgment["support"], judgment["relevance"]
    if (
        any(
            type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 1
            for v in (support, progress)
        )
        or judgment.get("completion") is not None
    ):
        raise ValueError("invalid intermediate probability")
    if support >= 0.5 and progress >= 0.5:
        return "eligible"
    if support < 0.5 and progress < 0.5:
        return "both"
    return "support_only" if support < 0.5 else "progress_only"


def new_group():
    return {
        "runs": 0,
        "accepted_steps": 0,
        "proposal_batches": 0,
        "scored_batches": 0,
        "rejected_batches_with_support_passing_candidate": 0,
        "initial_scored_batches": 0,
        "initial_accepted_selection_differs_from_likelihood": 0,
        **{
            key: Counter()
            for key in (
                "reasoning_stops",
                "output_stops",
                "zero_step_stops",
                "step_count_histogram",
                "candidate_finish_reasons",
                "invalid_candidates",
                "candidate_gates",
                "initial_likelihood_winner_gate",
                "initial_batch_outcomes",
            )
        },
    }


def summarize(rows):
    groups, keys = {}, set()
    for row in rows:
        if row["key"] in keys:
            raise ValueError("duplicate job key")
        keys.add(row["key"])
        result, mode = row["result"], row["mode"]
        if mode not in ("single", "likelihood", "jev") or result["mode"] != mode:
            raise ValueError("unexpected mode")
        group = groups.setdefault(f"{row['id'].split('/')[0]}/{mode}", new_group())
        group["runs"] += 1
        group["accepted_steps"] += len(result["steps"])
        group["step_count_histogram"][str(len(result["steps"]))] += 1
        group["reasoning_stops"][result["reasoning_stop_reason"]] += 1
        group["output_stops"][result["stop_reason"]] += 1
        if not result["steps"]:
            group["zero_step_stops"][result["reasoning_stop_reason"]] += 1
        accepted = []
        for step, entry in enumerate(
            e for e in result["trace"] if e["event"] == "proposal" and e["phase"] == "step"
        ):
            group["proposal_batches"] += 1
            candidates = entry["proposal"]["candidates"]
            valid, seen = [], set()
            for i, candidate in enumerate(candidates):
                group["candidate_finish_reasons"][candidate["finish_reason"]] += 1
                frame = parse_frame("<step>" + candidate["text"])
                ids = tuple(candidate["token_ids"])
                reason = None
                if frame is None or frame.kind != "step":
                    reason = "parse_failure"
                elif not ids:
                    reason = "empty_tokens"
                elif candidate["finish_reason"] in ("cancelled", "time", "eos"):
                    reason = "disallowed_finish"
                elif ids in seen:
                    reason = "duplicate_tokens"
                elif frame.body in accepted:
                    reason = "repeated_accepted_body"
                if reason:
                    group["invalid_candidates"][reason] += 1
                else:
                    seen.add(ids)
                    valid.append(i)
            if valid != entry["valid_indices"]:
                raise ValueError("recorded valid indices disagree with frozen parsing policy")
            selected = entry["selected_index"]
            if selected is not None and selected not in valid:
                raise ValueError("invalid selection")
            if mode == "jev" and valid:
                if "evaluation" not in entry:
                    raise ValueError(
                        "unscored valid Jev batch; this audit expects successful calls"
                    )
                judgments = entry["evaluation"]["judgments"]
                if len(judgments) != len(valid):
                    raise ValueError("judgment count does not match candidates")
                group["scored_batches"] += 1
                categories = [gate(j) for j in judgments]
                group["candidate_gates"].update(categories)
                eligible = [
                    (i, j) for i, j in zip(valid, judgments, strict=True) if gate(j) == "eligible"
                ]
                expected = (
                    max(
                        eligible,
                        key=lambda ij: (
                            min(ij[1]["support"], ij[1]["relevance"]),
                            candidates[ij[0]]["mean_logprob"],
                        ),
                    )[0]
                    if eligible
                    else None
                )
                if selected != expected:
                    raise ValueError("recorded selection disagrees with frozen Jev policy")
                if selected is None and "progress_only" in categories:
                    group["rejected_batches_with_support_passing_candidate"] += 1
                if step == 0:
                    group["initial_scored_batches"] += 1
                    best = max(valid, key=lambda i: candidates[i]["mean_logprob"])
                    group["initial_likelihood_winner_gate"][categories[valid.index(best)]] += 1
                    if selected is not None and selected != best:
                        group["initial_accepted_selection_differs_from_likelihood"] += 1
            elif "evaluation" in entry:
                raise ValueError("unexpected scoring on an unscored batch")
            if step == 0:
                outcome = (
                    "no_valid_step"
                    if not valid
                    else ("all_rejected" if selected is None else "accepted")
                )
                group["initial_batch_outcomes"][outcome] += 1
            if selected is not None:
                accepted.append(parse_frame("<step>" + candidates[selected]["text"]).body)
        if accepted != result["steps"]:
            raise ValueError("accepted step ledger disagrees with selections")
    return {
        "schema": "frozen-trace-diagnostics-v1",
        "jobs": len(keys),
        "thresholds": {"support": 0.5, "progress": 0.5},
        "groups": {
            key: {
                k: dict(sorted(v.items())) if isinstance(v, Counter) else v
                for k, v in value.items()
            }
            for key, value in sorted(groups.items())
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = args.runs.read_bytes()
    summary = summarize(json.loads(line) for line in data.splitlines() if line.strip())
    summary["input_sha256"] = hashlib.sha256(data).hexdigest()
    summary["analyzer_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    from jev_guided_decoding import framing

    summary["parser_sha256"] = hashlib.sha256(Path(framing.__file__).read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(f"Audited {summary['jobs']} jobs; wrote aggregate counts to {args.output}")


if __name__ == "__main__":
    main()
