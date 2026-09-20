import asyncio
import copy
import json

import httpx
import pytest

from jev_guided_decoding.types import Request, ScorerError
from jev_guided_decoding.verdict import VerdictScorer


def response():
    return {
        "model": "jev-test",
        "answers": {
            "verdict": {
                "type": "choice",
                "choice": "UNKNOWN",
                "probabilities": {"ENTAILED": 0.03, "CONTRADICTED": 0.02, "UNKNOWN": 0.95},
                "confidence": 0.89,
            }
        },
        "usage": {"input_tokens": 123, "output_tokens": 30},
    }


def decide(transport):
    async def run():
        async with VerdictScorer("fake", transport=transport) as scorer:
            return await scorer.decide(Request("Classify the claim", "Given facts"), ["Tentative"])

    return asyncio.run(run())


def test_fixed_options_and_original_evidence_are_sent_without_generated_final_or_gold():
    captured = []

    def respond(request):
        captured.append(json.loads(request.content))
        return httpx.Response(200, json=response())

    result = decide(httpx.MockTransport(respond))
    payload = captured[0]
    assert payload["state"] == {
        "question": "Classify the claim",
        "evidence": "Given facts",
        "tentative_steps": ["Tentative"],
    }
    question = payload["questions"]["verdict"]
    assert question["type"] == "choice"
    assert set(question["criteria"]) == {"ENTAILED", "CONTRADICTED", "UNKNOWN"}
    assert "not evidence" in question["instructions"]
    assert result.choice == "UNKNOWN" and result.probabilities["UNKNOWN"] == 0.95
    assert result.confidence == 0.89 and result.input_tokens == 123
    assert result.payload == payload and result.raw_response == response()


@pytest.mark.parametrize(
    "field,value",
    [
        ("type", "noul"),
        ("choice", "ENTAINED"),
        ("choice", "ENTAILED"),
        ("choice", []),
        ("probabilities", {"ENTAILED": 0.5, "CONTRADICTED": 0.5}),
        ("probabilities", {"ENTAILED": 0.9, "CONTRADICTED": 0.9, "UNKNOWN": 0.9}),
        ("probabilities", {"ENTAILED": True, "CONTRADICTED": 0, "UNKNOWN": 0}),
        ("probabilities", {"ENTAILED": 0, "CONTRADICTED": -0.1, "UNKNOWN": 1.1}),
        ("probabilities", []),
        ("confidence", True),
        ("confidence", "0.9"),
        ("confidence", 1.1),
        ("confidence", None),
    ],
)
def test_invalid_choice_contract_is_an_error_not_unknown(field, value):
    raw = response()
    raw["answers"]["verdict"][field] = value
    with pytest.raises(ScorerError, match="invalid response") as error:
        decide(httpx.MockTransport(lambda request: httpx.Response(200, json=raw)))
    assert error.value.attempts == 1 and error.value.usage_unknown


@pytest.mark.parametrize("change", ["missing", "nan"])
def test_missing_choice_and_nonfinite_probability_are_rejected(change):
    raw = copy.deepcopy(response())
    if change == "missing":
        del raw["answers"]["verdict"]
    else:
        raw["answers"]["verdict"]["probabilities"]["UNKNOWN"] = float("nan")
    with pytest.raises(ScorerError):
        decide(httpx.MockTransport(lambda request: httpx.Response(200, text=json.dumps(raw))))


def test_transport_timeout_is_not_replayed():
    calls = []

    def respond(request):
        calls.append(request)
        raise httpx.ReadTimeout("private error")

    with pytest.raises(ScorerError) as error:
        decide(httpx.MockTransport(respond))
    assert len(calls) == 1 and error.value.usage_unknown
    assert "private error" not in str(error.value)
