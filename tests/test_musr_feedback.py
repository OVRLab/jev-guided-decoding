import asyncio
import json
import runpy
from pathlib import Path

import pytest

from jev_guided_decoding.experiment_budget import BudgetExhausted, InputTokenBudget

HERE = Path(__file__).resolve().parents[1] / "research/iterations/musr_transfer"


def module():
    return runpy.run_path(str(HERE / "feedback.py"))


def case():
    return dict(
        id="fixture/1",
        task="object_placements",
        split="development",
        context="Alice moved the cup.",
        question="Where does Bob believe the cup is?",
        choices=["pantry", "hall"],
    )


class Provider:
    def __init__(self, failure=None):
        self.calls = 0
        self.failure = failure

    async def _evaluate(self, payload, parser, **kwargs):
        self.calls += 1
        assert kwargs == dict(timeout=90, max_attempts=1)
        if self.failure:
            raise self.failure
        raw = dict(
            model="jev-1.13.0",
            answers=dict(correct=dict(type="noul", noul=0.7)),
            usage=dict(input_tokens=250, output_tokens=10),
        )
        value = parser(raw["answers"])
        return value, raw["model"], 250, 10, 1, 0.01, raw


def test_single_judgment_binds_real_selection_without_references():
    m = module()
    p = m["payload"](case(), "Reasoning.\nANSWER: 2")
    assert list(p["questions"]) == ["correct"]
    assert p["state"]["response"] == "Reasoning.\nANSWER: 2"
    assert p["state"]["selection"] == dict(number=2, text="hall")
    assert m["payload"](case(), "ANSWER: 1 or 2")["state"]["selection"] is None
    with pytest.raises(ValueError):
        m["payload"](case() | dict(answer_index=1), "ANSWER: 2")


def test_one_reserved_attempt_success_no_duplicate_or_resume(tmp_path):
    m, provider = module(), Provider()
    with InputTokenBudget(tmp_path / "budget.jsonl", max_usd=0.05) as budget:
        feedback = m["Feedback"](provider, budget, tmp_path, delay=0)
        assert asyncio.run(feedback.score(case(), "ANSWER: 2")) == 0.7
        assert budget.charged_tokens == 250 and not budget.unresolved
        with pytest.raises(ValueError, match="Duplicate"):
            asyncio.run(feedback.score(case(), "ANSWER: 2"))
        assert provider.calls == 1
    request = json.loads((tmp_path / "requests.jsonl").read_text())
    response = json.loads((tmp_path / "responses.jsonl").read_text())
    assert request["reservation"] == response["reservation"]
    assert response["probability"] == 0.7 and response["attempts"] == 1
    with pytest.raises(ValueError, match="resume"):
        m["Feedback"](provider, None, tmp_path)


def test_timeout_retains_unknown_charge_and_cap_stops_before_dispatch(tmp_path):
    m, provider = module(), Provider(TimeoutError("secret-must-not-be-logged"))
    with InputTokenBudget(tmp_path / "budget.jsonl", max_usd=0.004) as budget:
        feedback = m["Feedback"](provider, budget, tmp_path, delay=0)
        with pytest.raises(TimeoutError):
            asyncio.run(feedback.score(case(), "ANSWER: 2"))
        assert budget.charged_tokens == 65536 and len(budget.unresolved) == 1
        with pytest.raises(BudgetExhausted):
            asyncio.run(feedback.score(case() | dict(id="fixture/2"), "ANSWER: 2"))
        assert provider.calls == 1
    failure = (tmp_path / "failures.jsonl").read_text()
    assert "secret-must-not-be-logged" not in failure
    assert json.loads(failure)["usage_unknown"] is True
