import asyncio
from dataclasses import replace

import pytest

from jev_guided_decoding.framing import parse_frame
from jev_guided_decoding.generated_answer import (
    GeneratedAnswerConfig,
    GeneratedAnswerController,
    IntermediateScorer,
    prepare_generated_request,
)
from jev_guided_decoding.types import (
    Candidate,
    Evaluation,
    Judgment,
    Proposal,
    Request,
    ScorerError,
)

REQUEST = Request(
    "What is the result? Put only the number inside the final frame.",
    "Two groups each have three items.",
)


def candidate(text, score=-0.1, finish="frame"):
    return Candidate(tuple(map(ord, text)), text, score, finish)


class Backend:
    def __init__(self, batches):
        self.batches, self.calls = list(batches), []

    def encode(self, request):
        self.request = request
        return (1,)

    def encode_control(self, text):
        return tuple(map(ord, text))

    def decode(self, ids):
        return "".join(map(chr, ids))

    def propose_frames(self, prompt_ids, accepted_ids, **kwargs):
        self.calls.append((accepted_ids, kwargs))
        batch = self.batches.pop(0)
        if callable(batch):
            batch = batch(accepted_ids, kwargs)
        assert len(batch) <= kwargs["count"]
        assert all(len(c.token_ids) <= kwargs["max_tokens"] for c in batch)
        batch = tuple(replace(c, full_text=self.decode(accepted_ids + c.token_ids)) for c in batch)
        return Proposal(
            batch,
            sum(len(c.token_ids) for c in batch),
            max((len(c.token_ids) for c in batch), default=0) * kwargs["count"],
            (len(prompt_ids) + len(accepted_ids)) * kwargs["count"],
            0.01,
        )


class Scorer:
    def __init__(self, scores=None):
        self.calls, self.scores = [], scores or {}

    async def score(self, request, prefix, candidates, **kwargs):
        self.calls.append((request, prefix, candidates, kwargs))
        for c in candidates:
            assert parse_frame(c.text).kind == "step"
        return Evaluation(
            tuple(
                Judgment(*self.scores.get(parse_frame(c.text).body, (0.9, 0.8))) for c in candidates
            ),
            "jev-1.13.0",
            10,
            2,
            1,
            0.01,
            {},
        )


def run(backend, scorer=None, mode="jev", **config):
    return asyncio.run(
        GeneratedAnswerController(
            backend, GeneratedAnswerConfig(max_steps=1, **config), scorer
        ).run(REQUEST, mode)
    )


def test_jev_changes_intermediate_selection_but_final_is_only_granite_tokens():
    wrong, right = candidate("2 + 3 = 5.</step>", -0.1), candidate("2 * 3 = 6.</step>", -0.2)
    final = candidate("6</final>")
    backend = Backend([[wrong, right], [final]])
    scorer = Scorer({"2 + 3 = 5.": (0.1, 0.9), "2 * 3 = 6.": (0.9, 0.9)})
    result = run(backend, scorer)
    assert result.text == "6" and result.stop_reason == "complete"
    assert result.output_source == "granite_generated"
    assert result.final_token_ids == final.token_ids
    assert result.generated_token_ids == right.token_ids + final.token_ids
    assert result.steps == ["2 * 3 = 6."]
    assert backend.decode(backend.calls[-1][0]) == "<step>2 * 3 = 6.</step>\n<final>"
    assert len(scorer.calls) == 1
    assert backend.calls[-1][1]["count"] == 1 and backend.calls[-1][1]["greedy"]


@pytest.mark.parametrize("mode", ["single", "likelihood", "jev"])
def test_identical_model_final_generation_when_no_step_is_usable(mode):
    bad = candidate("broken", finish="length")
    final = candidate("6</final>")
    backend = Backend([[bad], [final]])
    scorer = Scorer()
    result = run(backend, scorer, mode)
    assert result.text == "6" and result.steps == []
    assert backend.decode(backend.calls[-1][0]) == "<final>"
    assert scorer.calls == []
    assert result.generated_token_ids == final.token_ids


