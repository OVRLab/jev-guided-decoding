import asyncio
import json

import httpx
import pytest

from jev_guided_decoding.jev import JevScorer
from jev_guided_decoding.types import Candidate, Request, ScorerError


def test_provider_error_keeps_bounded_details_without_echoing_a_credential():
    async def exercise():
        fake = "test-credential-never-publish"

        def reply(request):
            return httpx.Response(
                400,
                headers={"x-request-id": "request-123"},
                json={"error": "invalid shape", "debug": f"Bearer {fake}", "padding": "x" * 10000},
            )

        async with JevScorer(fake, max_retries=0, transport=httpx.MockTransport(reply)) as scorer:
            with pytest.raises(ScorerError) as failure:
                await scorer.score(
                    Request("Q", "E"), "", (Candidate((1,), "Claim", -0.1, "frame"),)
                )
        diagnostic = failure.value.diagnostics
        assert diagnostic["status_code"] == 400
        assert diagnostic["request_id"] == "request-123"
        assert "invalid shape" in diagnostic["body_excerpt"]
        assert fake not in json.dumps(diagnostic)
        assert len(diagnostic["body_excerpt"]) <= 4096
        assert diagnostic["body_truncated"]
        assert failure.value.usage_unknown

    asyncio.run(exercise())


@pytest.mark.parametrize("status", [429, 529])
def test_exhausted_retryable_response_keeps_status_and_unknown_usage(status):
    async def exercise():
        fake = "test-rate-limit-credential"
        calls = []

        def reply(request):
            calls.append(request)
            return httpx.Response(
                status,
                headers={"retry-after": "3", "x-request-id": "rate-request"},
                json={"error": "try later", "echo": fake},
            )

        async with JevScorer(fake, max_retries=0, transport=httpx.MockTransport(reply)) as scorer:
            with pytest.raises(ScorerError) as failure:
                await scorer.score(
                    Request("Q", "E"), "", (Candidate((1,), "Claim", -0.1, "frame"),)
                )
        assert len(calls) == failure.value.attempts == 1
        assert failure.value.usage_unknown
        assert failure.value.diagnostics["status_code"] == status
        assert failure.value.diagnostics["retry_after_seconds"] == 3
        assert failure.value.diagnostics["request_id"] == "rate-request"
        assert fake not in json.dumps(failure.value.diagnostics)

    asyncio.run(exercise())
