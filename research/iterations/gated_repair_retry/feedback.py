"""Bounded explicit-rejection retries; one reservation and receipt per attempt."""

import asyncio
import math
import runpy
from pathlib import Path

from jev_guided_decoding.jev import _probability
from jev_guided_decoding.types import ScorerError

HERE = Path(__file__).resolve().parent
OLD = runpy.run_path(str(HERE.parent / "gated_repair_continue/feedback.py"))
C, append, now, records, mapping = (OLD[k] for k in ("C", "append", "now", "records", "mapping"))
effective = OLD["effective"]
TRANSIENT = (429, 503, 529)


class Feedback:
    def __init__(self, scorer, budget, output, *, sleep=asyncio.sleep):
        self.scorer, self.budget, self.output, self.sleep = scorer, budget, output, sleep
        self.legacy_requests = mapping(records(output / "api-requests.jsonl"))
        self.legacy_responses = mapping(records(output / "api-responses.jsonl"))
        self.legacy_failures = mapping(records(output / "api-failures.jsonl"))
        if set(self.legacy_responses) & set(self.legacy_failures) or set(self.legacy_requests) != (
            set(self.legacy_responses) | set(self.legacy_failures)
        ):
            raise ValueError("Incomplete legacy requests")
        self.missing = len(self.legacy_failures)
        if self.missing > 16:
            raise ValueError("Too many legacy missing cases")
        for row in self.legacy_failures.values():
            if row["reservation"] in budget.unresolved:
                self.retain(row["reservation"])
        if any(
            records(output / name)
            for name in (
                "new-requests.jsonl",
                "new-responses.jsonl",
                "new-failures.jsonl",
                "case-completions.jsonl",
            )
        ):
            raise ValueError("Unsupported in-process delivery resume")
        self.started, self.completed = {}, {}

    def retain(self, reservation):
        self.budget.acknowledge_max_charge(
            reservation,
            reason="R25 v4: unknown attempt usage retained at full reservation",
            authorization="Owner-authorized complete study; $20 R25/$75 cumulative cap",
        )

    def complete(self, ident, probability, attempts):
        if probability is None:
            self.missing += 1
        append(
            self.output / "case-completions.jsonl",
            dict(
                id=ident,
                actual_probability_correct=probability,
                attempts=attempts,
                missing=probability is None,
                at=now(),
            ),
        )
        self.completed[ident] = probability
        if self.missing > 16:
            raise ValueError("Missing-feedback case budget exhausted")
        return probability

    async def score(self, case, draft):
        ident = case["id"]
        payload = C["feedback_payload"](case, draft)
        if ident in self.legacy_requests:
            if payload != self.legacy_requests[ident]["payload"]:
                raise ValueError("Legacy input changed")
            return (
                self.legacy_responses[ident]["probability_correct"]
                if ident in self.legacy_responses
                else None
            )
        if ident in self.started:
            if self.started[ident] != payload or ident not in self.completed:
                raise ValueError("Changed input or incomplete duplicate dispatch")
            return self.completed[ident]
        self.started[ident] = payload
        await self.sleep(2)
        for attempt in range(1, 5):
            if len(self.budget.max_charged) + len(self.budget.unresolved) >= 64:
                raise ValueError("Unknown-charge attempt budget exhausted")
            reservation = self.budget.reserve()
            append(
                self.output / "new-requests.jsonl",
                dict(
                    id=ident,
                    attempt=attempt,
                    reservation=reservation,
                    payload=payload,
                    at=now(),
                ),
            )
            try:
                p, version, tokens, out, count, seconds, raw = await self.scorer._evaluate(
                    payload, lambda a: _probability(a, "correct"), timeout=90, max_attempts=1
                )
                if version != "jev-1.13.0" or count != 1:
                    raise ValueError("Unexpected model or attempts")
                self.budget.settle(reservation, tokens)
                append(
                    self.output / "new-responses.jsonl",
                    dict(
                        id=ident,
                        attempt=attempt,
                        reservation=reservation,
                        probability_correct=p,
                        model=version,
                        input_tokens=tokens,
                        output_tokens=out,
                        attempts=count,
                        seconds=seconds,
                        raw=raw,
                        at=now(),
                    ),
                )
            except Exception as error:
                info = getattr(error, "diagnostics", None) or {}
                diagnostics = {
                    k: info[k]
                    for k in ("status_code", "retry_after_seconds", "response_sha256")
                    if k in info
                }
                explicit = (
                    isinstance(error, ScorerError) and diagnostics.get("status_code") in TRANSIENT
                )
                transport = (
                    isinstance(error, ScorerError)
                    and error.usage_unknown
                    and str(error) == "Jev request failed or timed out; it was not replayed"
                )
                delay = diagnostics.get("retry_after_seconds", 0)
                valid_delay = (
                    type(delay) in (int, float) and math.isfinite(delay) and 0 <= delay <= 300
                )
                admitted = (explicit or transport) and valid_delay
                retry = admitted and explicit and attempt < 4
                cooldown = max(30 * 2 ** (attempt - 1), delay) if retry else None
                append(
                    self.output / "new-failures.jsonl",
                    dict(
                        id=ident,
                        attempt=attempt,
                        reservation=reservation,
                        error_type=type(error).__name__,
                        message=str(error)
                        if isinstance(error, ScorerError)
                        else "Non-provider integrity error",
                        usage_unknown=reservation in self.budget.unresolved,
                        diagnostics=diagnostics,
                        admitted=admitted,
                        retry=retry,
                        cooldown_seconds=cooldown,
                        at=now(),
                    ),
                )
                if not admitted:
                    raise
                self.retain(reservation)
                if retry:
                    await self.sleep(cooldown)
                    continue
                return self.complete(ident, None, attempt)
            return self.complete(ident, p, attempt)
        raise AssertionError("Unreachable delivery state")
