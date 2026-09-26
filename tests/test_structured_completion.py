import asyncio
import runpy
from pathlib import Path

import pytest

from jev_guided_decoding.experiment_budget import InputTokenBudget
from jev_guided_decoding.types import ScorerError

ROOT = Path(__file__).resolve().parents[1]
A = runpy.run_path(str(ROOT / "research/experiments/structured_completion.py"))


def test_schedule_excludes_completed_and_failed_starts_without_reordering():
    cases = [{"id": "a", "index": 0}, {"id": "b", "index": 1}]
    full = A["ordered_jobs"](cases, [17], ["native", "jev"])
    starts = [{**j, "status": "started"} for j in full[:2]]
    rows = [{**full[0], "status": "complete"}, {**full[1], "status": "failed"}]
    assert A["remaining_jobs"](cases, [17], ["native", "jev"], starts, rows) == full[2:]
    for bad in (starts[::-1], starts + starts[:1], starts[1:]):
        with pytest.raises(ValueError):
            A["remaining_jobs"](cases, [17], ["native", "jev"], bad, rows)


@pytest.mark.parametrize("status", [429, 529])
def test_explicit_rate_failure_keeps_full_charge_waits_and_does_not_replay(tmp_path, status):
    async def exercise():
        sleeps, records = [], []

        async def sleep(seconds):
            sleeps.append(seconds)

        with InputTokenBudget(tmp_path / "ledger.jsonl") as budget:
            before = set(budget.reserved)
            key = budget.reserve()
            error = ScorerError(
                "limited",
                attempts=1,
                usage_unknown=True,
                diagnostics={"status_code": status, "retry_after_seconds": 75},
            )
            assert await A["recover_rate_failure"](
                error, budget, before, 0, records.append, sleep=sleep
            )
            assert sleeps == [75]
            assert budget.charged_tokens == 65536
            assert key in budget.max_charged and not budget.unresolved
            assert len(budget.reserved) == 1  # No scorer call/reservation is replayed.
            assert [r["event"] for r in records] == ["cooldown_started", "cooldown_complete"]

    asyncio.run(exercise())


@pytest.mark.parametrize(
    "status,delay,incidents", [(None, 0, 0), (500, 0, 0), (429, 301, 0), (529, 1, 3)]
)
def test_unknown_failure_or_exhausted_recovery_budget_stays_blocked(
    tmp_path, status, delay, incidents
):
    async def exercise():
        async def sleep(seconds):
            pytest.fail("No cooldown or new dispatch is permitted")

        with InputTokenBudget(tmp_path / "ledger.jsonl") as budget:
            before = set(budget.reserved)
            key = budget.reserve()
            error = ScorerError(
                "failed",
                attempts=1,
                usage_unknown=True,
                diagnostics={"status_code": status, "retry_after_seconds": delay},
            )
            assert not await A["recover_rate_failure"](
                error, budget, before, incidents, lambda _: None, sleep=sleep
            )
            assert budget.unresolved == {key}
            assert not budget.max_charged

    asyncio.run(exercise())
