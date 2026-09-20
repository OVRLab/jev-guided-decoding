"""Freeze, run, resume never-started jobs, and independently grade a controlled study."""

import argparse
import asyncio
import hashlib
import json
import os
import platform
import random
import runpy
import subprocess
import time
import tomllib
from collections import Counter, defaultdict
from dataclasses import asdict, replace
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean

from jev_guided_decoding.framing import DEMONSTRATION_PROMPT
from jev_guided_decoding.jev import load_api_key
from jev_guided_decoding.reasoning import (
    ReasoningCancelled,
    ReasoningConfig,
    prepare_reasoning_request,
)
from jev_guided_decoding.verdict import FixedVerdictController, VerdictConfig, VerdictScorer

ROOT = Path(__file__).resolve().parents[1]
DATA = runpy.run_path(str(ROOT / "experiments/proofwriter_data.py"))
MODES = ["fixed_jev", "unguided_fixed_jev", "final_only_fixed_jev", "direct_jev"]
DERIVED = {
    "granite_alone": "unguided_fixed_jev",
    "guided_generated": "fixed_jev",
    "final_filtered_generated": "final_only_fixed_jev",
}
PRIMARY_CONTROLS = ("unguided_fixed_jev", "final_only_fixed_jev", "direct_jev")


def prepared(case):
    return asdict(prepare_reasoning_request(DATA["request_for"](case), "examples"))


