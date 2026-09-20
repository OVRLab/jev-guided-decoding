import asyncio
import json

import httpx
import pytest

from jev_guided_decoding.jev import ENDPOINT, JevScorer, build_payload, load_api_key
from jev_guided_decoding.types import Candidate, Request, ScorerError

REQUEST = Request("Who is the backup?", "Mira owns the checklist. Tomas is the backup.")
CANDIDATES = (Candidate((1,), "Tomas.", -1, "eos"),)


def response(probability=0.9):
    return {
        "model": "jev-test",
        "usage": {"input_tokens": 123, "output_tokens": 12},
        "answers": {
            f"{kind}_0": {"type": "noul", "noul": probability}
            for kind in ("support", "relevance", "completion")
        },
    }


def score(handler, **kwargs):
    async def perform():
        async with JevScorer(
            "test-secret", transport=httpx.MockTransport(handler), **kwargs
        ) as scorer:
            return await scorer.score(REQUEST, "", CANDIDATES, timeout=1, max_attempts=3)

    return asyncio.run(perform())


def test_batches_independent_questions_and_preserves_actual_model_and_usage():
    def handler(request):
        assert str(request.url) == ENDPOINT
        payload = json.loads(request.content)
        assert len(payload["questions"]) == 3
        assert payload["state"]["evidence"] == REQUEST.evidence
        assert "test-secret" not in request.content.decode()
        return httpx.Response(200, json=response())

    result = score(handler)
    assert result.judgments[0].support == 0.9
    assert result.judgments[0].completion == 0.9
    assert result.model == "jev-test"
    assert result.input_tokens == 123
    assert result.raw_response == response()


def test_scores_exact_full_decoding_instead_of_joining_retokenized_fragments():
    candidate = Candidate((1,), "fragment", -1, "sentence", "Exact full decoding.")
    payload = build_payload(REQUEST, "prefix", (candidate,), "jev-test")
    assert payload["questions"]["support_0"]["instructions"]["proposed_answer"] == (
        "Exact full decoding."
    )
    assert "completion_0" not in payload["questions"]


def test_empty_eos_has_no_fabricated_relevance_probability():
    ending = (Candidate((2,), "", -1, "eos"),)
    payload = build_payload(REQUEST, "Tomas is the backup.", ending, "test")
    assert set(payload["questions"]) == {"support_0", "completion_0"}

    async def perform():
        raw = response()
        del raw["answers"]["relevance_0"]
        transport = httpx.MockTransport(lambda request: httpx.Response(200, json=raw))
        async with JevScorer("test", transport=transport) as scorer:
            return await scorer.score(REQUEST, "Tomas is the backup.", ending)

    result = asyncio.run(perform())
    assert result.judgments[0].relevance is None
    assert result.judgments[0].completion == 0.9


def test_429_retries_only_after_explicit_retryable_response():
    calls = []

    def handler(request):
        calls.append(request)
        return (
            httpx.Response(429, headers={"Retry-After": "0"})
            if len(calls) == 1
            else (httpx.Response(200, json=response()))
        )

    result = score(handler)
    assert result.attempts == 2
    assert len(calls) == 2


def test_long_retry_after_never_retries_early():
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(529, headers={"Retry-After": "1000"})

    with pytest.raises(ScorerError, match="budget exhausted"):
        score(handler)
    assert len(calls) == 1


def test_timeout_does_not_retry_possibly_billed_request():
    calls = []

    def handler(request):
        calls.append(request)
        raise httpx.ReadTimeout("timeout", request=request)

    with pytest.raises(ScorerError) as error:
        score(handler)
    assert error.value.usage_unknown
    assert error.value.attempts == 1
    assert len(calls) == 1
    assert "test-secret" not in str(error.value)


@pytest.mark.parametrize("bad", [float("nan"), -0.1, 1.1, "0.9", True])
def test_invalid_probabilities_are_errors_not_negative_judgments(bad):
    with pytest.raises(ScorerError, match="invalid response"):
        score(lambda request: httpx.Response(200, content=json.dumps(response(bad))))


def test_redirect_does_not_forward_credentials():
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(307, headers={"location": "https://example.org/"})

    with pytest.raises(ScorerError, match="HTTP 307"):
        score(handler)
    assert len(calls) == 1


def test_loads_key_without_serializing_it(monkeypatch, tmp_path):
    monkeypatch.setenv("TYPESAFE_API_KEY", "environment-secret")
    key_file = tmp_path / "key"
    key_file.write_text("file-secret\n")
    assert load_api_key() == "environment-secret"
    assert load_api_key(key_file) == "file-secret"
