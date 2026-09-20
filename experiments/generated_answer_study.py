"""Freeze and compare Granite-generated answers with intermediate-only Jev guidance."""

import argparse
import asyncio
import hashlib
import json
import os
import platform
import runpy
import subprocess
import time
import tomllib
from collections import Counter, defaultdict
from dataclasses import asdict, replace
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean

from jev_guided_decoding.experiment_budget import BudgetedIntermediateScorer, InputTokenBudget
from jev_guided_decoding.generated_answer import (
    GENERATED_PROMPT,
    MODES,
    GeneratedAnswerConfig,
    GeneratedAnswerController,
    prepare_generated_request,
)
from jev_guided_decoding.jev import load_api_key
from jev_guided_decoding.reasoning import ReasoningCancelled

ROOT = Path(__file__).resolve().parents[1]
DATA = runpy.run_path(str(ROOT / "experiments/generated_answer_data.py"))
HELPERS = runpy.run_path(str(ROOT / "experiments/controlled_study.py"))
read_lines, write_json = HELPERS["read_lines"], HELPERS["write_json"]
source_hashes, remaining_jobs = HELPERS["source_hashes"], HELPERS["remaining_jobs"]
ERRORS = ("scorer_error", "backend_error", "backend_contract_error", "cancelled")


def prepared(case):
    return asdict(prepare_generated_request(DATA["request_for"](case)))


def plan_jobs(cases, seeds):
    if (
        not cases
        or not seeds
        or len({c["id"] for c in cases}) != len(cases)
        or len(set(seeds)) != len(seeds)
    ):
        raise ValueError("Empty or duplicate cases/seeds")
    jobs = []
    for i, case in enumerate(cases):
        for j, seed in enumerate(seeds):
            shift = (i + j) % len(MODES)
            for mode in (*MODES[shift:], *MODES[:shift]):
                jobs.append(
                    {
                        "key": f"{case['id']}|{seed}|{mode}",
                        "id": case["id"],
                        "seed": seed,
                        "mode": mode,
                    }
                )
    return jobs


def analyze(cases, seeds, rows):
    jobs = plan_jobs(cases, seeds)
    planned = {j["key"]: j for j in jobs}
    case_map = {c["id"]: c for c in cases}
    indexed = {}
    for row in rows:
        if row["key"] not in planned or row["key"] in indexed:
            raise ValueError("Unexpected or duplicate job")
        if any(row[k] != planned[row["key"]][k] for k in ("id", "seed", "mode")):
            raise ValueError("Job identity mismatch")
        if row["request"] != prepared(case_map[row["id"]]) or row["result"]["mode"] != row["mode"]:
            raise ValueError("Problem identity mismatch")
        DATA["grade"](case_map[row["id"]], row["result"])
        indexed[row["key"]] = row
    tasks = {}
    for task in sorted({c["task"] for c in cases}):
        subset = [c for c in cases if c["task"] == task]
        modes, scores = {}, {}
        for mode in MODES:
            counts = Counter(planned=len(subset) * len(seeds))
            by_seed, by_depth = defaultdict(Counter), defaultdict(Counter)
            per_problem = []
            for case in subset:
                outcomes = []
                for seed in seeds:
                    row = indexed.get(f"{case['id']}|{seed}|{mode}")
                    grade = DATA["grade"](case, row["result"] if row else None)
                    outcome = {
                        "correct": int(grade["correct"]),
                        "completed": int(grade["completed"]),
                        "format_valid": int(grade["format_valid"]),
                        "missing": int(row is None),
                    }
                    counts.update(outcome)
                    by_seed[str(seed)].update(planned=1, **outcome)
                    by_depth[str(case.get("depth"))].update(planned=1, **outcome)
                    outcomes.append(int(grade["correct"]))
                per_problem.append(mean(outcomes))
            scores[mode] = per_problem
            modes[mode] = {
                **counts,
                "accuracy": counts["correct"] / counts["planned"],
                "by_seed": dict(by_seed),
                "by_depth": dict(by_depth),
            }
        contrasts = {
            control: HELPERS["paired_interval"](
                [a - b for a, b in zip(scores["jev"], scores[control], strict=True)], comparisons=4
            )
            for control in ("single", "likelihood")
        }
        tasks[task] = {
            "independent_problems": len(subset),
            "modes": modes,
            "primary_contrasts": contrasts,
        }
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
    ]
    for mode in MODES:
        selected = [r["result"] for r in rows if r["mode"] == mode]
        changed = 0
        for result in selected:
            for entry in result.get("trace", []):
                if (
                    entry["event"] == "proposal"
                    and entry.get("phase") == "step"
                    and entry.get("selected_index") is not None
                ):
                    valid = entry["valid_indices"]
                    best = max(
                        valid, key=lambda i: entry["proposal"]["candidates"][i]["mean_logprob"]
                    )
                    changed += entry["selected_index"] != best
        resources[mode] = {field: sum(r.get(field, 0) for r in selected) for field in fields}
        resources[mode].update(
            stop_reasons=dict(Counter(r["stop_reason"] for r in selected)),
            reasoning_stops=dict(Counter(r.get("reasoning_stop_reason") for r in selected)),
            accepted_steps=sum(len(r["steps"]) for r in selected),
            zero_step_runs=sum(not r["steps"] for r in selected),
            intermediate_choices_different_from_likelihood=changed,
            unknown_usage_runs=sum(bool(r.get("usage_unknown")) for r in selected),
        )
    complete = len(indexed) == len(jobs)
    no_errors = not any(
        r["result"]["stop_reason"] in ERRORS or r["result"].get("usage_unknown") for r in rows
    )
    return {
        "study_complete": complete,
        "planned_jobs": len(jobs),
        "recorded_jobs": len(rows),
        "seeds": seeds,
        "tasks": tasks,
        "resources": resources,
        "positive_accuracy_evidence": complete
        and no_errors
        and len(tasks) == 2
        and all(t["independent_problems"] >= 200 for t in tasks.values())
        and all(
            c["ci_adjusted"][0] > 0 for t in tasks.values() for c in t["primary_contrasts"].values()
        ),
        "claim_limit": (
            "Granite-generated answers under this staged controller; no classifier replacement, "
            "universal reasoning claim, or contamination guarantee."
        ),
    }


