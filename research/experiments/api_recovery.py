"""Single-attempt API recovery diagnostics; no historical trial is overwritten."""

import argparse
import asyncio
import hashlib
import json
import subprocess
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from jev_guided_decoding.experiment_budget import InputTokenBudget
from jev_guided_decoding.jev import load_api_key
from jev_guided_decoding.local_claims import LocalClaimScorer
from jev_guided_decoding.types import Candidate, Request, ScorerError

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sources():
    return {
        str(p.relative_to(ROOT)): sha(p)
        for p in sorted((ROOT / "src").rglob("*.py")) + [Path(__file__)]
    }


def write(path, value):
    with path.open("x") as stream:
        stream.write(json.dumps(value, indent=2, allow_nan=False) + "\n")


def prepare(args):
    rows = [json.loads(s) for s in args.prior.read_text().splitlines()]
    failed = [r for r in rows if r["status"] == "scorer_error"]
    if len(failed) != 1:
        raise ValueError("Expected one retained failure")
    fresh = {
        "name": "fresh-authentication",
        "request": asdict(Request("Evaluate the local claim.", "Neri is blue.")),
        "candidates": [asdict(Candidate((1,), "Neri is blue.", -0.1, "frame"))],
    }
    previous = {
        "name": "previous-request-shape",
        "request": failed[0]["request"],
        "candidates": [
            asdict(
                Candidate(tuple(c["token_ids"]), c["body"], c["mean_logprob"], c["finish_reason"])
            )
            for c in failed[0]["candidates"]
            if c["body"] is not None
        ],
        "previous_payload": failed[0]["payload"],
    }
    write(
        args.manifest,
        {
            "schema": "r13-api-recovery-v1",
            "created_at": datetime.now(UTC).isoformat(),
            "source_revision": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "source_hashes": sources(),
            "prior_sha256": sha(args.prior),
            "protocol": "docs/recovery-and-nebius-study.md",
            "max_stage_calls": 10,
            "attempts_per_request": 1,
            "seconds_per_request": 30,
            "model": "jev-1.13.0",
            "cases": [fresh, previous],
        },
    )


async def run(args):
    manifest = json.loads(args.manifest.read_text())
    if sources() != manifest["source_hashes"]:
        raise ValueError("Diagnostic source changed")
    if args.output.exists():
        raise FileExistsError(args.output)
    rows = []
    with InputTokenBudget(args.ledger, max_usd=3) as budget:
        initial = len(budget.reserved)
        if budget.unresolved:
            raise ValueError("Unresolved usage blocks diagnostic calls")
        async with LocalClaimScorer(load_api_key(), budget=budget) as scorer:
            for case in manifest["cases"]:
                if len(budget.reserved) - initial >= manifest["max_stage_calls"]:
                    break
                request = Request(**case["request"])
                candidates = tuple(
                    Candidate(**{**c, "token_ids": tuple(c["token_ids"])})
                    for c in case["candidates"]
                )
                payload = scorer._build_payload(request, "", candidates)
                if case.get("previous_payload") is not None and payload != case["previous_payload"]:
                    raise ValueError("Previous diagnostic payload does not match")
                row = {"name": case["name"], "payload": payload, "status": "started"}
                try:
                    evaluation = await scorer.score(
                        request, "", candidates, timeout=30, max_attempts=1
                    )
                    row.update(status="complete", evaluation=asdict(evaluation))
                except ScorerError as exc:
                    row.update(
                        status="scorer_error",
                        error=str(exc),
                        diagnostics=exc.diagnostics,
                        usage_unknown=exc.usage_unknown,
                        attempts=exc.attempts,
                    )
                rows.append(row)
                print(json.dumps({"name": row["name"], "status": row["status"]}), flush=True)
                if row["status"] != "complete":
                    break
        write(
            args.output,
            {
                "manifest_sha256": sha(args.manifest),
                "rows": rows,
                "calls": len(budget.reserved) - initial,
                "charged_input_tokens": budget.charged_tokens,
                "unknown_max_charged": len(budget.max_charged),
                "unresolved": len(budget.unresolved),
                "completed_at": datetime.now(UTC).isoformat(),
            },
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "run"])
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--prior", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--ledger", type=Path)
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args)
    else:
        asyncio.run(run(args))


if __name__ == "__main__":
    main()