def write_json(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def read_lines(path):
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def source_hashes():
    paths = sorted((ROOT / "src").rglob("*.py")) + sorted((ROOT / "experiments").glob("*.py"))
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def plan_jobs(cases, seeds, modes=None):
    modes = MODES if modes is None else modes
    if not modes or len(set(modes)) != len(modes) or not set(modes) <= set(MODES):
        raise ValueError("Invalid study modes")
    if len(seeds) != len(set(seeds)) or len({c["id"] for c in cases}) != len(cases):
        raise ValueError("Duplicate case or seed")
    jobs = []
    for i, case in enumerate(cases):
        for j, seed in enumerate(seeds):
            offset = (i + j) % len(modes)
            for mode in modes[offset:] + modes[:offset]:
                jobs.append(
                    {
                        "key": f"{case['id']}|{seed}|{mode}",
                        "id": case["id"],
                        "seed": seed,
                        "mode": mode,
                    }
                )
    return jobs


def remaining_jobs(jobs, events):
    planned = {j["key"] for j in jobs}
    started = [e["key"] for e in events if e["event"] == "started"]
    if len(started) != len(set(started)):
        raise ValueError("Duplicate started job")
    if not set(started) <= planned:
        raise ValueError("Unplanned started job")
    return [j for j in jobs if j["key"] not in set(started)]


def paired_interval(differences, comparisons=3):
    """Problem-level percentile bootstrap with Bonferroni familywise adjustment."""
    rng = random.Random(20260920)
    n = len(differences)
    draws = sorted(mean(rng.choices(differences, k=n)) for _ in range(5000))
    tail = 0.05 / (2 * comparisons)
    return {
        "difference": mean(differences),
        "ci_adjusted": [draws[int(5000 * tail)], draws[min(4999, int(5000 * (1 - tail)))]],
        "confidence_level": 1 - 0.05 / comparisons,
        "wins": sum(d > 0 for d in differences),
        "losses": sum(d < 0 for d in differences),
        "ties": sum(d == 0 for d in differences),
        "independent_problems": n,
        "method": f"5000 problem-cluster bootstrap samples; {comparisons} adjusted contrasts",
    }


def analyze(cases, seeds, rows, modes=None):
    modes = MODES if modes is None else modes
    case_map = {c["id"]: c for c in cases}
    indexed = {}
    for row in rows:
        key = (row["id"], row["seed"], row["result"]["mode"])
        if key in indexed:
            raise ValueError("Duplicate result")
        if key[0] not in case_map or key[1] not in seeds or key[2] not in modes:
            raise ValueError("Unplanned result")
        if row["request"] != prepared(case_map[key[0]]):
            raise ValueError("Problem identity mismatch")
        indexed[key] = row
    mode_results, correctness = {}, {}
    all_modes = [*modes, *(m for m, source in DERIVED.items() if source in modes)]
    for mode in all_modes:
        counters = Counter(planned=len(cases) * len(seeds))
        strata, seed_counts, confusion = defaultdict(Counter), defaultdict(Counter), Counter()
        score_by_case = []
        for case in cases:
            scores = []
            for seed in seeds:
                row = indexed.get((case["id"], seed, DERIVED.get(mode, mode)))
                result = row["result"] if row else None
                if result and mode in DERIVED:
                    result = result.get("reasoning_outcome")
                complete = bool(result and result.get("phase") == "complete")
                text = result.get("text", "").strip() if result else ""
                predicted = text if complete and text in DATA["LABELS"] else "NO_VERDICT"
                correct = predicted == case["label"]
                first_word = text.split()[0].strip(".,:;") if text else ""
                scores.append(int(correct))
                counters.update(
                    correct=int(correct),
                    completed=int(complete),
                    missing=int(row is None),
                    recognized=int(predicted != "NO_VERDICT"),
                    first_label_correct=int(complete and first_word == case["label"]),
                )
                confusion[(case["label"], predicted)] += 1
                for target in (strata[str(case["depth"])], seed_counts[str(seed)]):
                    target.update(planned=1, correct=int(correct), completed=int(complete))
            score_by_case.append(mean(scores))
        total, completed = counters["planned"], counters["completed"]
        tp = confusion[("UNKNOWN", "UNKNOWN")]
        predicted_unknown = sum(n for (a, b), n in confusion.items() if b == "UNKNOWN")
        actual_unknown = sum(n for (a, b), n in confusion.items() if a == "UNKNOWN")
        mode_results[mode] = {
            **dict(counters),
            "accuracy": counters["correct"] / total,
            "coverage": counters["recognized"] / total,
            "accuracy_given_completion": counters["correct"] / completed if completed else None,
            "unknown_precision": tp / predicted_unknown if predicted_unknown else None,
            "unknown_recall": tp / actual_unknown if actual_unknown else None,
            "confusion": {f"{a}->{b}": n for (a, b), n in sorted(confusion.items())},
            "by_depth": dict(strata),
            "by_seed": dict(seed_counts),
        }
        correctness[mode] = score_by_case
    resources = {}
    fields = [
        "generated_tokens",
        "decode_token_slots",
        "prefill_tokens",
        "api_calls",
        "jev_input_tokens",
        "jev_output_tokens",
        "elapsed_seconds",
        "generation_seconds",
        "jev_seconds",
        "backtracks",
        "resamples",
    ]
    claim_audits = {}
    for mode in modes:
        selected = [r["result"] for r in rows if r["result"]["mode"] == mode]
        resources[mode] = {f: sum(r.get(f, 0) for r in selected) for f in fields}
        resources[mode]["unknown_usage_runs"] = sum(bool(r.get("usage_unknown")) for r in selected)
        resources[mode]["stop_reasons"] = dict(Counter(r["stop_reason"] for r in selected))
        claim_audits[mode] = dict(
            Counter(
                check["status"]
                for row in rows
                if row["result"]["mode"] == mode
                for check in DATA["audit_steps"](
                    case_map[row["id"]]["world"], row["result"]["steps"]
                )
            )
        )
    controls = [c for c in PRIMARY_CONTROLS if c in modes] if "fixed_jev" in modes else []
    contrasts = {
        control: paired_interval(
            [a - b for a, b in zip(correctness["fixed_jev"], correctness[control], strict=True)],
            comparisons=len(controls),
        )
        for control in controls
    }
    complete = len(indexed) == len(cases) * len(seeds) * len(modes)
    return {
        "independent_problems": len(cases),
        "seeds": seeds,
        "study_complete": complete,
        "modes": mode_results,
        "primary_contrasts": contrasts,
        "resources": resources,
        "leading_claim_audits": claim_audits,
        "step_audit_limit": (
            "Only recognized leading atomic claims are checked; "
            "full inference and cited justifications are not verified."
        ),
        "claim_limit": (
            "Intervals describe this selected benchmark; "
            "no universal proof, no contamination guarantee."
        ),
        "positive_accuracy_evidence": complete
        and len(cases) >= 200
        and len(contrasts) == len(PRIMARY_CONTROLS)
        and not any(
            r["result"].get("usage_unknown")
            or r["result"]["stop_reason"]
            in ("scorer_error", "backend_error", "backend_contract_error", "cancelled")
            for r in rows
        )
        and all(c["ci_adjusted"][0] > 0 for c in contrasts.values()),
    }


def freeze(archive, output, config_path, pilot=False, extra_control_only=False, stress=False):
    if stress and pilot:
        raise ValueError("Stress evaluation is separate from the development pilot")
    if extra_control_only and not pilot:
        raise ValueError("Extra-control-only is a development pilot option")
    config = tomllib.loads(config_path.read_text())
    decoding = ReasoningConfig(**config["reasoning"])
    VerdictConfig(**config["verdict"]).validate_reservation(decoding)
    if decoding.prompt_style != "examples":
        raise ValueError("This protocol freezes the existing examples prompt")
    split = "generated" if stress else "dev" if pilot else "test"
    quotas = (
        {
            (label, depth): 1
            for label, depth in [("ENTAILED", 1), ("CONTRADICTED", 3), ("UNKNOWN", None)]
        }
        if pilot
        else DATA["main_quotas"]()
    )
    cases = (
        runpy.run_path(str(ROOT / "experiments/reasoning_stress.py"))["make_cases"]()
        if stress
        else DATA["select_cases"](DATA["load_split"](archive, split), quotas)
    )
    seeds = [42] if pilot or stress else [42, 43, 44]
    modes = ["final_only_fixed_jev"] if extra_control_only else MODES
    jobs = plan_jobs(cases, seeds, modes)
    output.mkdir(parents=True, exist_ok=False)
    dataset = "".join(json.dumps(c, sort_keys=True) + "\n" for c in cases)
    (output / "cases.jsonl").write_text(dataset)
    write_json(
        output / "protocol.json",
        {
            "created_at": datetime.now(UTC).isoformat(),
            "purpose": "pilot" if pilot else "stress" if stress else "evaluation",
            "dataset_source": "experiments/reasoning_stress.py" if stress else DATA["ARCHIVE_URL"],
            "archive_sha256": None if stress else DATA["ARCHIVE_SHA256"],
            "split": split,
            "strata": DATA["counts"](cases),
            "seeds": seeds,
            "modes": modes,
            "jobs": jobs,
            "dataset_sha256": hashlib.sha256(dataset.encode()).hexdigest(),
            "config": config,
            "source_hashes": source_hashes(),
            "git_revision": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "working_tree_dirty": bool(
                subprocess.check_output(
                    ["git", "status", "--porcelain"], cwd=ROOT, text=True
                ).strip()
            ),
            "prompt_sha256": hashlib.sha256(DEMONSTRATION_PROMPT.encode()).hexdigest(),
            "max_active_seconds": 1200 if pilot else 10800 if stress else 172800,
            "max_api_calls": sum(
                decoding.max_api_calls if j["mode"] in ("fixed_jev", "final_only_fixed_jev") else 1
                for j in jobs
            ),
            "rights": (
                "New fictional worlds generated by this repository's MIT-licensed code."
                if stress
                else "Archive has a README but no explicit dataset license; "
                "raw source text stays local pending clarification."
            ),
            "analysis": (
                "Exact canonical verdict; incomplete and missing count incorrect; "
                "5000 problem-cluster bootstrap draws; three adjusted primary contrasts."
            ),
        },
    )
    print(f"Frozen {len(cases)} theories, {len(jobs)} jobs at {output}", flush=True)


async def execute(output):
    protocol = json.loads((output / "protocol.json").read_text())
    if protocol["source_hashes"] != source_hashes():
        raise ValueError("Experiment source changed since freeze")
    dataset = (output / "cases.jsonl").read_bytes()
    if hashlib.sha256(dataset).hexdigest() != protocol["dataset_sha256"]:
        raise ValueError("Frozen dataset changed")
    cases = [json.loads(line) for line in dataset.splitlines()]
    case_map = {c["id"]: c for c in cases}
    config = protocol["config"]
    decoding, verdict = ReasoningConfig(**config["reasoning"]), VerdictConfig(**config["verdict"])
    # Exclusive process lease: never remove a stale lock automatically or replay ambiguous work.
    lock = output / "running.lock"
    with lock.open("x") as stream:
        stream.write(str(os.getpid()))
    try:
        events, rows = read_lines(output / "journal.jsonl"), read_lines(output / "runs.jsonl")
        jobs = remaining_jobs(protocol["jobs"], events)
        known = {r["key"]: r for r in rows}
        active_used = sum(
            e.get("reserved_seconds", 0)
            if e["key"] not in known
            else known[e["key"]]["result"]["elapsed_seconds"]
            for e in events
            if e["event"] == "started"
        )
        calls_used = sum(
            e.get("reserved_calls", 0)
            if e["key"] not in known or known[e["key"]]["result"].get("usage_unknown")
            else known[e["key"]]["result"]["api_calls"]
            for e in events
            if e["event"] == "started"
        )
        if not jobs:
            print("No never-started jobs remain", flush=True)
            return 0
        from jev_guided_decoding.backends.transformers import TransformersBackend

        started = time.monotonic()
        backend = TransformersBackend.load(**config["model"], local_files_only=True)
        load_seconds = time.monotonic() - started
        request = prepare_reasoning_request(
            DATA["request_for"](case_map[jobs[0]["id"]]), "examples"
        )
        for count in (1, decoding.candidates):
            await asyncio.to_thread(
                backend.propose_frames,
                backend.encode(request),
                (),
                count=count,
                max_tokens=2,
                seed=42,
                greedy=count == 1,
                max_seconds=90,
            )
        session = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        write_json(
            output / f"session-{session}.json",
            {
                "backend": backend.metadata(),
                "load_seconds": load_seconds,
                "warmup": "two tokens at batch sizes one and configured candidates; excluded",
                "platform": platform.platform(),
                "python": platform.python_version(),
                "remaining_jobs": len(jobs),
                "active_seconds_before": active_used,
            },
        )
        jev = dict(config["jev"])
        jev.pop("input_usd_per_million", None)

        def append(stream, value):
            stream.write(json.dumps(value, allow_nan=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())

        async with VerdictScorer(load_api_key(), **jev) as scorer:
            with (
                (output / "journal.jsonl").open("a") as journal,
                (output / "runs.jsonl").open("a") as stream,
            ):
                for job in jobs:
                    reserve_calls = (
                        decoding.max_api_calls
                        if job["mode"] in ("fixed_jev", "final_only_fixed_jev")
                        else 1
                    )
                    if (
                        active_used + decoding.max_seconds > protocol["max_active_seconds"]
                        or calls_used + reserve_calls > protocol["max_api_calls"]
                    ):
                        print("Global study budget exhausted before dispatch", flush=True)
                        return 3
                    case = case_map[job["id"]]
                    request = prepare_reasoning_request(DATA["request_for"](case), "examples")
                    backend.reset_memory_peak()
                    append(
                        journal,
                        {
                            "event": "started",
                            **job,
                            "session": session,
                            "reserved_seconds": decoding.max_seconds,
                            "reserved_calls": reserve_calls,
                            "at": datetime.now(UTC).isoformat(),
                        },
                    )
                    try:
                        result = await FixedVerdictController(
                            backend, replace(decoding, seed=job["seed"]), scorer, verdict
                        ).run(request, job["mode"])
                    except ReasoningCancelled as exc:
                        result = exc.result
                    row = {
                        **job,
                        "session": session,
                        "request": asdict(request),
                        "result": result.to_dict(),
                        "memory": backend.memory() if job["mode"] != "direct_jev" else {},
                    }
                    append(stream, row)
                    append(journal, {"event": "finished", "key": job["key"], "session": session})
                    rows.append(row)
                    active_used += result.elapsed_seconds
                    calls_used += reserve_calls if result.usage_unknown else result.api_calls
                    print(
                        f"{len(rows)}/{len(protocol['jobs'])} {job['key']}: "
                        f"{result.stop_reason}; {result.elapsed_seconds:.2f}s; "
                        f"calls={result.api_calls}",
                        flush=True,
                    )
                    if result.stop_reason in (
                        "scorer_error",
                        "backend_error",
                        "backend_contract_error",
                        "cancelled",
                    ):
                        return 2
        return 0
    finally:
        lock.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["freeze", "run", "analyze"])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--archive", type=Path)
    parser.add_argument(
        "--config", type=Path, default=ROOT / "configs/granite-4.0-1b-proofwriter.toml"
    )
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--extra-control-only", action="store_true")
    parser.add_argument("--stress", action="store_true")
    args = parser.parse_args()
    if args.action == "freeze":
        freeze(
            args.archive, args.output, args.config, args.pilot, args.extra_control_only, args.stress
        )
    elif args.action == "run":
        return asyncio.run(execute(args.output))
    else:
        cases, rows = (
            read_lines(args.output / "cases.jsonl"),
            read_lines(args.output / "runs.jsonl"),
        )
        protocol = json.loads((args.output / "protocol.json").read_text())
        modes = protocol.get("modes", list(dict.fromkeys(j["mode"] for j in protocol["jobs"])))
        result = analyze(cases, protocol["seeds"], rows, modes)
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        write_json(args.output / f"analysis-{stamp}.json", result)
        print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
