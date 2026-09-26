"""Three localized judgments, one reserved attempt, no ambiguous replay."""

import asyncio
import json
import os
import runpy
from datetime import UTC, datetime
from pathlib import Path

from jev_guided_decoding.jev import _probability

C = runpy.run_path(str(Path(__file__).with_name("common.py")))


def now():
    return datetime.now(UTC).isoformat()


def append(path, value):
    with Path(path).open("a") as f:
        f.write(json.dumps(value, allow_nan=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


class Feedback:
    def __init__(self, scorer, budget, output, delay=2):
        self.scorer, self.budget, self.output, self.delay = scorer, budget, output, delay
        if any(
            (output / n).exists() for n in ("requests.jsonl", "responses.jsonl", "failures.jsonl")
        ):
            raise ValueError("Unregistered feedback resume")
        self.started = set()

    async def score(self, case, draft):
        request = C["payload"](case, draft)
        if case["id"] in self.started:
            raise ValueError("Duplicate dispatch refused")
        self.started.add(case["id"])
        await asyncio.sleep(self.delay)
        reservation = self.budget.reserve()
        append(
            self.output / "requests.jsonl",
            dict(id=case["id"], payload=request, reservation=reservation, at=now()),
        )
        try:
            values, version, tokens, out, attempts, seconds, raw = await self.scorer._evaluate(
                request,
                lambda a: [_probability(a, f"q{i}") for i in (1, 2, 3)],
                timeout=90,
                max_attempts=1,
            )
            C["probabilities"](values)
            if version != "jev-1.13.0" or attempts != 1:
                raise ValueError("Unexpected model or attempt count")
            self.budget.settle(reservation, tokens)
            append(
                self.output / "responses.jsonl",
                dict(
                    id=case["id"],
                    probabilities=values,
                    model=version,
                    input_tokens=tokens,
                    output_tokens=out,
                    attempts=attempts,
                    seconds=seconds,
                    raw=raw,
                    reservation=reservation,
                    at=now(),
                ),
            )
            return values
        except BaseException as exc:
            append(
                self.output / "failures.jsonl",
                dict(
                    id=case["id"],
                    reservation=reservation,
                    error_type=type(exc).__name__,
                    usage_unknown=reservation in self.budget.unresolved,
                    at=now(),
                ),
            )
            raise
