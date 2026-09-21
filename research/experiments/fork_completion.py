"""Complete never-attempted DEVELOPMENT proposals locally, with no Jev dispatch."""

import argparse
import json
import os
import runpy
import subprocess
import time
from dataclasses import asdict
from pathlib import Path

from jev_guided_decoding.types import Request

FORK = runpy.run_path(str(Path(__file__).with_name("claim_forks.py")))
ROOT, sha, write_json = FORK["ROOT"], FORK["sha"], FORK["write_json"]


def remaining_cases(cases, prior):
    ids = [row["id"] for row in prior]
    if len(ids) != len(set(ids)) or set(ids) - {case["id"] for case in cases}:
        raise ValueError("Duplicate or unexpected prior attempt")
    return [case for case in cases if case["id"] not in set(ids)]


def source_hashes():
    return {**FORK["source_hashes"](), str(Path(__file__).relative_to(ROOT)): sha(__file__)}


def prepare(args):
    prior = [json.loads(line) for line in args.prior.read_text().splitlines()]
    data = ROOT / "research/protocols/claim-forks-v2/development.json"
    remaining = remaining_cases(json.loads(data.read_text()), prior)
    write_json(
        args.manifest,
        {
            "schema": "development-fork-completion-v1",
            "source_hashes": source_hashes(),
            "source_revision": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "prior_sha256": sha(args.prior),
            "data_sha256": sha(data),
            "planned_new": len(remaining),
            "prior_attempts": len(prior),
            "stage_seconds": 1800,
            "no_paid_calls": True,
            "purpose": "Post-interruption development proposal coverage; "
            "never a critic gate result",
        },
    )


def run(args):
    manifest = json.loads(args.manifest.read_text())
    data = ROOT / "research/protocols/claim-forks-v2/development.json"
    if (
        manifest["source_hashes"] != source_hashes()
        or sha(args.prior) != manifest["prior_sha256"]
        or sha(data) != manifest["data_sha256"]
    ):
        raise ValueError("Frozen source or data changed")
    prior = [json.loads(line) for line in args.prior.read_text().splitlines()]
    remaining = remaining_cases(json.loads(data.read_text()), prior)
    settings = json.loads((data.parent / "manifest.json").read_text())
    from jev_guided_decoding.backends.transformers import TransformersBackend

    runtime_class = runpy.run_path(str(Path(__file__).with_name("logit_runtime.py")))[
        "LogitTokenBackend"
    ]
    args.output.mkdir(parents=True, exist_ok=False)
    loaded = time.monotonic()
    base = TransformersBackend.load(
        settings["model"],
        revision=settings["revision"],
        device="mps",
        temperature=1,
        top_p=1,
        local_files_only=True,
    )
    runtime = runtime_class(base)
    warm = Request("Write a short claim.", "Rumi is blue.", FORK["DATA"]["CLAIM_SYSTEM"])
    runtime.inspect(base.encode(warm), base.encode_control("<step>"))
    write_json(
        args.output / "metadata.json",
        {
            "manifest_sha256": sha(args.manifest),
            "model": base.metadata(),
            "loading_and_warmup_seconds": time.monotonic() - loaded,
            "planned": len(remaining),
            "paid_calls": 0,
        },
    )
    rows, started = [], time.monotonic()
    with (args.output / "runs.jsonl").open("x") as stream:
        for case in remaining:
            if time.monotonic() - started >= manifest["stage_seconds"]:
                break
            seed = settings["seed_base"] + case["index"] * settings["prefix_seed_stride"]
            request = Request(
                FORK["DATA"]["request_question"](case),
                case["evidence"],
                FORK["DATA"]["CLAIM_SYSTEM"],
            )
            record = {
                "id": case["id"],
                "case": case,
                "request": asdict(request),
                "seed": seed,
                "status": "started",
                "candidates": [],
            }
            start = time.monotonic()
            try:
                FORK["propose"](case, request, base, runtime, settings, seed, record=record)
                for candidate in record["candidates"]:
                    if candidate["body"] is not None:
                        candidate["oracle"] = FORK["grade_claim"](case, candidate["body"])
                record["status"] = "proposals_only"
            except Exception as exc:
                record.update(
                    status="backend_error",
                    error_type=type(exc).__name__,
                    failed_operation_compute_unknown=True,
                )
            record["seconds"] = time.monotonic() - start
            stream.write(json.dumps(record, allow_nan=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
            rows.append(record)
            print(
                json.dumps(
                    {"done": len(rows), "planned": len(remaining), "status": record["status"]}
                ),
                flush=True,
            )
            if record["status"] != "proposals_only":
                break
    write_json(
        args.output / "summary.json",
        {
            "planned": len(remaining),
            "recorded": len(rows),
            "completed_proposals": sum(r["status"] == "proposals_only" for r in rows),
            "paid_calls": 0,
            "critic_gate_admitted": False,
            "seconds": time.monotonic() - started,
            "runs_sha256": sha(args.output / "runs.jsonl"),
        },
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "run"])
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--prior", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args)
    elif args.output is None:
        parser.error("run requires --output")
    else:
        run(args)


if __name__ == "__main__":
    main()
