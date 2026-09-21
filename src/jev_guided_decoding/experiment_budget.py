"""Durable, exclusive reservations for a bounded Jev experiment."""

from __future__ import annotations

import json
import os
import uuid
from decimal import Decimal
from pathlib import Path

from .generated_answer import IntermediateScorer
from .types import ScorerError


class BudgetExhausted(RuntimeError):
    pass


class InputTokenBudget:
    """Reserve the documented maximum input before dispatch; unknown usage stays charged.

    A process lease prevents concurrent spenders. A crash intentionally leaves its
    lease for explicit recovery after verifying that the old process has stopped.
    """

    def __init__(self, path, *, max_usd=3, usd_per_million=0.05):
        self.path = Path(path)
        self.lock = self.path.with_suffix(".lock")
        self.terms = {
            "max_usd": str(max_usd),
            "usd_per_million": str(usd_per_million),
            "request_token_ceiling": 65536,
        }
        cap, rate = Decimal(str(max_usd)), Decimal(str(usd_per_million))
        if not cap.is_finite() or not rate.is_finite() or cap <= 0 or rate <= 0:
            raise ValueError("Invalid budget terms")
        self.token_limit = int(cap * 1000000 / rate)
        self.reserved, self.settled, self.max_charged = {}, {}, {}
        self.stream = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.lock.open("x") as lease:
            lease.write(str(os.getpid()))
        try:
            events = (
                [json.loads(s) for s in self.path.read_text().splitlines()]
                if self.path.exists()
                else []
            )
            if events:
                if events[0] != {"event": "terms", **self.terms}:
                    raise ValueError("Budget terms changed")
                for event in events[1:]:
                    key = event["id"]
                    if event["event"] == "reserve":
                        if key in self.reserved:
                            raise ValueError("Duplicate reservation")
                        self.reserved[key] = 65536
                    elif event["event"] == "settle":
                        self._validate_settlement(key, event["input_tokens"])
                        self.settled[key] = event["input_tokens"]
                    elif event["event"] == "charge_max_unknown":
                        self._validate_max_charge(key, event["reason"], event["authorization"])
                        self.max_charged[key] = {
                            "reason": event["reason"],
                            "authorization": event["authorization"],
                        }
                    else:
                        raise ValueError("Unknown budget event")
            self.stream = self.path.open("a")
            if not events:
                self._append({"event": "terms", **self.terms})
            if self.charged_tokens > self.token_limit:
                raise ValueError("Existing ledger exceeds budget")
            return self
        except BaseException:
            if self.stream:
                self.stream.close()
            self.lock.unlink()
            raise

    def __exit__(self, *args):
        self.stream.close()
        self.stream = None
        self.lock.unlink()

    def _append(self, event):
        if self.stream is None:
            raise RuntimeError("Budget lease is not held")
        self.stream.write(json.dumps(event, allow_nan=False) + "\n")
        self.stream.flush()
        os.fsync(self.stream.fileno())

    @property
    def charged_tokens(self):
        return sum(self.settled.get(key, amount) for key, amount in self.reserved.items())

    @property
    def unresolved(self):
        return set(self.reserved) - set(self.settled) - set(self.max_charged)

    def _validate_max_charge(self, key, reason, authorization):
        if key not in self.unresolved:
            raise ValueError("Maximum charge requires one unresolved reservation")
        if any(
            not isinstance(v, str) or not v.strip() or len(v) > 500 for v in (reason, authorization)
        ):
            raise ValueError("Explicit reason and authorization are required")

    def acknowledge_max_charge(self, key, *, reason, authorization):
        """Record an authorized conservative charge, never an actual usage receipt.

        Scorers do not call this method. A separately authorized recovery workflow
        may permit new work while retaining the old unknown call at its full cost.
        """
        self._validate_max_charge(key, reason, authorization)
        self._append(
            {
                "event": "charge_max_unknown",
                "id": key,
                "reason": reason,
                "authorization": authorization,
            }
        )
        self.max_charged[key] = {"reason": reason, "authorization": authorization}

    def reserve(self):
        if self.charged_tokens + 65536 > self.token_limit:
            raise BudgetExhausted("Input-token spending cap reached before dispatch")
        key = uuid.uuid4().hex
        self._append({"event": "reserve", "id": key})
        self.reserved[key] = 65536
        return key

    def _validate_settlement(self, key, tokens):
        if key not in self.reserved or key in self.settled or key in self.max_charged:
            raise ValueError("Missing or already settled reservation")
        if type(tokens) is not int or not 0 <= tokens <= 65536:
            raise ValueError("Invalid input token usage")

    def settle(self, key, input_tokens):
        self._validate_settlement(key, input_tokens)
        self._append({"event": "settle", "id": key, "input_tokens": input_tokens})
        self.settled[key] = input_tokens


class BudgetedIntermediateScorer(IntermediateScorer):
    def __init__(self, api_key, budget, **kwargs):
        if kwargs.pop("max_retries", 0) != 0:
            raise ValueError("Budgeted experiment permits one attempt only")
        super().__init__(api_key, max_retries=0, **kwargs)
        self.budget = budget

    async def score(self, request, prefix, candidates, *, timeout=60, max_attempts=1):
        if max_attempts != 1:
            raise ValueError("Budgeted experiment permits one attempt only")
        self._build_payload(request, prefix, candidates)
        try:
            reservation = self.budget.reserve()
        except BudgetExhausted as exc:
            raise ScorerError(str(exc), attempts=0, usage_unknown=False) from None
        # Any exception/cancellation leaves the maximum reservation in place.
        try:
            result = await super().score(
                request, prefix, candidates, timeout=timeout, max_attempts=1
            )
        except ScorerError:
            raise
        except Exception:
            raise ScorerError(
                "Unclassified provider failure", attempts=1, usage_unknown=True
            ) from None
        if result.attempts != 1 or result.model != self.model:
            raise ScorerError("Unexpected model or attempt count", attempts=1, usage_unknown=True)
        try:
            self.budget.settle(reservation, result.input_tokens)
        except (ValueError, OSError):
            raise ScorerError(
                "Provider usage violates reservation", attempts=1, usage_unknown=True
            ) from None
        return result