def freeze(args):
    config = tomllib.loads(args.config.read_text())
    GeneratedAnswerConfig(**config["generation"])
    if config["jev"]["max_retries"] != 0:
        raise ValueError("Only one HTTP attempt allowed")
    exclusions = json.loads(args.exclusions.read_text())
    ids, hashes = set(exclusions["theory_ids"]), set(exclusions["evidence_sha256"])
    for path in args.exclude_cases:
        for c in read_lines(path):
            if "theory_id" in c:
                ids.add(c["theory_id"])
            hashes.add(c["evidence_sha256"])
    exclusions = {"theory_ids": sorted(ids), "evidence_sha256": sorted(hashes)}
    cases = DATA["select_cases"](args.archive, args.gsm, exclusions, pilot=args.pilot)
    seeds = [42] if args.pilot else [42, 43, 44]
    dirty = bool(
        subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()
    )
    if dirty:
        raise ValueError("Commit source and protocol before freezing inference")
    args.output.mkdir(parents=True, exist_ok=False)
    dataset = "".join(json.dumps(c, sort_keys=True) + "\n" for c in cases)
    (args.output / "cases.jsonl").write_text(dataset)
    write_json(args.output / "exclusions.json", exclusions)
    write_json(
        args.output / "protocol.json",
        {
            "created_at": datetime.now(UTC).isoformat(),
            "purpose": "pilot" if args.pilot else "evaluation",
            "jobs": plan_jobs(cases, seeds),
            "seeds": seeds,
            "modes": MODES,
            "config": config,
            "dataset_sha256": hashlib.sha256(dataset.encode()).hexdigest(),
            "exclusions_sha256": hashlib.sha256(
                (args.output / "exclusions.json").read_bytes()
            ).hexdigest(),
            "source_hashes": source_hashes(),
            "git_revision": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "working_tree_dirty": dirty,
            "prompt_sha256": hashlib.sha256(GENERATED_PROMPT.encode()).hexdigest(),
            "sources": {
                "gsm8k_revision": DATA["GSM_REVISION"],
                "gsm8k_sha256": hashlib.sha256(args.gsm.read_bytes()).hexdigest(),
                "proofwriter_sha256": DATA["PROOF"]["ARCHIVE_SHA256"],
            },
            "max_active_seconds": 3600 if args.pilot else 64800,
            "budget": {
                "shared_jev_cap_usd": 3,
                "accounting_usd_per_million_input": 0.05,
                "request_ceiling_tokens": 65536,
            },
            "output_contract": (
                "All final answers are Granite-generated; no Jev final calls. "
                "Same grading for all arms."
            ),
            "analysis": (
                "Four task-specific contrasts; 5000 paired problem-cluster draws; "
                "98.75% intervals; all planned outcomes in denominators."
            ),
        },
    )
    print(
        f"Frozen {len(cases)} problems and {len(plan_jobs(cases, seeds))} jobs at {args.output}",
        flush=True,
    )


def append(stream, value):
    stream.write(json.dumps(value, allow_nan=False) + "\n")
    stream.flush()
    os.fsync(stream.fileno())


