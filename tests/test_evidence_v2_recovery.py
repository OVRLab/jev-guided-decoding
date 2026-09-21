"""Recovery must retain failed blocks and refuse started work."""

import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def recovery():
    return runpy.run_path(str(ROOT / "research/iterations/evidence_v2_recovery.py"))


def test_common_failure_keeps_denominator_without_invented_logprob():
    m = recovery()["recovery_metrics"]
    cases = [
        {"id": "a", "missing": False, "condition": "clean"},
        {"id": "b", "missing": True, "condition": "distracted"},
    ]
    rows = [
        {"id": "a", "status": "complete", "correct": True, "reference_logprob": -0.4},
        {"id": "b", "status": "failed"},
    ]
    result = m(rows, cases)
    assert result["accuracy"] == 0.5
    assert result["mean_logprob"] == -0.4
    assert result["missing"] == 0
    assert result["complete"] == 1


def test_recovery_accepts_only_bounded_transport_failures():
    allowed = recovery()["recoverable"]
    timeout = {
        "status_code": None,
        "usage_unknown": True,
        "message": "Jev request failed or timed out; it was not replayed",
    }
    assert allowed(timeout, 1)
    assert not allowed(timeout, 3)
    assert not allowed({**timeout, "message": "Unexpected model or attempt count"}, 1)
    assert not allowed({**timeout, "status_code": 401}, 1)


def test_recovery_refuses_duplicate_started_job(tmp_path):
    ns = recovery()
    (tmp_path / "starts.jsonl").write_text(
        '{"kind":"jev","stage":"development","id":"a","mode":"relevance"}\n'
    )
    (tmp_path / "inputs.jsonl").touch()
    runner = ns["RecoveryRunner"](None, tmp_path, {"max_seconds": 60})
    try:
        with pytest.raises(ValueError, match="replayed"):
            runner.start("jev", "development", "a", "relevance")
        runner.start("jev", "development", "b", "relevance")
    finally:
        runner.close()


def test_recovery_timeout_charges_unknown_and_next_context_only(tmp_path):
    import asyncio

    from jev_guided_decoding.experiment_budget import InputTokenBudget
    from jev_guided_decoding.types import ScorerError

    ns = recovery()
    (tmp_path / "starts.jsonl").touch()
    (tmp_path / "inputs.jsonl").touch()
    runner = ns["RecoveryRunner"](None, tmp_path, {"max_seconds": 60})
    case = {
        "id": "a",
        "question": "Which room?",
        "sources": [{"id": "s1", "text": "Record."}],
        "labels": ["red"],
    }
    with InputTokenBudget(tmp_path / "ledger", max_usd=1) as budget:

        class Fake:
            def __init__(self):
                self.budget = budget
                self.model = "jev-1.13.0"
                self.calls = 0

            async def score(self, view, *, timeout):
                assert timeout == 90
                self.calls += 1
                budget.reserve()
                raise ScorerError(
                    "Jev request failed or timed out; it was not replayed", usage_unknown=True
                )

        scorer = Fake()
        with (tmp_path / "scores").open("x") as stream:
            outcome = asyncio.run(runner.score(case, scorer, "development", stream))
            assert outcome[0] is None and outcome[2] == 60
            assert budget.charged_tokens == 65536 and not budget.unresolved
            with pytest.raises(ValueError, match="replayed"):
                asyncio.run(runner.score(case, scorer, "development", stream))
            assert scorer.calls == 1
    runner.close()
