"""R13 operational continuation: never replay a started job or alter inference policy."""

import argparse
import asyncio
import json
import math
import random
import runpy
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

from jev_guided_decoding.experiment_budget import InputTokenBudget
from jev_guided_decoding.framing import parse_frame
from jev_guided_decoding.jev import load_api_key
from jev_guided_decoding.local_claims import LocalClaimScorer
from jev_guided_decoding.types import ScorerError

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
S = runpy.run_path(str(HERE / "structured_study.py"))
D, C = S["DATA"], S["CONTROL"]
AUTHORIZATION = (
    "Owner 2026-09-21 instruction to resolve issues and run the full test under cumulative $50; "
    "bounded never-started-job recovery in research/structured-study-continuation.md."
)


def read(path):
    return json.loads(path.read_text())


def rows(path):
    return [json.loads(s) for s in path.read_text().splitlines()]


def key(job):
    return tuple(job[k] for k in ("id", "seed", "mode"))


def ordered_jobs(cases, seeds, arms):
    jobs = []
    for case in cases:
        for seed in seeds:
            order = list(arms)
            random.Random(seed + case["index"] * 817).shuffle(order)
            jobs.extend(dict(id=case["id"], seed=seed, mode=mode) for mode in order)
    return jobs


def remaining_jobs(cases, seeds, arms, starts, previous):
    jobs = ordered_jobs(cases, seeds, arms)
    started = [key(j) for j in starts]
    if started != [key(j) for j in jobs[: len(starts)]]:
        raise ValueError("Previous starts must be the exact frozen schedule prefix")
    if [key(r) for r in previous] != started:
        raise ValueError("Every prior start must retain exactly one outcome, including failures")
    return jobs[len(starts) :]


async def recover_rate_failure(error, budget, before, incidents, emit, *, sleep=asyncio.sleep):
    details = getattr(error, "diagnostics", None) or {}
    delay = details.get("retry_after_seconds", 60)
    if (
        not isinstance(error, ScorerError)
        or details.get("status_code") not in {429, 529}
        or error.attempts != 1
        or incidents >= 3
        or type(delay) not in (int, float)
        or not math.isfinite(delay)
        or not 0 <= delay <= 300
        or len(budget.unresolved) != 1
        or budget.unresolved & before
    ):
        return False
    delay = max(60, delay)
    budget.acknowledge_max_charge(
        next(iter(budget.unresolved)),
        reason="Explicit HTTP 429/529, no usage receipt; failed job retained and never replayed.",
        authorization=AUTHORIZATION,
    )
    emit(dict(event="cooldown_started", delay_seconds=delay, status=details["status_code"]))
    await sleep(delay)
    emit(dict(event="cooldown_complete", delay_seconds=delay))
    return True


def prepare(args):
    original = read(args.original / "manifest.json")
    cases = read(args.original / "test.json")
    starts, previous = (rows(args.prior / "test" / n) for n in ("job-starts.jsonl", "runs.jsonl"))
    jobs = remaining_jobs(cases, original["seeds"]["test"], original["arms"], starts, previous)
    if len(starts) != 3016 or len(jobs) != 3284:
        raise ValueError("This registered recovery is specific to the stopped 3,016-job segment")
    current = S["sources"]()
    changed = [p for p, h in original["source_hashes"].items() if current.get(p) != h]
    if changed != ["src/jev_guided_decoding/jev.py"]:
        raise ValueError("Only the registered transport-diagnostics change is permitted")
    S["write"](
        args.manifest,
        dict(
            schema="structured-v2-completion-v1",
            created_at=datetime.now(UTC).isoformat(),
            source_revision=subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            source_hashes=current,
            original_manifest_sha256=S["sha"](args.original / "manifest.json"),
            prior_hashes={
                n: S["sha"](args.prior / n)
                for n in (
                    "metadata.json",
                    "completion.json",
                    "test/job-starts.jsonl",
                    "test/runs.jsonl",
                    "test/summary.json",
                )
            },
            jobs=jobs,
            protocol="research/structured-study-continuation.md",
            max_seconds=12000,
            max_rate_recoveries=3,
            min_cooldown_seconds=60,
            max_cooldown_seconds=300,
        ),
    )


