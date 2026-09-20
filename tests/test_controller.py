import asyncio

import pytest

from jev_guided_decoding import Controller, DecodeConfig, Request
from jev_guided_decoding.types import Candidate, Evaluation, Judgment, Proposal, ScorerError

REQUEST = Request("Who owns the checklist?", "Mira owns the checklist. Tomas is the backup.")


class FakeBackend:
    def __init__(self, batches):
        self.batches = iter(batches)
        self.calls = []

    def encode(self, request):
        return (999,)

    def decode(self, ids):
        return " ".join(str(i) for i in ids)

    def propose(self, prompt_ids, accepted_ids, **kwargs):
        self.calls.append((accepted_ids, kwargs))
        candidates = tuple(next(self.batches))
        return Proposal(
            candidates,
            sum(len(c.token_ids) for c in candidates),
            max(len(c.token_ids) for c in candidates) * len(candidates),
            10,
            0.01,
        )


class FakeScorer:
    def __init__(self, evaluations):
        self.evaluations = iter(evaluations)

    async def score(self, *args, **kwargs):
        value = next(self.evaluations)
        if isinstance(value, Exception):
            raise value
        return Evaluation(tuple(value), "test", 100, 10, 1, 0.01, {})


def candidate(token, logprob=-1.0, reason="sentence"):
    return Candidate((token,), str(token), logprob, reason)


def run(backend, judgments, config=None, mode="jev"):
    return asyncio.run(
        Controller(
            backend,
            config or DecodeConfig(candidates=2),
            FakeScorer(judgments),
        ).run(REQUEST, mode)
    )


def test_rejected_tokens_never_reach_the_next_generation_prefix():
    backend = FakeBackend([[candidate(1), candidate(2)], [candidate(3, reason="eos")]])
    result = run(backend, [[Judgment(0.1, 0.9), Judgment(0.9, 0.9)], [Judgment(0.9, 0.9, 0.9)]])
    assert result.token_ids == (2, 3)
    assert backend.calls[1][0] == (2,)
    assert result.stop_reason == "eos"
    assert result.api_calls == 2
    assert result.jev_input_tokens == 200


def test_all_rejected_retries_same_prefix_then_stops_without_fallback():
    backend = FakeBackend([[candidate(1)], [candidate(2)]])
    result = run(backend, [[Judgment(0.1, 0.9)], [Judgment(0.2, 0.9)]])
    assert result.stop_reason == "all_rejected"
    assert result.token_ids == ()
    assert [c[0] for c in backend.calls] == [(), ()]
    assert backend.calls[0][1]["seed"] != backend.calls[1][1]["seed"]
    assert result.generated_tokens == 2


def test_eos_requires_complete_answer():
    backend = FakeBackend([[candidate(1, reason="eos")]])
    result = run(backend, [[Judgment(0.99, 0.99, 0.1)]], DecodeConfig(max_retries=0))
    assert result.stop_reason == "all_rejected"
    assert result.token_ids == ()


def test_empty_eos_checks_completion_without_demanding_new_information():
    backend = FakeBackend(
        [
            [candidate(1)],
            [Candidate((2,), "", -1, "eos")],
        ]
    )
    result = run(backend, [[Judgment(0.9, 0.9)], [Judgment(0.9, None, 0.9)]])
    assert result.stop_reason == "eos"
    assert result.token_ids == (1, 2)


def test_service_failure_is_explicit_and_does_not_replay_generation():
    backend = FakeBackend([[candidate(1)]])
    result = run(backend, [ScorerError("timeout", attempts=1, usage_unknown=True)])
    assert result.stop_reason == "scorer_error"
    assert result.api_calls == 1
    assert result.usage_unknown
    assert result.token_ids == ()
    assert len(backend.calls) == 1


def test_decode_budget_counts_rejected_branches_and_padding_slots():
    backend = FakeBackend([[candidate(1), candidate(2)]])
    result = run(
        backend,
        [[Judgment(0.1, 0.1), Judgment(0.1, 0.1)]],
        DecodeConfig(candidates=2, max_decode_tokens=2, chunk_tokens=99),
    )
    assert backend.calls[0][1]["max_tokens"] == 1
    assert result.stop_reason == "decode_budget"
    assert result.decode_token_slots == 2


def test_api_budget_stops_before_another_candidate_batch():
    backend = FakeBackend([[candidate(1)]])
    result = run(backend, [[Judgment(0.9, 0.9)]], DecodeConfig(max_api_calls=1))
    assert result.stop_reason == "api_budget"
    assert len(backend.calls) == 1


def test_likelihood_control_selects_highest_model_logprob_without_jev():
    backend = FakeBackend([[candidate(1, -2, "eos"), candidate(2, -0.5, "eos")]])
    result = run(backend, [], mode="likelihood")
    assert result.token_ids == (2,)
    assert result.api_calls == 0


def test_answer_budget_preserves_existing_prefix():
    backend = FakeBackend([[candidate(1)]])
    result = run(backend, [], DecodeConfig(max_answer_tokens=1), mode="greedy")
    assert result.token_ids == (1,)
    assert result.stop_reason == "answer_budget"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"candidates": 0},
        {"max_retries": -1},
        {"chunk_tokens": 1.5},
        {"support_threshold": float("nan")},
        {"max_seconds": float("inf")},
        {"seed": -1},
    ],
)
def test_invalid_budgets_fail_before_work(kwargs):
    with pytest.raises(ValueError):
        DecodeConfig(**kwargs)
