import asyncio
import json

import httpx
import pytest

from jev_guided_decoding.reasoning_scorer import ReasoningScorer
from jev_guided_decoding.types import Candidate, Request, ScorerError


def test_phase_aware_questions_keep_prefix_untrusted_and_final_relevance_unasked():
    captured = []

    def respond(request):
        payload = json.loads(request.content)
        captured.append(payload)
        answers = {key: {"type": "noul", "noul": 0.9} for key in payload["questions"]}
        return httpx.Response(
            200,
            json={
                "model": "jev-test",
                "answers": answers,
                "usage": {"input_tokens": 20, "output_tokens": 5},
            },
        )

    async def exercise():
        async with ReasoningScorer("fake", transport=httpx.MockTransport(respond)) as scorer:
            return await scorer.score(
                Request("May Mira enter?", "A valid badge is required."),
                "<step>Mira has a badge.</step>",
                (
                    Candidate((1,), "<step>A badge permits entry.</step>", -0.1, "frame"),
                    Candidate((2,), "<final>Not established.</final>", -0.2, "frame"),
                ),
            )

    result = asyncio.run(exercise())
    questions = captured[0]["questions"]
    assert set(questions) == {"support_0", "relevance_0", "support_1", "completion_1"}
    assert "not an extra source" in json.dumps(questions["support_0"])
    assert "Not established" not in json.dumps(questions["support_0"])
    assert result.judgments[0].completion is None
    assert result.judgments[1].relevance is None
    assert result.judgments[1].completion == 0.9


def test_missing_final_completion_is_a_service_contract_error():
    def respond(request):
        return httpx.Response(
            200,
            json={
                "model": "fake",
                "answers": {"support_0": {"type": "noul", "noul": 0.99}},
                "usage": {"input_tokens": 1, "output_tokens": 1},
            },
        )

    async def exercise():
        async with ReasoningScorer("fake", transport=httpx.MockTransport(respond)) as scorer:
            with pytest.raises(ScorerError):
                await scorer.score(
                    Request("Q", "E"), "", (Candidate((1,), "<final>Yes</final>", -0.1, "frame"),)
                )

    asyncio.run(exercise())
