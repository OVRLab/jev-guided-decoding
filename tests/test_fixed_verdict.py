import asyncio
from dataclasses import replace

import pytest
from test_reasoning import Backend, Scorer, candidate

from jev_guided_decoding.reasoning import ReasoningCancelled, ReasoningConfig
from jev_guided_decoding.types import Request, ScorerError
from jev_guided_decoding.verdict import (
    FixedVerdictController,
    VerdictConfig,
    VerdictEvaluation,
)

REQUEST = Request("Classify permission", "A certificate AND permit allow entry.")


def evaluation(probability=0.95):
    return VerdictEvaluation(
        "UNKNOWN",
        {
            "ENTAILED": (1 - probability) / 2,
            "CONTRADICTED": (1 - probability) / 2,
            "UNKNOWN": probability,
        },
        0.8,
        "fake",
        20,
        4,
        1,
        0.1,
        {},
        {},
    )


class Decider(Scorer):
    def __init__(self, scores=None, answer=None):
        super().__init__(scores)
        self.answer = answer or evaluation()
        self.decisions = []

    async def decide(self, request, steps, **kwargs):
        self.decisions.append((request, steps, kwargs))
        return self.answer


def run(backend, scorer, mode="fixed_jev", **config):
    return asyncio.run(
        FixedVerdictController(
            backend, ReasoningConfig(max_resamples=0, **config), scorer, VerdictConfig()
        ).run(REQUEST, mode)
    )


def test_unknown_is_available_when_granite_never_proposes_a_final():
    scorer = Decider({"Invented permit": (0.01, 0.9, None)})
    result = run(Backend([[candidate("<step>Invented permit</step>")]]), scorer)
    assert result.text == "UNKNOWN" and result.phase == "complete"
    assert result.output_source == "jev_choice"
    assert result.reasoning_outcome["stop_reason"] == "no_eligible_branch"
    assert result.token_ids == () and result.generated_tokens > 0
    assert result.api_calls == 2 and result.jev_input_tokens == 30
    assert scorer.decisions[0][1] == []


def test_choice_cannot_rewrite_the_generated_token_path_or_receive_its_final_label():
    final = candidate("<final>ENTAINED. Wrong answer.</final>")
    scorer = Decider()
    result = run(Backend([[final]]), scorer)
    assert result.token_ids == final.token_ids and result.text == "UNKNOWN"
    assert result.reasoning_outcome["text"] == "ENTAINED. Wrong answer."
    assert scorer.decisions[0][1] == []
    assert result.schema_version == "fixed-verdict-v1"


def test_reserved_call_survives_reasoning_api_exhaustion_with_exact_partial_steps():
    step = candidate("<step>Certificate established</step>")
    scorer = Decider()
    result = run(Backend([[step]]), scorer, max_api_calls=2)
    assert result.reasoning_outcome["stop_reason"] == "api_budget"
    assert result.token_ids == step.token_ids
    assert scorer.decisions[0][1] == ["Certificate established"]
    assert scorer.decisions[0][2]["max_attempts"] == 1
    assert result.api_calls == 2 and result.text == "UNKNOWN"


def test_direct_jev_needs_no_backend_and_has_zero_generation_work():
    scorer = Decider()
    result = run(None, scorer, mode="direct_jev", max_api_calls=1)
    assert result.phase == "complete" and result.text == "UNKNOWN"
    assert result.token_ids == () and result.generated_tokens == result.prefill_tokens == 0
    assert result.reasoning_outcome is None and scorer.calls == []
    assert result.api_calls == 1


def test_uncertainty_is_not_a_semantic_unknown_answer():
    result = run(None, Decider(answer=evaluation(0.4)), mode="direct_jev")
    assert result.text == "" and result.stop_reason == "uncertain_verdict"
    assert result.decision["choice"] == "UNKNOWN"


def test_upstream_service_error_does_not_trigger_another_call():
    class Failed(Decider):
        async def score(self, *args, **kwargs):
            raise ScorerError("failure", attempts=1, usage_unknown=True)

    scorer = Failed()
    result = run(Backend([[candidate("<step>A</step>")]]), scorer)
    assert result.stop_reason == "scorer_error" and result.text == ""
    assert result.usage_unknown and scorer.decisions == []


def test_final_timeout_retains_prior_work_and_unknown_usage():
    class Failed(Decider):
        async def decide(self, *args, **kwargs):
            raise ScorerError("timeout", attempts=1, usage_unknown=True)

    result = run(Backend([[candidate("<final>Done</final>")]]), Failed())
    assert result.stop_reason == "scorer_error" and result.text == ""
    assert result.api_calls == 2 and result.generated_tokens > 0 and result.usage_unknown


