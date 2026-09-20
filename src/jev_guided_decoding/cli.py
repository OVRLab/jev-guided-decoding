from __future__ import annotations

import argparse
import asyncio
import json
import platform
import subprocess
import sys
import time
import tomllib
from contextlib import AsyncExitStack
from dataclasses import asdict, replace
from datetime import UTC, datetime
from pathlib import Path

from .benchmark import answer_metrics, load_cases, summarize
from .controller import Controller
from .jev import JevScorer, load_api_key
from .reasoning import (
    ReasoningCancelled,
    ReasoningConfig,
    ReasoningController,
    prepare_reasoning_request,
)
from .reasoning_scorer import ReasoningScorer
from .types import DecodeConfig, Request


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Experimental Jev-guided decoding")
    sub = root.add_subparsers(dest="command", required=True)
    for name in ("generate", "benchmark", "reason", "reason-benchmark"):
        reasoning = name.startswith("reason")
        choices = ["jev", "greedy", "sample", "likelihood"]
        if reasoning:
            choices.append("final_jev")
        p = sub.add_parser(name)
        p.add_argument("--config", type=Path, required=True)
        p.add_argument("--output", type=Path, required=True)
        p.add_argument("--key-file", type=Path)
        p.add_argument("--local-files-only", action="store_true")
        if name in ("generate", "reason"):
            p.add_argument("--question", required=True)
            p.add_argument("--evidence-file", type=Path, required=True)
            p.add_argument("--mode", choices=choices, default="jev")
        else:
            p.add_argument("--dataset", type=Path, required=True)
            p.add_argument(
                "--modes",
                nargs="+",
                choices=choices,
                default=["greedy", "likelihood", "final_jev", "jev"]
                if reasoning
                else ["greedy", "sample", "likelihood", "jev"],
            )
            p.add_argument("--limit", type=int)
            p.add_argument("--seeds", type=int, nargs="+")
    return root


