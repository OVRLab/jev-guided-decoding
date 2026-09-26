import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
S = runpy.run_path(str(ROOT / "research/experiments/evidence_study.py"))


def test_policy_selection_and_negative_oracle_gate():
    outcomes = [
        {"count": 1, "strength": 1.0, "accuracy": 0.7, "clean_accuracy": 0.8, "mean_logprob": -0.5},
        {
            "count": 2,
            "strength": 2.0,
            "accuracy": 0.8,
            "clean_accuracy": 0.79,
            "mean_logprob": -0.4,
        },
    ]
    assert S["select_policy"](outcomes, 0.7, 0.8)["admitted"]
    assert not S["select_policy"](outcomes, 0.79, 0.8)["admitted"]
    assert not S["select_policy"](outcomes, 0.7, 0.9)["admitted"]


def test_analysis_retains_missing_failures_and_pairs_contexts_by_world():
    cases = [
        {"id": "w1/clean", "world_id": "w1", "condition": "clean", "reference": "red"},
        {"id": "w1/distracted", "world_id": "w1", "condition": "distracted", "reference": "blue"},
        {"id": "w2/clean", "world_id": "w2", "condition": "clean", "reference": "red"},
        {"id": "w2/distracted", "world_id": "w2", "condition": "distracted", "reference": "blue"},
    ]
    rows = [
        {
            "id": c["id"],
            "mode": "native",
            "status": "complete",
            "label": c["reference"],
            "seconds": 0.1,
        }
        for c in cases
    ]
    rows += [
        {
            "id": c["id"],
            "mode": "jev",
            "status": "complete",
            "label": c["reference"],
            "seconds": 0.2,
        }
        for c in cases[:2]
    ]
    result = S["summarize"](rows, cases, arms=["native", "jev"], controls=["native"], draws=100)
    assert result["arms"]["jev"]["accuracy"] == 0.5
    assert result["arms"]["jev"]["missing"] == 2
    assert result["comparisons"]["native"]["difference"] == -0.5
    assert result["worlds"] == 2
    with pytest.raises(ValueError):
        S["summarize"](
            rows + [rows[0]], cases, arms=["native", "jev"], controls=["native"], draws=0
        )


def test_public_scorer_payload_never_contains_reference_or_final_choice():
    E = runpy.run_path(str(ROOT / "research/experiments/evidence_scorer.py"))
    payload = E["payload_for"](
        {
            "id": "test",
            "question": "Which room contains parcel mio?",
            "sources": [{"id": "E01", "text": "parcel mio is in crate nara"}],
            "labels": ["red", "UNKNOWN"],
        },
        "jev-1.13.0",
    )
    assert set(payload["state"]) == {"question", "sources"}
    assert set(payload["questions"]) == {"relevance_0"}
    assert payload["questions"]["relevance_0"]["type"] == "noul"
    with pytest.raises(ValueError):
        E["payload_for"]({"id": "bad", "reference": "red"}, "jev-1.13.0")


def test_provider_recovery_uses_preserved_http_diagnostics():
    from jev_guided_decoding.types import ScorerError

    failure = ScorerError(
        "overloaded",
        attempts=1,
        usage_unknown=True,
        diagnostics={"status_code": 529, "retry_after_seconds": 90},
    )
    info = S["failure_info"](failure)
    assert info["status_code"] == 529
    assert info["retry_after"] == 90


@pytest.mark.parametrize(
    "status,wrong_model", [(200, False), (200, True), (400, False), (529, False)]
)
def test_relevance_receipt_and_unknown_reservation_are_durable(tmp_path, status, wrong_model):
    import asyncio

    import httpx

    from jev_guided_decoding.experiment_budget import InputTokenBudget
    from jev_guided_decoding.types import ScorerError

    E = runpy.run_path(str(ROOT / "research/experiments/evidence_scorer.py"))
    view = {
        "id": "case",
        "question": "Which room contains parcel mio?",
        "sources": [{"id": "E01", "text": "parcel mio is in crate nara"}],
        "labels": ["red", "UNKNOWN"],
    }
    calls = []

    def reply(request):
        calls.append(request)
        return httpx.Response(
            status,
            json={
                "model": "wrong" if wrong_model else "jev-1.13.0",
                "usage": {"input_tokens": 30, "output_tokens": 2},
                "answers": {"relevance_0": {"type": "noul", "noul": 0.8}},
            },
        )

    async def exercise():
        with InputTokenBudget(tmp_path / "ledger.jsonl") as budget:
            async with E["EvidenceScorer"](
                "test-key", budget=budget, transport=httpx.MockTransport(reply)
            ) as scorer:
                if status == 200 and not wrong_model:
                    result = await scorer.score(view)
                    assert result.scores == (0.8,)
                    assert budget.charged_tokens == 30
                else:
                    with pytest.raises(ScorerError):
                        await scorer.score(view)
                    assert budget.charged_tokens == 65536
                    with pytest.raises(ScorerError, match="Unsettled"):
                        await scorer.score(view)
                assert len(calls) == 1

    asyncio.run(exercise())
