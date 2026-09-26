import json
import runpy
from pathlib import Path

import httpx
import pytest

from jev_guided_decoding.experiment_budget import InputTokenBudget
from jev_guided_decoding.local_claims import LocalClaimScorer
from jev_guided_decoding.types import Candidate, Request, ScorerError

DATA = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "research/experiments/claim_worlds.py")
)


def test_oracle_requires_conjunction_and_does_not_infer_negation():
    case = {
        "facts": ["Mira is blue."],
        "rules": [[["Mira is blue.", "Mira is calm."], "Mira is ready."]],
        "entities": ["Mira"],
        "properties": ["blue", "calm", "ready"],
    }
    assert DATA["grade_claim"](case, "Mira is blue.")["correct"] is True
    assert DATA["grade_claim"](case, "Mira is ready.")["correct"] is False
    assert DATA["grade_claim"](case, "Mira is not ready.")["correct"] is False
    assert DATA["grade_claim"](case, "It is not established that Mira is ready.")["correct"] is True
    assert DATA["grade_claim"](case, "Mira is blue. Therefore Mira is ready.") is None


def test_oracle_rejects_reverse_rules_and_handles_explicit_negative():
    case = {
        "facts": ["Mira is ready.", "Mira is not calm."],
        "rules": [[["Mira is blue."], "Mira is ready."]],
        "entities": ["Mira"],
        "properties": ["blue", "calm", "ready"],
    }
    assert DATA["grade_claim"](case, "Mira is blue.")["correct"] is False
    assert DATA["grade_claim"](case, "Mira is not calm.")["correct"] is True
    assert DATA["grade_claim"](case, "It is not established that Mira is calm.")["correct"] is True


def test_fresh_worlds_have_unique_evidence_and_separate_rendering_templates():
    dev = DATA["worlds"]("development", 60)
    gate = DATA["worlds"]("gate", 100)
    assert len({r["id"] for r in dev + gate}) == 160
    assert not {r["evidence"] for r in dev}.intersection(r["evidence"] for r in gate)
    assert {r["template"] for r in dev}.isdisjoint(r["template"] for r in gate)
    assert len({r["motif"] for r in dev}) == 6
    for r in dev + gate:
        closure = DATA["closure"](r)
        assert all(
            not (f"{e} is {p}." in closure and f"{e} is not {p}." in closure)
            for e in r["entities"]
            for p in r["properties"]
        )


def candidate(text):
    return Candidate((1,), text, -0.1, "frame")


def test_local_payload_has_no_prefix_or_reference_and_one_specific_claim():
    scorer = LocalClaimScorer("test-key")
    payload = scorer._build_payload(
        Request("What follows?", "Mira is blue."),
        "A prior unsupported guess",
        (candidate("Mira is calm."),),
    )
    assert payload["state"] == {"evidence": "Mira is blue."}
    assert "prior unsupported" not in json.dumps(payload)
    assert set(payload["questions"]) == {"support_0", "assessable_0"}


def test_budgeted_local_scoring_rejects_wrong_version_and_preserves_reservation(tmp_path):
    async def exercise():
        def reply(request):
            return httpx.Response(
                200,
                json={
                    "model": "different-model",
                    "usage": {"input_tokens": 50, "output_tokens": 2},
                    "answers": {
                        "support_0": {"type": "noul", "noul": 0.9},
                        "assessable_0": {"type": "noul", "noul": 1.0},
                    },
                },
            )

        with InputTokenBudget(tmp_path / "budget.jsonl") as budget:
            async with LocalClaimScorer(
                "test-key", budget=budget, transport=httpx.MockTransport(reply)
            ) as scorer:
                with pytest.raises(ScorerError, match="model"):
                    await scorer.score(Request("Q", "E"), "", (candidate("Mira is calm."),))
                assert budget.charged_tokens == 65536

    import asyncio

    asyncio.run(exercise())


def test_http_400_leaves_unknown_usage_and_blocks_any_subsequent_dispatch(tmp_path):
    async def exercise():
        dispatched = []

        def reply(request):
            dispatched.append(request)
            return httpx.Response(400, json={"error": "Test failure, no usage receipt"})

        with InputTokenBudget(tmp_path / "budget.jsonl") as budget:
            async with LocalClaimScorer(
                "test-key", budget=budget, transport=httpx.MockTransport(reply)
            ) as scorer:
                with pytest.raises(ScorerError, match="HTTP 400") as failure:
                    await scorer.score(Request("Q", "E"), "", (candidate("Mira is blue."),))
                assert failure.value.usage_unknown
                with pytest.raises(ScorerError, match="Unsettled"):
                    await scorer.score(Request("Q", "E"), "", (candidate("Mira is blue."),))
                assert len(dispatched) == 1
                assert budget.charged_tokens == 65536
                assert len(budget.reserved) == 1 and not budget.settled

    import asyncio

    asyncio.run(exercise())
