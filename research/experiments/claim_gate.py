"""Freeze, run and independently analyze a bounded local-claim critic study."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import math
import os
import random
import runpy
import subprocess
import time
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from jev_guided_decoding.experiment_budget import InputTokenBudget
from jev_guided_decoding.framing import parse_frame
from jev_guided_decoding.jev import load_api_key
from jev_guided_decoding.local_claims import LocalClaimScorer
from jev_guided_decoding.types import Candidate, Request, ScorerError

ROOT = Path(__file__).resolve().parents[2]
DATA = runpy.run_path(str(Path(__file__).with_name("claim_worlds.py")))
MODEL = "ibm-granite/granite-4.0-1b"
REVISION = "6a7381ba1f54d684ff508d991aeb7dc580157103"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(value, indent=2, allow_nan=False) + "\n")


def source_hashes():
    paths = sorted((ROOT / "src").rglob("*.py")) + [
        Path(__file__),
        Path(__file__).with_name("claim_worlds.py"),
    ]
    return {str(p.relative_to(ROOT)): sha(p) for p in paths}


def prepare(output):
    output.mkdir(parents=True, exist_ok=False)
    for split, count in (("development", 60), ("gate", 100)):
        write_json(output / f"{split}.json", DATA["worlds"](split, count))
    manifest = {
        "schema": "local-claim-gate-v1",
        "created_at": datetime.now(UTC).isoformat(),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "source_hashes": source_hashes(),
        "model": MODEL,
        "revision": REVISION,
        "jev": "jev-1.13.0",
        "temperature": 1.0,
        "top_p": 1.0,
        "candidates": 3,
        "chunk_tokens": 48,
        "seconds_per_batch": 45,
        "stage_seconds": 1800,
        "seed_base": 72191,
        "max_jev_calls": 160,
        "jev_ledger_cap_usd": 3,
        "dataset_hashes": {s: sha(output / f"{s}.json") for s in ("development", "gate")},
        "gates": {
            "all_jobs_completed": True,
            "min_canonical_coverage": 0.8,
            "min_mixed_batches": 25,
            "ranking_95pct_lower_bound_above": 0,
            "selected_false_or_uncertified_acceptance_95pct_upper_bound_max": 0.15,
            "acceptance_support_threshold": 0.8,
            "assessability_threshold": 0.5,
            "bootstrap_draws": 5000,
            "bootstrap_seed": 19371,
        },
        "limitations": "Synthetic full-claim entailment, not natural-language proof verification. "
        "Renderer templates differ; elementary logical motifs intentionally overlap.",
    }
    write_json(output / "manifest.json", manifest)
    print("Prepared immutable development/gate data and execution manifest.", flush=True)


def wilson_upper(bad, count):
    if not count:
        return 1.0
    z = 1.6448536269514722  # one-sided 95%; unit is one selected claim per independent world
    p = bad / count
    return (
        p + z * z / (2 * count) + z * math.sqrt(p * (1 - p) / count + z * z / (4 * count * count))
    ) / (1 + z * z / count)


def analyze(rows, *, planned):
    if len({r["id"] for r in rows}) != len(rows):
        raise ValueError("duplicate job id")
    if len(rows) > planned:
        raise ValueError("More rows than planned")
    pairs, selected, selected_bad = [], 0, 0
    total, assessed, false, available, mixed, complete = 0, 0, 0, 0, 0, 0
    calibration = []
    for row in rows:
        complete += row["status"] == "complete"
        candidates = row["candidates"]
        total += len(candidates)
        assessed += sum(c["oracle"] is not None for c in candidates)
        false += sum(c["oracle"] is not None and not c["oracle"]["correct"] for c in candidates)
        available += any(c["oracle"] is not None and c["oracle"]["correct"] for c in candidates)
        choices = [
            c for c in candidates if c.get("judgment") is not None and c.get("duplicate_of") is None
        ]
        calibration.extend(
            (c["judgment"]["support"], int(c["oracle"]["correct"]))
            for c in choices
            if c["oracle"] is not None
        )
        if not choices:
            continue
        likelihood = max(choices, key=lambda c: c["mean_logprob"])
        assessable = [c for c in choices if c["judgment"]["assessable"] >= 0.5]
        winner = (
            max(assessable, key=lambda c: (c["judgment"]["support"], c["mean_logprob"]))
            if assessable
            else likelihood
        )
        if winner["judgment"]["support"] >= 0.8 and winner["judgment"]["assessable"] >= 0.5:
            selected += 1
            selected_bad += winner["oracle"] is None or not winner["oracle"]["correct"]
        if all(c["oracle"] is not None for c in choices) and {
            c["oracle"]["correct"] for c in choices
        } == {True, False}:
            mixed += 1
            pairs.append((int(winner["oracle"]["correct"]), int(likelihood["oracle"]["correct"])))
    differences = [jev - likelihood for jev, likelihood in pairs]
    draws = []
    rng = random.Random(19371)
    if differences:
        for _ in range(5000):
            draws.append(sum(rng.choices(differences, k=len(differences))) / len(differences))
        draws.sort()
    interval = [draws[124], draws[4874]] if draws else [-1.0, 1.0]
    coverage = assessed / total if total else 0.0
    upper = wilson_upper(selected_bad, selected)
    gates = {
        "all_jobs_completed": len(rows) == complete == planned,
        "canonical_coverage": coverage >= 0.8,
        "mixed_opportunities": mixed >= 25,
        "ranking_advantage": bool(pairs) and interval[0] > 0,
        "acceptance_risk": upper <= 0.15,
    }
    return {
        "planned": planned,
        "recorded": len(rows),
        "complete": complete,
        "raw_candidates": total,
        "assessed_candidates": assessed,
        "unassessed_candidates": total - assessed,
        "certified_false_candidates": false,
        "canonical_coverage": coverage,
        "batches_with_correct_candidate": available,
        "mixed_batches": mixed,
        "calibration": {
            "unique_assessed_scored_candidates": len(calibration),
            "brier_score": sum((probability - truth) ** 2 for probability, truth in calibration)
            / len(calibration)
            if calibration
            else None,
            "bins": [
                {
                    "lower": index / 5,
                    "upper": (index + 1) / 5,
                    "count": len(members),
                    "mean_probability": sum(p for p, truth in members) / len(members)
                    if members
                    else None,
                    "observed_fraction": sum(truth for p, truth in members) / len(members)
                    if members
                    else None,
                }
                for index in range(5)
                for members in [
                    [(p, truth) for p, truth in calibration if min(4, int(p * 5)) == index]
                ]
            ],
        },
        "ranking": {
            "jev_correct": sum(jev for jev, likelihood in pairs),
            "likelihood_correct": sum(likelihood for jev, likelihood in pairs),
            "denominator": len(pairs),
            "difference": sum(differences) / len(pairs) if pairs else None,
            "difference_interval": interval,
        },
        "selected_high_score": selected,
        "selected_false_or_uncertified": selected_bad,
        "acceptance_risk_upper": upper,
        "gates": gates,
        "admitted": all(gates.values()),
    }


async def run(args):
    manifest = json.loads((args.manifest / "manifest.json").read_text())
    if manifest["source_hashes"] != source_hashes():
        raise ValueError("Frozen source changed")
    data_path = args.manifest / f"{args.split}.json"
    if sha(data_path) != manifest["dataset_hashes"][args.split]:
        raise ValueError("Frozen data changed")
    cases = json.loads(data_path.read_text())
    args.output.mkdir(parents=True, exist_ok=False)
    from jev_guided_decoding.backends.transformers import TransformersBackend

    loaded = time.monotonic()
    backend = TransformersBackend.load(
        MODEL,
        revision=REVISION,
        device=args.device,
        temperature=1.0,
        top_p=1.0,
        local_files_only=args.local_files_only,
    )
    loading_seconds = time.monotonic() - loaded
    # Separate authored warm-up, not a study case.
    warm = Request("Write a short claim.", "Rumi is blue.", DATA["CLAIM_SYSTEM"])
    backend.propose_frames(
        backend.encode(warm),
        backend.encode_control("<step>"),
        count=3,
        max_tokens=2,
        seed=123,
        greedy=False,
        max_seconds=30,
    )
    metadata = {
        "manifest_sha256": sha(args.manifest / "manifest.json"),
        "source_hashes": source_hashes(),
        "model": backend.metadata(),
        "split": args.split,
        "loading_seconds": loading_seconds,
        "started_at": datetime.now(UTC).isoformat(),
        "planned": len(cases),
    }
    write_json(args.output / "metadata.json", metadata)
    rows, started = [], time.monotonic()
    with InputTokenBudget(args.ledger, max_usd=3) as budget:
        async with LocalClaimScorer(load_api_key(), budget=budget) as scorer:
            with (args.output / "runs.jsonl").open("x") as stream:
                for case in cases:
                    if time.monotonic() - started >= manifest["stage_seconds"]:
                        break
                    record = {
                        "id": case["id"],
                        "motif": case["motif"],
                        "status": "started",
                        "candidates": [],
                        "seed": manifest["seed_base"] + case["index"],
                        "case": case,
                    }
                    request = Request(
                        DATA["request_question"](case), case["evidence"], DATA["CLAIM_SYSTEM"]
                    )
                    record["request"] = asdict(request)
                    job_started = time.monotonic()
                    try:
                        proposal = backend.propose_frames(
                            backend.encode(request),
                            backend.encode_control("<step>"),
                            count=3,
                            max_tokens=manifest["chunk_tokens"],
                            seed=record["seed"],
                            greedy=False,
                            max_seconds=manifest["seconds_per_batch"],
                        )
                        record["proposal"] = asdict(proposal)
                        valid, indices, seen = [], [], {}
                        for i, c in enumerate(proposal.candidates):
                            frame = parse_frame("<step>" + c.text)
                            entry = {
                                **asdict(c),
                                "body": frame.body if frame else None,
                                "oracle": None,
                                "judgment": None,
                                "duplicate_of": None,
                            }
                            if c.token_ids in seen:
                                entry["duplicate_of"] = seen[c.token_ids]
                            elif (
                                frame is not None
                                and frame.kind == "step"
                                and c.finish_reason == "frame"
                            ):
                                seen[c.token_ids] = i
                                valid.append(
                                    Candidate(
                                        c.token_ids, frame.body, c.mean_logprob, c.finish_reason
                                    )
                                )
                                indices.append(i)
                            record["candidates"].append(entry)
                        if valid:
                            record["payload"] = scorer._build_payload(request, "", tuple(valid))
                            evaluation = await scorer.score(request, "", tuple(valid), timeout=30)
                            record["evaluation"] = asdict(evaluation)
                            for i, j in zip(indices, evaluation.judgments, strict=True):
                                record["candidates"][i]["judgment"] = asdict(j)
                        # Independent labels are computed after scoring, never supplied in payload.
                        for entry in record["candidates"]:
                            if entry["body"] is not None:
                                entry["oracle"] = DATA["grade_claim"](case, entry["body"])
                            if entry["duplicate_of"] is not None:
                                entry["judgment"] = record["candidates"][entry["duplicate_of"]][
                                    "judgment"
                                ]
                        record["status"] = "complete"
                    except ScorerError as exc:
                        record.update(
                            status="scorer_error",
                            error=str(exc),
                            usage_unknown=exc.usage_unknown,
                            attempts=exc.attempts,
                        )
                    except Exception as exc:
                        record.update(status="backend_error", error_type=type(exc).__name__)
                    record["seconds"] = time.monotonic() - job_started
                    stream.write(json.dumps(record, allow_nan=False) + "\n")
                    stream.flush()
                    os.fsync(stream.fileno())
                    rows.append(record)
                    print(
                        json.dumps(
                            {"done": len(rows), "planned": len(cases), "status": record["status"]}
                        ),
                        flush=True,
                    )
                    if record["status"] != "complete":
                        break
        summary = analyze(rows, planned=len(cases))
        summary["ledger_charged_tokens_including_previous_studies"] = budget.charged_tokens
        summary["unsettled_reservations"] = len(set(budget.reserved) - set(budget.settled))
    summary["runs_sha256"] = sha(args.output / "runs.jsonl")
    summary["seconds"] = time.monotonic() - started
    write_json(args.output / "summary.json", summary)
    print(json.dumps(summary, indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("prepare")
    p.add_argument("--output", type=Path, required=True)
    p = commands.add_parser("run")
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--split", choices=["development", "gate"], required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--ledger", type=Path, required=True)
    p.add_argument("--device", default="auto")
    p.add_argument("--local-files-only", action="store_true")
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.output)
    else:
        asyncio.run(run(args))


if __name__ == "__main__":
    main()
