import asyncio
import json
import runpy
from pathlib import Path

import pytest

from jev_guided_decoding.experiment_budget import InputTokenBudget
from jev_guided_decoding.types import ScorerError

ROOT = Path(__file__).resolve().parents[1]


def module():
    return runpy.run_path(str(ROOT / "research/iterations/gated_repair_retry/feedback.py"))


class Provider:
    def __init__(self, results):
        self.results, self.calls = list(results), 0

    async def _evaluate(self, payload, parse, **kwargs):
        self.calls += 1
        assert kwargs["max_attempts"] == 1
        item = self.results.pop(0)
        if isinstance(item, Exception):
            raise item
        raw = {
            "model": "jev-1.13.0",
            "answers": {"correct": {"type": "noul", "noul": item}},
            "usage": {"input_tokens": 300, "output_tokens": 20},
        }
        return parse(raw["answers"]), raw["model"], 300, 20, 1, 0.1, raw


def error(code):
    return ScorerError(
        "Jev rejected request",
        attempts=1,
        usage_unknown=True,
        diagnostics={"status_code": code, "retry_after_seconds": 12},
    )


def case():
    return {
        "id": "gsm8k/train/example",
        "task": "gsm8k",
        "prompt": "What is 1+1?",
        "split": "train",
        "origin": "offline fixture",
    }


def test_retry_has_separate_prior_reservation_and_retains_every_unknown_charge(tmp_path):
    mod = module()
    sleeps = []

    async def sleep(delay):
        sleeps.append(delay)

    provider = Provider([error(529), error(503), 0.9])
    with InputTokenBudget(tmp_path / "budget.jsonl", max_usd=0.25, usd_per_million=0.042) as budget:
        f = mod["Feedback"](provider, budget, tmp_path, sleep=sleep)
        assert asyncio.run(f.score(case(), "Two")) == 0.9
        assert provider.calls == 3
        assert budget.charged_tokens == 65536 * 2 + 300
        assert not budget.unresolved
        assert sleeps == [2, 30, 60]
        assert asyncio.run(f.score(case(), "Two")) == 0.9
        assert provider.calls == 3
        with pytest.raises(ValueError):
            asyncio.run(f.score(case(), "Three"))
    requests = [json.loads(s) for s in (tmp_path / "new-requests.jsonl").read_text().splitlines()]
    assert len({r["reservation"] for r in requests}) == 3
    assert [r["attempt"] for r in requests] == [1, 2, 3]


def test_ambiguous_timeout_is_missing_without_replay_and_auth_is_fatal(tmp_path):
    mod = module()

    async def sleep(_):
        pass

    provider = Provider(
        [
            ScorerError(
                "Jev request failed or timed out; it was not replayed",
                attempts=1,
                usage_unknown=True,
            ),
            error(401),
        ]
    )
    with InputTokenBudget(tmp_path / "budget.jsonl", max_usd=0.25, usd_per_million=0.042) as budget:
        f = mod["Feedback"](provider, budget, tmp_path, sleep=sleep)
        assert asyncio.run(f.score(case(), "Two")) is None
        assert provider.calls == 1
        assert budget.charged_tokens == 65536
        with pytest.raises(ScorerError):
            asyncio.run(f.score({**case(), "id": "second"}, "Two"))
        assert provider.calls == 2


def test_legacy_failed_case_is_never_dispatched(tmp_path):
    mod = module()
    c = case()
    payload = mod["C"]["feedback_payload"](c, "Two")
    with InputTokenBudget(tmp_path / "budget.jsonl", max_usd=0.25, usd_per_million=0.042) as budget:
        reservation = budget.reserve()
        req = dict(id=c["id"], payload=payload, reservation=reservation)
        fail = dict(
            id=c["id"], reservation=reservation, usage_unknown=True, error_type="ScorerError"
        )
        (tmp_path / "api-requests.jsonl").write_text(json.dumps(req) + "\n")
        (tmp_path / "api-failures.jsonl").write_text(json.dumps(fail) + "\n")
        f = mod["Feedback"](Provider([]), budget, tmp_path)
        assert asyncio.run(f.score(c, "Two")) is None
        assert not budget.unresolved
        assert budget.charged_tokens == 65536


