"""One dispatch per case, explicit missing feedback, bounded transient continuation."""

import asyncio
import json
import math
import runpy
from pathlib import Path

from jev_guided_decoding.jev import _probability
from jev_guided_decoding.types import ScorerError

HERE = Path(__file__).resolve().parent
C = runpy.run_path(str(HERE / "common.py"))
S = runpy.run_path(str(HERE.parent / "gated_repair_fp32/study.py"))
append, now = S["append"], S["now"]


def effective(value):
    return 0.5 if value is None else C["gate_value"](value)


def recoverable(error, incidents):
    if not isinstance(error, ScorerError) or incidents >= 8:
        return False
    d = error.diagnostics or {}
    return d.get("status_code") in (429, 529) or (
        error.usage_unknown and str(error) == "Jev request failed or timed out; it was not replayed"
    )


def records(path):
    return [json.loads(s) for s in path.read_text().splitlines()] if path.exists() else []


def mapping(rows):
    result = {r["id"]: r for r in rows}
    if len(result) != len(rows):
        raise ValueError("Duplicate dispatch or receipt")
    return result


class Feedback:
    def __init__(self, scorer, budget, output, *, sleep=asyncio.sleep):
        self.scorer, self.budget, self.output, self.sleep = scorer, budget, output, sleep
        self.requests = mapping(records(output / "api-requests.jsonl"))
        self.responses = mapping(records(output / "api-responses.jsonl"))
        self.failures = mapping(records(output / "api-failures.jsonl"))
        if set(self.responses) & set(self.failures) or set(self.requests) != set(
            self.responses
        ) | set(self.failures):
            raise ValueError("Incomplete or overlapping prior requests")
        for failure in self.failures.values():
            historical = failure["id"] == "gsm8k/train/2355" and "admitted" not in failure
            if not historical and not failure.get("admitted", False):
                raise ValueError("Prior failure is fatal")
            if failure["reservation"] in budget.unresolved:
                self.retain(failure["reservation"])

    def retain(self, reservation):
        self.budget.acknowledge_max_charge(
            reservation,
            reason="R25 v3: unavailable feedback retained at maximum input reservation",
            authorization=(
                "Owner-authorized complete study within $75; frozen continuation; no request replay"
            ),
        )

    async def score(self, case, draft):
        payload = C["feedback_payload"](case, draft)
        ident = case["id"]
        if ident in self.requests:
            if self.requests[ident]["payload"] != payload:
                raise ValueError("Reused request input changed")
            if ident in self.responses:
                return self.responses[ident]["probability_correct"]
            failure = self.failures[ident]
            if failure.get("admitted", ident == "gsm8k/train/2355"):
                return None
            raise ValueError("Prior failure is fatal")
        reservation = self.budget.reserve()
        request = dict(id=ident, payload=payload, reservation=reservation, at=now())
        append(self.output / "api-requests.jsonl", request)
        self.requests[ident] = request
        try:
            p, version, tokens, out, attempts, seconds, raw = await self.scorer._evaluate(
                payload, lambda a: _probability(a, "correct"), timeout=90, max_attempts=1
            )
            if version != "jev-1.13.0" or attempts != 1:
                raise ValueError("Unexpected model/attempts")
            self.budget.settle(reservation, tokens)
            receipt = dict(
                id=ident,
                probability_correct=p,
                model=version,
                input_tokens=tokens,
                output_tokens=out,
                attempts=attempts,
                seconds=seconds,
                raw=raw,
                reservation=reservation,
                at=now(),
            )
            append(self.output / "api-responses.jsonl", receipt)
            self.responses[ident] = receipt
            return p
        except Exception as error:
            info = getattr(error, "diagnostics", None) or {}
            diagnostics = {
                k: info[k]
                for k in ("status_code", "retry_after_seconds", "response_sha256")
                if k in info
            }
            admitted = recoverable(error, len(self.failures))
            delay = diagnostics.get("retry_after_seconds", 60)
            if type(delay) not in (int, float) or not math.isfinite(delay) or delay > 300:
                admitted = False
                delay = None
            elif admitted:
                delay = max(60, delay)
            failure = dict(
                id=ident,
                error_type=type(error).__name__,
                message=str(error)
                if isinstance(error, ScorerError)
                else "Non-provider integrity error",
                usage_unknown=reservation in self.budget.unresolved,
                reservation=reservation,
                diagnostics=diagnostics,
                admitted=admitted,
                cooldown_seconds=delay if admitted else None,
                at=now(),
            )
            append(self.output / "api-failures.jsonl", failure)
            self.failures[ident] = failure
            if not admitted:
                raise
            self.retain(reservation)
            await self.sleep(delay)
            return None