def _write(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


async def run(args: argparse.Namespace) -> int:
    config = tomllib.loads(args.config.read_text())
    reasoning = args.command.startswith("reason")
    generation = args.command in ("generate", "reason")
    decoding = (
        ReasoningConfig(**config.get("reasoning", {}))
        if reasoning
        else DecodeConfig(**config.get("decoding", {}))
    )
    controller_type = ReasoningController if reasoning else Controller
    scorer_type = ReasoningScorer if reasoning else JevScorer

    def make_request(question, evidence):
        request = Request(question, evidence)
        return prepare_reasoning_request(request) if reasoning else request

    async def execute(request, mode, run_config):
        try:
            return await controller_type(backend, run_config, scorer).run(request, mode)
        except ReasoningCancelled as exc:
            return exc.result

    def exit_code(result):
        if result.stop_reason == "cancelled":
            return 130
        if result.stop_reason in ("scorer_error", "backend_error", "backend_contract_error"):
            return 2
        return 3 if reasoning and result.phase != "complete" else 0

    jev = dict(config.get("jev", {}))
    price = jev.pop("input_usd_per_million", None)
    if price is not None and (not isinstance(price, (int, float)) or not 0 <= price < float("inf")):
        raise ValueError("Jev input price must be finite and nonnegative")
    model_config = dict(config["model"])
    modes = [args.mode] if generation else list(dict.fromkeys(args.modes))
    if args.output.exists():
        raise ValueError("Output already exists; choose a new path to preserve prior results")
    if not generation:
        cases, dataset_hash = load_cases(args.dataset)
        if args.limit is not None:
            if args.limit < 1:
                raise ValueError("--limit must be positive")
            cases = cases[: args.limit]
        seeds = args.seeds or [decoding.seed]
        for seed in seeds:
            replace(decoding, seed=seed)
    else:
        request = make_request(args.question, args.evidence_file.read_text())
    key = load_api_key(args.key_file) if any(m in ("jev", "final_jev") for m in modes) else None
    # Import the heavy optional backend only after validating the request/configuration.
    from .backends.transformers import TransformersBackend

    load_started = time.monotonic()
    backend = TransformersBackend.load(**model_config, local_files_only=args.local_files_only)
    load_seconds = time.monotonic() - load_started
    try:
        revision = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], text=True).strip())
    except (OSError, subprocess.CalledProcessError):
        revision, dirty = None, None
    metadata = {
        "created_at": datetime.now(UTC).isoformat(),
        "config": config,
        "backend": backend.metadata(),
        "load_seconds": load_seconds,
        "platform": platform.platform(),
        "python": platform.python_version(),
        "git_revision": revision,
        "working_tree_dirty": dirty,
    }
    async with AsyncExitStack() as stack:
        scorer = await stack.enter_async_context(scorer_type(key, **jev)) if key else None
        if generation:
            backend.reset_memory_peak()
            result = await execute(request, args.mode, decoding)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            _write(
                args.output,
                {
                    "metadata": metadata,
                    "request": asdict(request),
                    "result": result.to_dict(),
                    "memory": backend.memory(),
                },
            )
            print(result.text)
            print(f"Stop: {result.stop_reason}; trace: {args.output}", file=sys.stderr)
            return exit_code(result)

        args.output.mkdir(parents=True)
        metadata.update(
            {
                "dataset_sha256": dataset_hash,
                "case_ids": [c["id"] for c in cases],
                "seeds": seeds,
                "modes": modes,
                "comparison": "Same configured token ceilings; actual work can differ by EOS, "
                "selection and retries. Compare recorded tokens and time, not ceilings alone.",
            }
        )
        _write(args.output / "metadata.json", metadata)
        # Warm kernels with the same public fixture; excluded from reported generation times.
        warmup = make_request(cases[0]["question"], cases[0]["evidence"])
        warmup_counts = {1}
        if any(mode in ("jev", "likelihood", "final_jev") for mode in modes):
            warmup_counts.add(decoding.candidates)
        for count in sorted(warmup_counts):
            await asyncio.to_thread(
                backend.propose_frames if reasoning else backend.propose,
                backend.encode(warmup),
                (),
                count=count,
                max_tokens=2,
                seed=decoding.seed,
                greedy=count == 1,
                max_seconds=decoding.max_seconds,
            )
        records = []
        status = 0
        with (args.output / "runs.jsonl").open("w") as stream:
            for case_index, case in enumerate(cases):
                request = make_request(case["question"], case["evidence"])
                for seed_index, seed in enumerate(seeds):
                    # Rotate mode order to reduce systematic warm-up/thermal ordering effects.
                    offset = (case_index + seed_index) % len(modes)
                    for mode in modes[offset:] + modes[:offset]:
                        backend.reset_memory_peak()
                        result = await execute(request, mode, replace(decoding, seed=seed))
                        record = {
                            "id": case["id"],
                            "seed": seed,
                            "request": asdict(request),
                            "references": case["answers"],
                            "result": result.to_dict(),
                            "metrics": answer_metrics(result.text, case["answers"]),
                            "memory": backend.memory(),
                            "estimated_jev_input_cost_usd": (
                                result.jev_input_tokens * price / 1_000_000
                                if price is not None
                                else None
                            ),
                        }
                        stream.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")
                        stream.flush()
                        records.append(record)
                        _write(args.output / "summary.json", _summary(records, reasoning))
                        print(
                            f"{case['id']} seed={seed} {mode}: {result.stop_reason}, "
                            f"F1={record['metrics']['token_f1']:.3f}, "
                            f"{result.elapsed_seconds:.2f}s, calls={result.api_calls}",
                            flush=True,
                        )
                        code = exit_code(result)
                        if code in (2, 130):
                            # Stop on service failure instead of repeatedly spending on broken runs.
                            return code
                        status = max(status, code)
        return status


def _summary(records: list[dict], reasoning: bool) -> dict:
    summary = summarize(records)
    if reasoning:
        for mode, row in summary.items():
            outcomes = [r["result"] for r in records if r["result"]["mode"] == mode]
            row["selected_path_tokens_per_second"] = row.pop("accepted_tokens_per_second")
            row["completed_runs"] = sum(r["phase"] == "complete" for r in outcomes)
            row["api_attempts_unknown"] = any(r["api_attempts_unknown"] for r in outcomes)
            for field in (
                "generation_seconds",
                "jev_seconds",
                "backtracks",
                "resamples",
                "duplicate_candidates",
                "unique_candidates",
                "expansions",
                "proposal_batches",
            ):
                row[field] = sum(r[field] for r in outcomes)
    return summary


def main() -> None:
    try:
        code = asyncio.run(run(parser().parse_args()))
    except (ValueError, OSError, KeyError, ImportError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from None
    raise SystemExit(code)
