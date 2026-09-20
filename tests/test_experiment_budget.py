import json

import pytest

from jev_guided_decoding.experiment_budget import BudgetExhausted, InputTokenBudget


def test_reserved_unknown_usage_survives_restart_and_blocks_overspending(tmp_path):
    path = tmp_path / "budget.jsonl"
    with InputTokenBudget(path, max_usd=0.004) as budget:
        token = budget.reserve()
        assert budget.charged_tokens == 65536
        with pytest.raises(BudgetExhausted):
            budget.reserve()
    with InputTokenBudget(path, max_usd=0.004) as budget:
        assert budget.charged_tokens == 65536
        with pytest.raises(BudgetExhausted):
            budget.reserve()
        budget.settle(token, 100)
        assert budget.charged_tokens == 100
        budget.reserve()


def test_budget_lease_prevents_two_spenders_and_terms_cannot_change(tmp_path):
    path = tmp_path / "budget.jsonl"
    with InputTokenBudget(path, max_usd=3):
        with pytest.raises(FileExistsError):
            with InputTokenBudget(path, max_usd=3):
                pass
    with pytest.raises(ValueError, match="terms"):
        with InputTokenBudget(path, max_usd=4):
            pass
    assert not path.with_suffix(".lock").exists()


def test_budget_rejects_double_settlement_and_invalid_usage(tmp_path):
    with InputTokenBudget(tmp_path / "budget.jsonl", max_usd=1) as budget:
        token = budget.reserve()
        for value in (-1, 65537, True):
            with pytest.raises(ValueError):
                budget.settle(token, value)
        budget.settle(token, 123)
        with pytest.raises(ValueError):
            budget.settle(token, 0)


def test_truncated_budget_record_fails_closed(tmp_path):
    path = tmp_path / "budget.jsonl"
    with InputTokenBudget(path, max_usd=1) as budget:
        budget.reserve()
    with path.open("a") as stream:
        stream.write("{")
    with pytest.raises(json.JSONDecodeError):
        with InputTokenBudget(path, max_usd=1):
            pass


@pytest.mark.parametrize("kind", ["success", "timeout", "wrong_model"])
def test_http_spending_is_reserved_before_dispatch_and_only_known_usage_is_refunded(tmp_path, kind):
    import asyncio

    import httpx

    from jev_guided_decoding.experiment_budget import BudgetedIntermediateScorer
    from jev_guided_decoding.types import Candidate, Request, ScorerError

    calls = []
    with InputTokenBudget(tmp_path / "budget.jsonl", max_usd=0.004) as budget:

        def respond(request):
            calls.append(request)
            assert budget.charged_tokens == 65536
            if kind == "timeout":
                raise httpx.ReadTimeout("private transport detail")
            return httpx.Response(
                200,
                json={
                    "model": "jev-1.13.0" if kind == "success" else "unexpected-version",
                    "answers": {
                        "support_0": {"type": "noul", "noul": 0.9},
                        "relevance_0": {"type": "noul", "noul": 0.8},
                    },
                    "usage": {"input_tokens": 123, "output_tokens": 7},
                },
            )

        async def scenario():
            async with BudgetedIntermediateScorer(
                "fake", budget, transport=httpx.MockTransport(respond)
            ) as scorer:
                return await scorer.score(
                    Request("Q", "Evidence"),
                    "",
                    (Candidate((1,), "<step>Reason</step>", -0.1, "frame"),),
                )

        if kind == "success":
            result = asyncio.run(scenario())
            assert result.input_tokens == budget.charged_tokens == 123
        else:
            with pytest.raises(ScorerError) as error:
                asyncio.run(scenario())
            assert error.value.usage_unknown and budget.charged_tokens == 65536
        assert len(calls) == 1