def test_all_jev_rejected_candidates_end_in_model_answer_without_rejected_tokens():
    backend = Backend([[candidate("Invented premise.</step>")], [candidate("6</final>")]])
    result = run(backend, Scorer({"Invented premise.": (0.1, 0.9)}))
    assert result.text == "6" and result.steps == []
    assert result.reasoning_stop_reason == "all_rejected"
    assert backend.decode(backend.calls[-1][0]) == "<final>"


def test_baseline_uses_likelihood_and_never_requires_or_calls_scorer():
    backend = Backend(
        [[candidate("A.</step>", -0.1), candidate("B.</step>", -0.3)], [candidate("6</final>")]]
    )
    result = run(backend, mode="likelihood")
    assert result.steps == ["A."] and result.api_calls == 0
    assert backend.request == prepare_generated_request(REQUEST)


def test_intermediate_scorer_refuses_a_final_even_if_called_accidentally():
    scorer = IntermediateScorer("fake")
    with pytest.raises(ValueError, match="intermediate"):
        scorer._build_payload(REQUEST, "", (candidate("<final>6</final>"),))


def test_budget_reserves_final_decode_and_prefill_before_any_reasoning():
    backend = Backend([[candidate("6</final>")]])
    result = run(backend, mode="single", max_decode_tokens=96, max_prefill_tokens=20)
    assert len(backend.calls) == 1
    assert backend.decode(backend.calls[0][0]) == "<final>"
    assert result.text == "6"


def test_incomplete_final_is_not_replaced_with_a_label_or_step_text():
    backend = Backend([[candidate("A.</step>")], [candidate("6", finish="length")]])
    result = run(backend, mode="single")
    assert result.text == "" and result.stop_reason == "incomplete_final"
    assert result.final_token_ids == tuple(map(ord, "6"))


def test_provider_failure_stops_without_final_or_hidden_fallback():
    class Broken(Scorer):
        async def score(self, *args, **kwargs):
            raise ScorerError("timeout", attempts=1, usage_unknown=True)

    backend = Backend([[candidate("A.</step>")]])
    result = run(backend, Broken())
    assert result.stop_reason == "scorer_error" and result.usage_unknown
    assert len(backend.calls) == 1 and not result.final_token_ids


def test_a_cancelled_final_never_counts_as_completed_even_if_text_is_complete():
    backend = Backend([[candidate("A.</step>")], [candidate("6</final>", finish="cancelled")]])
    result = run(backend, mode="single")
    assert result.stop_reason == "cancelled" and result.text == ""


def test_backend_cannot_fabricate_text_that_does_not_match_generated_ids():
    class LyingBackend(Backend):
        def propose_frames(self, *args, **kwargs):
            value = super().propose_frames(*args, **kwargs)
            return replace(
                value, candidates=tuple(replace(c, text="999</final>") for c in value.candidates)
            )

    backend = LyingBackend([[candidate("6</final>")]])
    result = run(backend, mode="single", max_decode_tokens=96)
    assert result.stop_reason == "backend_contract_error" and result.text == ""


def test_cancelled_model_worker_drains_before_request_ownership_is_released():
    import threading

    from jev_guided_decoding.reasoning import ReasoningCancelled

    entered, done = threading.Event(), threading.Event()

    class Slow(Backend):
        def propose_frames(self, prompt_ids, accepted_ids, *, cancel_event, **kwargs):
            entered.set()
            assert cancel_event.wait(2)
            done.set()
            return Proposal((), 1, 1, len(prompt_ids) + len(accepted_ids), 0.01)

    async def scenario():
        controller = GeneratedAnswerController(Slow([]), GeneratedAnswerConfig())
        task = asyncio.create_task(controller.run(REQUEST, "single"))
        await asyncio.to_thread(entered.wait, 2)
        task.cancel()
        with pytest.raises(ReasoningCancelled) as caught:
            await task
        assert done.is_set() and caught.value.result.generated_tokens == 1
        assert caught.value.result.stop_reason == "cancelled"

    asyncio.run(scenario())
