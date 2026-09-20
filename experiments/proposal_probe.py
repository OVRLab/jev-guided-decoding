"""Frozen development/evaluation protocol for the proposal prompt experiment."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import platform
import re
import subprocess
import time
import tomllib
from dataclasses import asdict, replace
from datetime import UTC, datetime
from pathlib import Path

from jev_guided_decoding.cli import parser as cli_parser
from jev_guided_decoding.cli import run as cli_run
from jev_guided_decoding.jev import load_api_key
from jev_guided_decoding.reasoning import (
    ReasoningCancelled,
    ReasoningConfig,
    ReasoningController,
    prepare_reasoning_request,
)
from jev_guided_decoding.reasoning_scorer import ReasoningScorer
from jev_guided_decoding.types import Request

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "experiments/proposal_worlds.json"
DATASET = ROOT / "data/proposal-evaluation.jsonl"
SEEDS = [42, 43]
MODES = ["greedy", "likelihood", "final_jev", "jev"]


def oracle(world: dict) -> str:
    known = set(world["facts"])
    while True:
        added = {conclusion for premises, conclusion in world["rules"] if set(premises) <= known}
        if added <= known:
            break
        known |= added
    yes, no = world["goal"] in known, world["opposite"] in known
    if yes and no:
        raise ValueError("An inconsistent world has no three-way verdict")
    return "ENTAILED" if yes else "CONTRADICTED" if no else "UNKNOWN"


def render(world: dict) -> dict:
    atoms = world["atoms"]
    evidence = "Fictional facts and one-way rules. Missing facts are not false.\n" + "\n".join(
        [f"Fact: {atoms[a]}." for a in world["facts"]]
        + [
            f"Rule: If {' AND '.join(atoms[p] for p in premises)}, then {atoms[conclusion]}."
            for premises, conclusion in world["rules"]
        ]
    )
    question = (
        f"Classify the claim '{atoms[world['goal']]}' using only these facts and rules. "
        "Begin the final answer with ENTAILED if the claim follows, CONTRADICTED if its "
        "explicit negation follows, or UNKNOWN if neither follows; then give a short reason."
    )
    return {
        "id": world["id"],
        "question": question,
        "evidence": evidence,
        "answers": [oracle(world)],
    }


def verdict(text: str) -> str | None:
    match = re.match(r"\s*(ENTAILED|CONTRADICTED|UNKNOWN)\b", text, re.IGNORECASE)
    return match[1].upper() if match else None


def grade_rows(rows: list[dict], worlds: list[dict], seeds: list[int], modes: list[str]) -> dict:
    expected = {
        (w["id"], seed, mode): oracle(w) for w in worlds for seed in seeds for mode in modes
    }
    observed = {}
    for row in rows:
        key = row["id"], row["seed"], row["result"]["mode"]
        if key not in expected or key in observed:
            raise ValueError("Unexpected or duplicate evaluation row")
        observed[key] = row["result"]
    grades = []
    for (case_id, seed, mode), gold in expected.items():
        result = observed.get((case_id, seed, mode))
        complete = result is not None and result["phase"] == "complete"
        predicted = verdict(result["text"]) if complete else None
        grades.append(
            {
                "id": case_id,
                "seed": seed,
                "mode": mode,
                "expected": gold,
                "predicted": predicted,
                "complete": complete,
                "verdict_match": complete and predicted == gold,
                "stop_reason": result["stop_reason"] if result else "not_run",
            }
        )
    summary = {}
    for mode in modes:
        group = [r for r in grades if r["mode"] == mode]
        summary[mode] = {
            "planned_runs": len(group),
            "not_run": sum(r["stop_reason"] == "not_run" for r in group),
            "completed": sum(r["complete"] for r in group),
            "recognized_verdicts": sum(r["predicted"] is not None for r in group),
            "matching_verdicts": sum(r["verdict_match"] for r in group),
        }
    return {
        "metric": "First-word verdict agreement, not explanation/step correctness",
        "summary": summary,
        "runs": grades,
    }


def write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


async def develop(output: Path) -> int:
    if output.exists():
        raise ValueError("Output already exists")
    config = tomllib.loads((ROOT / "configs/granite-4.0-1b-reasoning.toml").read_text())
    worlds = json.loads(FIXTURE.read_text())
    cases = [render(w) for w in worlds if w["split"] == "development"]
    key = load_api_key()
    # Keep core tests and offline grading free of optional inference imports.
    from jev_guided_decoding.backends.transformers import TransformersBackend

    output.mkdir(parents=True, exist_ok=False)
    load_started = time.monotonic()
    backend = TransformersBackend.load(**config["model"], local_files_only=True)
    load_seconds = time.monotonic() - load_started
    cfg = ReasoningConfig(
        **(
            config["reasoning"]
            | {
                "max_steps": 1,
                "max_expansions": 1,
                "max_resamples": 0,
                "max_api_calls": 1,
                "max_seconds": 30.0,
            }
        )
    )
    warmup = prepare_reasoning_request(
        Request(cases[0]["question"], cases[0]["evidence"]), "examples"
    )
    await asyncio.to_thread(
        backend.propose_frames,
        backend.encode(warmup),
        (),
        count=3,
        max_tokens=2,
        seed=42,
        greedy=False,
        max_seconds=30,
    )
    metadata = {
        "started_utc": datetime.now(UTC).isoformat(),
        "backend": backend.metadata(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "source_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "source_dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT)),
        "fixture_sha256": hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
        "config": asdict(cfg),
        "seeds": SEEDS,
        "styles": ["instructions", "examples"],
        "load_seconds": load_seconds,
        "warmup": "Excluded: examples prompt, 3 rows, 2 tokens, seed 42",
        "max_stage_seconds": 600,
        "max_stage_api_attempts": 16,
        "max_stage_batches": 16,
        "scoring": "Unchanged Jev 1.13.0, no HTTP retries; root eligibility only",
    }
    write(output / "metadata.json", metadata)
    deadline = time.monotonic() + 600
    stopped = None
    rows = []
    async with ReasoningScorer(
        key, model="jev-1.13.0", max_retries=0, request_timeout=20
    ) as scorer:
        with (output / "runs.jsonl").open("x") as stream:
            for index, case in enumerate(cases):
                for seed_index, seed in enumerate(SEEDS):
                    styles = ["instructions", "examples"]
                    if (index + seed_index) % 2:
                        styles.reverse()
                    for style in styles:
                        request = prepare_reasoning_request(
                            Request(case["question"], case["evidence"]), style
                        )
                        row = {
                            "id": case["id"],
                            "seed": seed,
                            "style": style,
                            "request": asdict(request),
                        }
                        remaining = deadline - time.monotonic()
                        if remaining <= 0:
                            stopped = stopped or "stage_time_budget"
                        if stopped:
                            row.update(result=None, status=stopped, eligible_candidates=0)
                        else:
                            run_config = replace(
                                cfg,
                                seed=seed,
                                prompt_style=style,
                                max_seconds=min(cfg.max_seconds, remaining),
                            )
                            try:
                                result = await ReasoningController(backend, run_config, scorer).run(
                                    request
                                )
                            except ReasoningCancelled as exc:
                                result = exc.result
                            proposals = [e for e in result.trace if e["event"] == "proposal"]
                            row.update(
                                result=result.to_dict(),
                                status=result.stop_reason,
                                eligible_candidates=sum(len(e["children"]) for e in proposals),
                            )
                            if result.stop_reason in (
                                "scorer_error",
                                "backend_error",
                                "backend_contract_error",
                                "cancelled",
                            ):
                                stopped = result.stop_reason
                        rows.append(row)
                        stream.write(json.dumps(row, allow_nan=False) + "\n")
                        stream.flush()
                        print(
                            f"{case['id']} seed={seed} {style}: "
                            f"{row['eligible_candidates']} eligible, {row['status']}",
                            flush=True,
                        )
    summary = {}
    for style in metadata["styles"]:
        group = [r for r in rows if r["style"] == style]
        results = [r["result"] for r in group if r["result"] is not None]
        summary[style] = {
            "planned_batches": len(group),
            "executed_batches": len(results),
            "batches_with_eligible_candidate": sum(r["eligible_candidates"] > 0 for r in group),
            "eligible_candidates": sum(r["eligible_candidates"] for r in group),
            **{
                name: sum(r[name] for r in results)
                for name in (
                    "generated_tokens",
                    "decode_token_slots",
                    "prefill_tokens",
                    "api_calls",
                    "jev_input_tokens",
                    "jev_output_tokens",
                    "elapsed_seconds",
                    "jev_seconds",
                )
            },
        }
    write(output / "summary.json", summary)
    return 2 if stopped else 0


async def evaluate(config: Path, output: Path) -> int:
    args = cli_parser().parse_args(
        [
            "reason-benchmark",
            "--config",
            str(config),
            "--dataset",
            str(DATASET),
            "--modes",
            *MODES,
            "--seeds",
            *map(str, SEEDS),
            "--local-files-only",
            "--output",
            str(output),
        ]
    )
    try:
        return await asyncio.wait_for(cli_run(args), 1800)
    except TimeoutError:
        return 130


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["develop", "export", "evaluate", "grade"])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--config", type=Path)
    args = parser.parse_args()
    if args.action == "develop":
        return asyncio.run(develop(args.output))
    if args.action == "evaluate":
        if args.config is None:
            parser.error("evaluate requires --config")
        return asyncio.run(evaluate(args.config, args.output))
    worlds = [w for w in json.loads(FIXTURE.read_text()) if w["split"] == "evaluation"]
    if args.action == "export":
        with args.output.open("x") as stream:
            for world in worlds:
                stream.write(json.dumps(render(world)) + "\n")
    else:
        rows = [json.loads(line) for line in (args.output / "runs.jsonl").read_text().splitlines()]
        result = grade_rows(rows, worlds, SEEDS, MODES)
        path = args.output / "verdicts.json"
        with path.open("x") as stream:
            stream.write(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