def test_late_choice_is_recorded_but_not_committed():
    now = [0.0]

    class Late(Decider):
        async def decide(self, *args, **kwargs):
            now[0] = 91.0
            return self.answer

    result = asyncio.run(
        FixedVerdictController(
            None, ReasoningConfig(max_seconds=90), Late(), VerdictConfig(), clock=lambda: now[0]
        ).run(REQUEST, "direct_jev")
    )
    assert result.text == "" and result.stop_reason == "time_budget"
    assert result.api_calls == 1 and result.decision is not None


def test_final_cancellation_remains_cancelled_and_never_commits_unknown():
    started = asyncio.Event()

    class Waiting(Decider):
        async def decide(self, *args, **kwargs):
            started.set()
            await asyncio.Future()

    async def exercise():
        controller = FixedVerdictController(None, ReasoningConfig(), Waiting(), VerdictConfig())
        task = asyncio.create_task(controller.run(REQUEST, "direct_jev"))
        await asyncio.wait_for(started.wait(), 1)
        task.cancel()
        with pytest.raises(ReasoningCancelled) as error:
            await task
        assert error.value.result.text == ""
        assert error.value.result.usage_unknown and error.value.result.api_attempts_unknown

    asyncio.run(exercise())


@pytest.mark.parametrize("value", [True, float("nan"), -1, 1.1])
def test_invalid_verdict_thresholds_fail_before_inference(value):
    with pytest.raises(ValueError):
        VerdictConfig(min_probability=value)


def test_impossible_reservation_is_rejected_before_generation():
    with pytest.raises(ValueError, match="reserve"):
        run(Backend([]), Decider(), max_api_calls=1)
    with pytest.raises(ValueError, match="reserve"):
        run(Backend([]), Decider(), max_seconds=5)


def test_tied_choice_does_not_arbitrarily_commit_a_verdict():
    answer = replace(
        evaluation(), probabilities={"ENTAILED": 0.5, "CONTRADICTED": 0, "UNKNOWN": 0.5}
    )
    controller = FixedVerdictController(
        None, ReasoningConfig(), Decider(answer=answer), VerdictConfig(min_probability=0.5)
    )
    result = asyncio.run(controller.run(REQUEST, "direct_jev"))
    assert result.stop_reason == "uncertain_verdict" and result.text == ""


@pytest.mark.parametrize("elapsed,expected_calls", [(81.0, 1), (91.0, 0)])
def test_reasoning_time_reservation_and_overrun_share_the_outer_deadline(elapsed, expected_calls):
    now = [0.0]

    class Slow(Backend):
        def propose_frames(self, *args, **kwargs):
            assert kwargs["max_seconds"] == 80
            proposal = super().propose_frames(*args, **kwargs)
            now[0] = elapsed
            return proposal

    scorer = Decider()
    controller = FixedVerdictController(
        Slow([[candidate("<step>Certificate</step>")]]),
        ReasoningConfig(max_seconds=90),
        scorer,
        VerdictConfig(),
        clock=lambda: now[0],
    )
    result = asyncio.run(controller.run(REQUEST))
    assert len(scorer.decisions) == expected_calls
    assert result.reasoning_outcome["stop_reason"] == "time_budget"
    assert result.generated_tokens > 0
    if expected_calls:
        assert scorer.decisions[0][2]["timeout"] == 9
        assert result.text == "UNKNOWN"
    else:
        assert result.text == "" and result.stop_reason == "time_budget"


def test_cancelling_reasoning_never_dispatches_the_final_choice():
    started = asyncio.Event()

    class Waiting(Decider):
        async def score(self, *args, **kwargs):
            started.set()
            await asyncio.Future()

    async def exercise():
        scorer = Waiting()
        controller = FixedVerdictController(
            Backend([[candidate("<step>A</step>")]]), ReasoningConfig(), scorer, VerdictConfig()
        )
        task = asyncio.create_task(controller.run(REQUEST))
        await asyncio.wait_for(started.wait(), 1)
        task.cancel()
        with pytest.raises(ReasoningCancelled) as error:
            await task
        assert scorer.decisions == []
        assert error.value.result.mode == "fixed_jev"
        assert error.value.result.reasoning_outcome["stop_reason"] == "cancelled"
        assert error.value.result.generated_tokens > 0 and error.value.result.usage_unknown

    asyncio.run(exercise())