def test_four_explicit_overloads_then_missing_and_bounded_cooldown(tmp_path):
    mod = module()
    sleeps = []

    async def sleep(delay):
        sleeps.append(delay)

    with InputTokenBudget(tmp_path / "budget.jsonl", max_usd=0.25, usd_per_million=0.042) as budget:
        f = mod["Feedback"](Provider([error(529) for _ in range(4)]), budget, tmp_path, sleep=sleep)
        assert asyncio.run(f.score(case(), "Two")) is None
        assert sleeps == [2, 30, 60, 120]
        assert len(budget.max_charged) == 4
    other = tmp_path / "fatal"
    other.mkdir()
    e = error(529)
    e.diagnostics["retry_after_seconds"] = 301
    with InputTokenBudget(other / "budget.jsonl", max_usd=0.25, usd_per_million=0.042) as budget:
        f = mod["Feedback"](Provider([e]), budget, other, sleep=sleep)
        with pytest.raises(ScorerError):
            asyncio.run(f.score(case(), "Two"))


def test_prior_snapshot_refuses_any_training_resume(tmp_path):
    mod = runpy.run_path(str(ROOT / "research/iterations/gated_repair_retry/study.py"))
    (tmp_path / "training-steps.jsonl").write_text("{}\n")
    with pytest.raises(ValueError, match="Only pre-training"):
        mod["prior_check"](tmp_path, {}, [])


def test_missing_and_unknown_attempt_caps_stop_without_extra_dispatch(tmp_path):
    mod = module()

    async def sleep(_):
        pass

    timeout = ScorerError(
        "Jev request failed or timed out; it was not replayed", attempts=1, usage_unknown=True
    )
    with InputTokenBudget(tmp_path / "budget.jsonl", max_usd=0.25, usd_per_million=0.042) as budget:
        provider = Provider([timeout])
        f = mod["Feedback"](provider, budget, tmp_path, sleep=sleep)
        f.missing = 16
        with pytest.raises(ValueError, match="Missing-feedback"):
            asyncio.run(f.score(case(), "Two"))
        assert provider.calls == 1
    other = tmp_path / "capped"
    other.mkdir()
    with InputTokenBudget(other / "budget.jsonl", max_usd=0.25, usd_per_million=0.042) as budget:
        f = mod["Feedback"](Provider([]), budget, other, sleep=sleep)
        for _ in range(64):
            reservation = budget.reserve()
            f.retain(reservation)
        with pytest.raises(ValueError, match="Unknown-charge"):
            asyncio.run(f.score(case(), "Two"))
        assert f.scorer.calls == 0


def test_delivery_audit_binds_each_attempt_and_rejects_forged_usage(tmp_path):
    audit = runpy.run_path(str(ROOT / "research/iterations/gated_repair_retry/delivery.py"))
    mod = module()

    from datetime import UTC, datetime, timedelta

    elapsed = [0]

    async def sleep(delay):
        elapsed[0] += delay

    c = case()
    with InputTokenBudget(tmp_path / "budget.jsonl", max_usd=0.25, usd_per_million=0.042) as budget:
        f = mod["Feedback"](Provider([error(529), 0.9]), budget, tmp_path, sleep=sleep)
        f.score.__globals__["now"] = lambda: (
            datetime(2026, 9, 23, tzinfo=UTC) + timedelta(seconds=elapsed[0])
        ).isoformat()
        assert asyncio.run(f.score(c, "Two")) == 0.9
    availability = dict(
        id=c["id"], actual_probability_correct=0.9, effective_probability_correct=0.9, source="jev"
    )
    (tmp_path / "feedback-availability.jsonl").write_text(json.dumps(availability) + "\n")
    m = dict(
        jev="jev-1.13.0",
        jev_cap=0.25,
        usd_per_million=0.042,
        legacy_cases=0,
        legacy_missing_ids=[],
        max_missing_cases=16,
        max_unknown_attempts=64,
        attempts_per_case=4,
    )
    result = audit["audit"](tmp_path, {c["id"]: c}, {c["id"]: {"text": "Two"}}, m)
    assert result["physical_attempts"] == 2
    assert result["known_input_tokens"] == 300
    assert result["unknown_attempts"] == 1
    assert result["missing_cases"] == 0
    path = tmp_path / "new-responses.jsonl"
    receipt = json.loads(path.read_text())
    receipt["input_tokens"] = 299
    path.write_text(json.dumps(receipt) + "\n")
    with pytest.raises(ValueError):
        audit["audit"](tmp_path, {c["id"]: c}, {c["id"]: {"text": "Two"}}, m)