async def run(args):
    manifest = read(args.manifest)
    original = read(args.original / "manifest.json")
    if manifest["source_hashes"] != S["sources"]():
        raise ValueError("Continuation source changed")
    if manifest["original_manifest_sha256"] != S["sha"](args.original / "manifest.json"):
        raise ValueError("Original manifest changed")
    for name, digest in manifest["prior_hashes"].items():
        if S["sha"](args.prior / name) != digest:
            raise ValueError("Stopped evidence changed")
    for split, digest in original["dataset_hashes"].items():
        if S["sha"](args.original / f"{split}.json") != digest:
            raise ValueError("Frozen data changed")
    cases = read(args.original / "test.json")
    by_id = {c["id"]: c for c in cases}
    previous = rows(args.prior / "test/runs.jsonl")
    jobs = remaining_jobs(
        cases,
        original["seeds"]["test"],
        original["arms"],
        rows(args.prior / "test/job-starts.jsonl"),
        previous,
    )
    if jobs != manifest["jobs"]:
        raise ValueError("Remaining schedule changed")
    args.output.mkdir(parents=True, exist_ok=False)
    import torch

    from jev_guided_decoding.backends.transformers import TransformersBackend

    torch.set_num_threads(2)
    load_started = time.monotonic()
    base = TransformersBackend.load(
        original["model"],
        revision=original["revision"],
        device="cuda",
        temperature=original["temperature"],
        top_p=original["top_p"],
        local_files_only=True,
    )
    runtime = runpy.run_path(str(HERE / "structured_runtime.py"))["StructuredRuntime"](base)
    digest = runpy.run_path(str(HERE / "logit_mechanism.py"))["weight_digest"]
    before = digest(base)
    if before != read(args.prior / "metadata.json")["weights_before"]:
        raise ValueError("Model weights differ from original segment")
    warm = D["model_view"](D["worlds"]("development", 1)[0])
    grammar, opening = runtime.make_grammar(warm["entities"], warm["properties"])
    runtime.inspect(base.encode(C["request_for"](warm)), opening, allowed=grammar.allowed(opening))
    S["write"](
        args.output / "metadata.json",
        dict(
            started_at=datetime.now(UTC).isoformat(),
            loading_seconds=time.monotonic() - load_started,
            model=base.metadata(),
            weights_before=before,
            source_hashes=S["sources"](),
            manifest_sha256=S["sha"](args.manifest),
            git_status=subprocess.check_output(
                ["git", "status", "--porcelain"], cwd=ROOT, text=True
            ),
        ),
    )
    started, new, incidents, failure = time.monotonic(), [], 0, None
    with InputTokenBudget(args.ledger, max_usd=3) as budget:
        if budget.unresolved:
            raise ValueError("Unresolved usage blocks continuation")
        with (
            (args.output / "runs.jsonl").open("x") as stream,
            (args.output / "job-starts.jsonl").open("x") as starts,
            (args.output / "incidents.jsonl").open("x") as incident_file,
        ):
            async with LocalClaimScorer(
                load_api_key(), model=original["jev_model"], budget=budget
            ) as scorer:
                for job in jobs:
                    if time.monotonic() - started >= manifest["max_seconds"]:
                        failure = "stage_time_limit"
                        break
                    row = {**job, "status": "started"}
                    S["append"](starts, {**row, "at": datetime.now(UTC).isoformat()})
                    case, error, prior_reservations = by_id[job["id"]], None, set(budget.reserved)
                    try:
                        view = D["model_view"](case)
                        await C["run_job"](
                            view,
                            runtime,
                            mode=job["mode"],
                            seed=job["seed"],
                            scorer=scorer,
                            record=row,
                            limits=original["limits"],
                            final_grammar=True,
                        )
                        row["audit"] = S["audit"](row, view, base)
                        if not all(row["audit"].values()):
                            raise ValueError("Token/prompt audit failed")
                    except BaseException as exc:
                        error = exc
                        row.update(status="failed", stage_error=type(exc).__name__)
                    for step in row.get("steps", []):
                        for branch in step.get("checkpoint", {}).get("branches", []):
                            branch["oracle"] = (
                                D["grade_claim"](case, branch["body"]) if "body" in branch else None
                            )
                        if step.get("text"):
                            frame = parse_frame(step["text"])
                            step["oracle"] = D["grade_claim"](case, frame.body) if frame else None
                    row.update(
                        reference_label=case["reference_label"],
                        motif=case["motif"],
                        depth=case["depth"],
                    )
                    S["append"](stream, row)
                    new.append(row)
                    print(
                        json.dumps(
                            dict(
                                done=len(new),
                                planned=len(jobs),
                                combined_recorded=len(previous) + len(new),
                                status=row["status"],
                            )
                        ),
                        flush=True,
                    )
                    if error:

                        def emit(event, job=job):
                            S["append"](
                                incident_file, {**job, **event, "at": datetime.now(UTC).isoformat()}
                            )

                        if await recover_rate_failure(
                            error, budget, prior_reservations, incidents, emit
                        ):
                            incidents += 1
                            continue
                        failure = type(error).__name__
                        break
        combined = previous + new
        summary = S["summarize"](
            combined, cases, original["seeds"]["test"], original["arms"], bootstrap=5000
        )
        summary.update(
            continuation_elapsed_seconds=time.monotonic() - started, stopped_reason=failure
        )
        S["write"](args.output / "combined-summary.json", summary)
        with (args.output / "combined-runs.jsonl").open("x") as stream:
            for row in combined:
                S["append"](stream, row)
        after = digest(base)
        result = dict(
            all_planned_attempted=len(combined) == 6300,
            new_recorded=len(new),
            prior_recorded=len(previous),
            rate_recoveries=incidents,
            stopped_reason=failure,
            weights_before=before,
            weights_after=after,
            weights_unchanged=after == before,
            ledger=dict(
                charged_input_tokens=budget.charged_tokens,
                unresolved=len(budget.unresolved),
                maximum_charged_unknown_calls=len(budget.max_charged),
            ),
        )
        S["write"](args.output / "completion.json", result)
        print(json.dumps(result), flush=True)
        return (
            0
            if result["all_planned_attempted"] and result["weights_unchanged"] and failure is None
            else 2
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "run"])
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--prior", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--ledger", type=Path)
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args)
        return 0
    return asyncio.run(run(args))


if __name__ == "__main__":
    raise SystemExit(main())
