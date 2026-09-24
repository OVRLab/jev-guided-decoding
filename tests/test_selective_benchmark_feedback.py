import asyncio
import json
import runpy
from pathlib import Path

import pytest

from jev_guided_decoding.experiment_budget import InputTokenBudget
from jev_guided_decoding.types import ScorerError

ROOT = Path(__file__).parents[1]
OLD = runpy.run_path(str(ROOT / "tests/test_gated_repair_retry.py"))
Provider, error = OLD["Provider"], OLD["error"]


def module():
    return runpy.run_path(str(ROOT / "research/iterations/selective_benchmarks/feedback.py"))


def case():
    return dict(
        id="fixture/1",
        task="math",
        family="math",
        prompt="What is 1+1?",
        format="number",
        origin_id="1",
        cluster="1",
        split="development",
    )


def test_feedback_payload_excludes_reference_and_keeps_native_answer():
    m = module()
    p = m["payload"](case(), "#### 2")
    assert p["state"] == {"problem": "What is 1+1?", "response": "#### 2"}
    with pytest.raises(ValueError):
        m["payload"](case() | {"answer": "2"}, "#### 2")
    p = m["payload"](case() | {"format": "instruction"}, "hello")
    assert "all" in p["questions"]["correct"]["instructions"]


def test_retries_have_separate_charges_and_duplicate_input_is_not_resent(tmp_path):
    m = module()
    delays = []

    async def sleep(n):
        delays.append(n)

    provider = Provider([error(529), 0.2])
    with InputTokenBudget(tmp_path / "budget.jsonl", max_usd=0.15, usd_per_million=0.042) as budget:
        f = m["Feedback"](provider, budget, tmp_path, sleep=sleep)
        assert asyncio.run(f.score(case(), "two")) == 0.2
        assert delays == [2, 30]
        assert budget.charged_tokens == 65536 + 300
        assert asyncio.run(f.score(case(), "two")) == 0.2 and provider.calls == 2
        with pytest.raises(ValueError):
            asyncio.run(f.score(case(), "three"))
    req = [json.loads(line) for line in (tmp_path / "requests.jsonl").read_text().splitlines()]
    assert len({r["reservation"] for r in req}) == 2


def test_timeout_remains_missing_and_fatal_auth_is_not_retried(tmp_path):
    m = module()

    async def sleep(n):
        pass

    timeout = ScorerError(
        "Jev request failed or timed out; it was not replayed", attempts=1, usage_unknown=True
    )
    provider = Provider([timeout, error(401)])
    with InputTokenBudget(tmp_path / "budget.jsonl", max_usd=0.15, usd_per_million=0.042) as budget:
        f = m["Feedback"](provider, budget, tmp_path, sleep=sleep)
        assert asyncio.run(f.score(case(), "two")) is None
        assert provider.calls == 1 and budget.charged_tokens == 65536
        with pytest.raises(ScorerError):
            asyncio.run(f.score(case() | {"id": "fixture/2"}, "two"))
        assert provider.calls == 2


def test_uncertain_charge_cap_stops_before_new_dispatch_and_resume_refused(tmp_path):
    m = module()

    async def sleep(n):
        pass

    with InputTokenBudget(tmp_path / "budget.jsonl", max_usd=0.15, usd_per_million=0.042) as budget:
        f = m["Feedback"](Provider([]), budget, tmp_path, sleep=sleep)
        for _ in range(16):
            f.retain(budget.reserve())
        with pytest.raises(ValueError, match="Unknown-charge"):
            asyncio.run(f.score(case(), "two"))
        assert f.scorer.calls == 0
    (tmp_path / "requests.jsonl").write_text("{}\n")
    with pytest.raises(ValueError, match="resume"):
        m["Feedback"](Provider([]), None, tmp_path)
