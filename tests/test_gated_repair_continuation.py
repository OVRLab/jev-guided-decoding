import asyncio
import runpy
from pathlib import Path

import pytest

from jev_guided_decoding.experiment_budget import InputTokenBudget
from jev_guided_decoding.types import ScorerError

ROOT = Path(__file__).resolve().parents[1]


def module():
    return runpy.run_path(str(ROOT / "research/iterations/gated_repair_continue/feedback.py"))


def test_missing_is_neutral_not_a_receipt_and_only_transients_are_admitted():
    m = module()
    assert m["effective"](None) == 0.5
    assert m["effective"](0.8) == 0.8
    assert m["recoverable"](ScorerError("error", diagnostics={"status_code": 529}), 1)
    assert not m["recoverable"](ScorerError("error", diagnostics={"status_code": 401}), 1)
    assert not m["recoverable"](
        ScorerError("invalid response", diagnostics={"status_code": 200}), 1
    )
    assert not m["recoverable"](ScorerError("error", diagnostics={"status_code": 529}), 8)
    with pytest.raises(ValueError):
        m["effective"](float("nan"))


def test_failed_request_is_never_replayed_and_charge_remains(tmp_path):
    m = module()
    waits = []

    class Scorer:
        calls = 0

        async def _evaluate(self, payload, parse, **kwargs):
            self.calls += 1
            raise ScorerError(
                "error",
                attempts=1,
                usage_unknown=True,
                diagnostics={"status_code": 529, "retry_after_seconds": 1},
            )

    async def sleep(seconds):
        waits.append(seconds)

    case = dict(id="train/x", task="gsm8k", split="train", prompt="Question?", origin="train/x")
    scorer = Scorer()

    async def scenario():
        with InputTokenBudget(
            tmp_path / "budget.jsonl", max_usd=0.25, usd_per_million=0.042
        ) as budget:
            f = m["Feedback"](scorer, budget, tmp_path, sleep=sleep)
            assert await f.score(case, "draft") is None
            assert await f.score(case, "draft") is None
            assert scorer.calls == 1
            assert budget.charged_tokens == 65536
            assert len(budget.max_charged) == 1

    asyncio.run(scenario())
    assert waits == [60]
    assert not (tmp_path / "api-responses.jsonl").exists()


def test_authentication_failure_stops_without_neutral_fallback(tmp_path):
    m = module()

    class Scorer:
        async def _evaluate(self, *args, **kwargs):
            raise ScorerError(
                "auth", attempts=1, usage_unknown=True, diagnostics={"status_code": 401}
            )

    async def scenario():
        with InputTokenBudget(
            tmp_path / "budget.jsonl", max_usd=0.25, usd_per_million=0.042
        ) as budget:
            f = m["Feedback"](Scorer(), budget, tmp_path)
            with pytest.raises(ScorerError):
                await f.score(
                    dict(id="x", task="arc", split="test", prompt="Q", origin="x"), "draft"
                )
            assert len(budget.unresolved) == 1

    asyncio.run(scenario())


def test_recovery_only_dispatches_new_cases_and_preserves_real_receipt(tmp_path):
    m = module()

    class Scorer:
        calls = 0

        async def _evaluate(self, payload, parse, **kwargs):
            assert kwargs == dict(timeout=90, max_attempts=1)
            self.calls += 1
            if self.calls == 1:
                raise ScorerError(
                    "busy", attempts=1, usage_unknown=True, diagnostics={"status_code": 429}
                )
            raw = dict(
                model="jev-1.13.0",
                answers={"correct": dict(type="noul", noul=0.8)},
                usage=dict(input_tokens=50, output_tokens=20),
            )
            return parse(raw["answers"]), raw["model"], 50, 20, 1, 0.1, raw

    async def sleep(seconds):
        assert seconds == 60

    async def scenario():
        with InputTokenBudget(
            tmp_path / "budget.jsonl", max_usd=0.25, usd_per_million=0.042
        ) as budget:
            scorer = Scorer()
            f = m["Feedback"](scorer, budget, tmp_path, sleep=sleep)
            case = dict(id="a", task="arc", split="train", prompt="First?", origin="a")
            assert await f.score(case, "draft") is None
            assert await f.score(case | {"id": "b", "prompt": "Second?"}, "other") == 0.8
            assert await f.score(case, "draft") is None
            with pytest.raises(ValueError, match="input changed"):
                await f.score(case, "different draft")
            assert scorer.calls == 2 and budget.charged_tokens == 65586

    asyncio.run(scenario())


def test_generation_duplicate_and_unsupported_resume_are_refused(tmp_path):
    s = runpy.run_path(str(ROOT / "research/iterations/gated_repair_continue/study.py"))
    runner = s["Runner"].__new__(s["Runner"])
    runner.started_jobs = {("x", "native")}
    with pytest.raises(ValueError, match="duplicate"):
        runner.answer({"id": "x"}, "native", [1])
    (tmp_path / "selection.json").write_text("{}")
    with pytest.raises(ValueError, match="pre-training"):
        s["prior_check"](tmp_path, {}, [])


def test_unavailable_feedback_retains_native_without_reference_access():
    r = runpy.run_path(str(ROOT / "research/iterations/gated_repair_continue/retention.py"))
    assert r["route"](None) == "native"
    rows = [dict(id="x", arm="native", correct=False), dict(id="x", arm="live", correct=True)]
    assert r["replay"](rows, {"x": None}, "live")[0]["correct"] is False


def test_excessive_provider_cooldown_stops_without_followup(tmp_path):
    m = module()

    class Scorer:
        async def _evaluate(self, *args, **kwargs):
            raise ScorerError(
                "busy",
                attempts=1,
                usage_unknown=True,
                diagnostics={"status_code": 529, "retry_after_seconds": 301},
            )

    async def sleep(seconds):
        raise AssertionError("unbounded wait must not begin")

    async def scenario():
        with InputTokenBudget(
            tmp_path / "budget.jsonl", max_usd=0.25, usd_per_million=0.042
        ) as budget:
            f = m["Feedback"](Scorer(), budget, tmp_path, sleep=sleep)
            with pytest.raises(ScorerError):
                await f.score(
                    dict(id="x", task="arc", split="train", prompt="Q", origin="x"), "draft"
                )
            assert budget.charged_tokens == 65536 and len(budget.unresolved) == 1

    asyncio.run(scenario())