async def execute(output, ledger):
    protocol = json.loads((output / "protocol.json").read_text())
    if protocol["source_hashes"] != source_hashes():
        raise ValueError("Source changed since freeze")
    dataset = (output / "cases.jsonl").read_bytes()
    if hashlib.sha256(dataset).hexdigest() != protocol["dataset_sha256"]:
        raise ValueError("Dataset changed since freeze")
    if (
        hashlib.sha256((output / "exclusions.json").read_bytes()).hexdigest()
        != protocol["exclusions_sha256"]
    ):
        raise ValueError("Exclusions changed since freeze")
    cases = [json.loads(s) for s in dataset.splitlines()]
    if protocol["jobs"] != plan_jobs(cases, protocol["seeds"]):
        raise ValueError("Job manifest changed")
    lock = output / "running.lock"
    with lock.open("x") as stream:
        stream.write(str(os.getpid()))
    try:
        rows, events = read_lines(output / "runs.jsonl"), read_lines(output / "journal.jsonl")
        jobs = remaining_jobs(protocol["jobs"], events)
        if not jobs:
            print("No never-started jobs remain", flush=True)
            return 0
        if any(
            r["result"]["stop_reason"] in ERRORS or r["result"].get("usage_unknown") for r in rows
        ):
            raise ValueError(
                "A prior service failure requires explicit investigation; no automatic continuation"
            )
        known = {r["key"]: r for r in rows}
        if any(e["key"] not in known for e in events if e["event"] == "started"):
            raise ValueError(
                "A started job has no outcome; preserve it and investigate before continuation"
            )
        active = sum(r["result"]["elapsed_seconds"] for r in rows)
        config = protocol["config"]
        decoding = GeneratedAnswerConfig(**config["generation"])
        from jev_guided_decoding.backends.transformers import TransformersBackend

        start = time.monotonic()
        backend = TransformersBackend.load(**config["model"], local_files_only=True)
        load_seconds = time.monotonic() - start
        case_map = {c["id"]: c for c in cases}
        warmup = prepare_generated_request(DATA["request_for"](case_map[jobs[0]["id"]]))
        for count in (1, decoding.candidates):
            await asyncio.to_thread(
                backend.propose_frames,
                backend.encode(warmup),
                backend.encode_control("<step>"),
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
                "warmup": "Two tokens at batch one and configured candidates; excluded from jobs",
                "platform": platform.platform(),
                "python": platform.python_version(),
            },
        )
        with InputTokenBudget(ledger, max_usd=3, usd_per_million=0.05) as budget:
            if set(budget.reserved) - set(budget.settled):
                raise ValueError("Unsettled prior paid attempt; no automatic continuation")
            async with BudgetedIntermediateScorer(
                load_api_key(), budget, **config["jev"]
            ) as scorer:
                with (
                    (output / "journal.jsonl").open("a") as journal,
                    (output / "runs.jsonl").open("a") as stream,
                ):
                    for job in jobs:
                        if active + decoding.max_seconds > protocol["max_active_seconds"]:
                            print("Active-time cap reached before dispatch", flush=True)
                            return 3
                        request = prepare_generated_request(
                            DATA["request_for"](case_map[job["id"]])
                        )
                        backend.reset_memory_peak()
                        append(
                            journal,
                            {
                                "event": "started",
                                **job,
                                "session": session,
                                "at": datetime.now(UTC).isoformat(),
                            },
                        )
                        try:
                            result = await GeneratedAnswerController(
                                backend,
                                replace(decoding, seed=job["seed"]),
                                scorer if job["mode"] == "jev" else None,
                            ).run(request, job["mode"])
                        except ReasoningCancelled as exc:
                            result = exc.result
                        row = {
                            **job,
                            "session": session,
                            "request": asdict(request),
                            "result": result.to_dict(),
                            "memory": backend.memory(),
                        }
                        append(stream, row)
                        append(
                            journal, {"event": "finished", "key": job["key"], "session": session}
                        )
                        rows.append(row)
                        active += result.elapsed_seconds
                        print(
                            f"{len(rows)}/{len(protocol['jobs'])} {job['key']}: "
                            f"{result.stop_reason}; {result.elapsed_seconds:.2f}s; "
                            f"steps={len(result.steps)}; calls={result.api_calls}",
                            flush=True,
                        )
                        if result.stop_reason in ERRORS or result.usage_unknown:
                            return 2
        return 0
    finally:
        lock.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["freeze", "run", "analyze"])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--gsm", type=Path)
    parser.add_argument("--exclusions", type=Path)
    parser.add_argument("--exclude-cases", type=Path, action="append", default=[])
    parser.add_argument(
        "--config", type=Path, default=ROOT / "configs/granite-4.0-1b-generated-answer.toml"
    )
    parser.add_argument(
        "--ledger", type=Path, default=ROOT / "results/generated-answer-budget.jsonl"
    )
    parser.add_argument("--pilot", action="store_true")
    args = parser.parse_args()
    if args.action == "freeze":
        freeze(args)
    elif args.action == "run":
        return asyncio.run(execute(args.output, args.ledger))
    else:
        protocol = json.loads((args.output / "protocol.json").read_text())
        result = analyze(
            read_lines(args.output / "cases.jsonl"),
            protocol["seeds"],
            read_lines(args.output / "runs.jsonl"),
        )
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        write_json(args.output / f"analysis-{stamp}.json", result)
        print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
