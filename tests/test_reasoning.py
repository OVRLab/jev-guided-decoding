import asyncio
import threading
from dataclasses import replace

import pytest

from jev_guided_decoding.framing import Frame, parse_frame
from jev_guided_decoding.reasoning import (
    ReasoningCancelled,
    ReasoningConfig,
    ReasoningController,
)
from jev_guided_decoding.types import (
    Candidate,
    Evaluation,
    Judgment,
    Proposal,
    Request,
    ScorerError,
)

REQUEST = Request("May Mira enter?", "A valid badge permits entry.")


def candidate(text, likelihood=-0.1, finish="frame"):
    return Candidate(tuple(map(ord, text)), text, likelihood, finish)


class Backend:
    def __init__(self, batches):
        self.batches = list(batches)
        self.prefixes = []

    def encode(self, request):
        assert "<step>" in request.system and "<final>" in request.system
        return (1,)

    def decode(self, ids):
        return "".join(map(chr, ids))

    def propose_frames(self, prompt_ids, accepted_ids, *, count, max_tokens, **kwargs):
        self.prefixes.append(accepted_ids)
        batch = self.batches.pop(0)
        if callable(batch):
            batch = batch(accepted_ids)
        assert len(batch) <= count
        assert all(len(c.token_ids) <= max_tokens for c in batch)
        batch = tuple(replace(c, full_text=self.decode(accepted_ids + c.token_ids)) for c in batch)
        return Proposal(
            batch,
            sum(len(c.token_ids) for c in batch),
            max((len(c.token_ids) for c in batch), default=0) * len(batch),
            (len(prompt_ids) + len(accepted_ids)) * len(batch),
            0.01,
        )


class Scorer:
    def __init__(self, scores=None):
        self.scores = scores or {}
        self.calls = []

    async def score(self, request, prefix, candidates, **kwargs):
        self.calls.append((prefix, candidates))
        judgments = []
        for c in candidates:
            frame = parse_frame(c.text)
            default = (0.95, None, 0.95) if frame.kind == "final" else (0.95, 0.9, None)
            judgments.append(Judgment(*self.scores.get(frame.body, default)))
        return Evaluation(tuple(judgments), "fake", 10, 2, 1, 0.01, {})


def run(backend, scorer=None, mode="jev", **config):
    return asyncio.run(
        ReasoningController(backend, ReasoningConfig(max_resamples=0, **config), scorer).run(
            REQUEST, mode
        )
    )


def test_frame_parser_preserves_content_and_rejects_incomplete_or_multiple_frames():
    assert parse_frame(" \n<step>Value 3.14. Dr. Li agrees.\nNext line.</step>\n") == Frame(
        "step", "Value 3.14. Dr. Li agrees.\nNext line."
    )
    assert parse_frame("<final>Not established.</final>") == Frame("final", "Not established.")
    for invalid in (
        "<step>unfinished",
        "<final></final>",
        "Answer: yes",
        "<step>x</final>",
        "<step>x</step><final>yes</final>",
        "<step><step>x</step></step>",
    ):
        assert parse_frame(invalid) is None


def test_final_summary_completes_without_eos_and_keeps_exact_token_path():
    step = candidate("<step>A badge permits entry.</step>")
    final = candidate("<final>Mira may enter.</final>")
    backend = Backend([[step], [final]])
    result = run(backend, Scorer())
    assert result.stop_reason == "complete" and result.phase == "complete"
    assert result.text == "Mira may enter."
    assert result.steps == ["A badge permits entry."]
    assert result.token_ids == step.token_ids + final.token_ids
    assert backend.prefixes == [(), step.token_ids]
    assert result.schema_version == "reasoning-v1"


def test_duplicate_candidates_are_scored_once_and_resampling_can_add_an_alternative():
    a = candidate("<step>A</step>")
    b = candidate("<step>B</step>")
    final = candidate("<final>Done</final>")
    backend = Backend([[a, a, a], [a, b, b], [final]])
    scorer = Scorer()
    config = ReasoningConfig(max_resamples=1)
    result = asyncio.run(ReasoningController(backend, config, scorer).run(REQUEST))
    assert result.stop_reason == "complete"
    assert [[c.text for c in call[1]] for call in scorer.calls] == [
        [a.text],
        [b.text],
        [final.text],
    ]
    assert result.duplicate_candidates == 4
    assert result.resamples == 1
    assert result.generated_tokens == 4 * len(a.token_ids) + 2 * len(b.token_ids) + len(
        final.token_ids
    )


def test_dead_end_restores_saved_sibling_without_rejected_prefix_tokens():
    a = candidate("<step>A</step>")
    b = candidate("<step>B</step>", -0.2)
    rejected = candidate("<step>Wrong</step>")
    final = candidate("<final>Recovered</final>")
    backend = Backend([[a, b], [rejected], [final]])
    result = run(backend, Scorer({"Wrong": (0.1, 0.9, None)}))
    assert result.stop_reason == "complete" and result.backtracks == 1
    assert backend.prefixes == [(), a.token_ids, b.token_ids]
    assert result.token_ids == b.token_ids + final.token_ids
    assert result.steps == ["B"]
    assert result.api_calls == 3 and result.expansions == 3


def test_low_completion_final_is_rejected_even_with_high_support():
    result = run(
        Backend([[candidate("<final>Only part</final>")]]), Scorer({"Only part": (0.99, None, 0.2)})
    )
    assert result.stop_reason == "no_eligible_branch"
    assert result.text == "" and result.phase == "stopped"


@pytest.mark.parametrize(
    "text,finish,reason",
    [
        ("<step>Truncated", "length", "incomplete_step"),
        ("", "eos", "premature_eos"),
        ("<step>Done</step>", "eos", "premature_eos"),
    ],
)
def test_incomplete_steps_and_early_eos_are_not_sent_to_jev(text, finish, reason):
    scorer = Scorer()
    result = run(Backend([[candidate(text, finish=finish)]]), scorer)
    assert result.stop_reason == reason
    assert scorer.calls == [] and result.text == ""


def test_baseline_needs_no_scorer_and_final_only_mode_scores_only_finals():
    step, final = candidate("<step>A</step>"), candidate("<final>Done</final>")
    assert run(Backend([[step], [final]]), mode="likelihood").stop_reason == "complete"
    scorer = Scorer()
    result = run(Backend([[step], [final]]), scorer, mode="final_jev")
    assert result.stop_reason == "complete"
    assert len(scorer.calls) == 1 and scorer.calls[0][1][0].text == final.text


@pytest.mark.parametrize(
    "setting,limit,reason",
    [
        ("max_context_tokens", 1, "context_budget"),
        ("max_prefill_tokens", 2, "prefill_budget"),
        ("max_decode_tokens", 2, "decode_budget"),
    ],
)
def test_global_work_budgets_prevent_unaffordable_proposal(setting, limit, reason):
    backend = Backend([])
    result = run(backend, Scorer(), **{setting: limit})
    assert result.stop_reason == reason and backend.prefixes == []


def test_api_budget_does_not_reset_when_backtracking():
    a, b = candidate("<step>A</step>"), candidate("<step>B</step>", -0.2)
    backend = Backend([[a, b], [candidate("<step>Wrong</step>")]])
    scorer = Scorer({"Wrong": (0.1, 0.9, None)})
    result = run(backend, scorer, max_api_calls=2)
    assert result.stop_reason == "api_budget" and result.api_calls == 2
    assert len(backend.prefixes) == 2


def test_depth_limit_tries_shallower_saved_alternative():
    a, b = candidate("<step>A</step>"), candidate("<final>Done</final>", -0.2)
    # At depth one the step cannot expand; the saved final can still complete.
    result = run(Backend([[a, b]]), Scorer({"A": (0.99, 0.99, None)}), max_steps=1)
    assert result.stop_reason == "complete" and result.text == "Done"


def test_expansion_limit_is_global_across_branches():
    a, b = candidate("<step>A</step>"), candidate("<step>B</step>", -0.2)
    backend = Backend([[a, b], [candidate("<step>Wrong</step>")]])
    result = run(backend, Scorer({"Wrong": (0.1, 0.9, None)}), max_expansions=2)
    assert result.stop_reason == "expansion_budget" and result.expansions == 2


def test_scorer_failure_retains_unknown_usage_and_does_not_fall_back():
    class Failing:
        async def score(self, *args, **kwargs):
            raise ScorerError("unavailable", attempts=1, usage_unknown=True)

    result = run(Backend([[candidate("<final>Maybe</final>")]]), Failing())
    assert result.stop_reason == "scorer_error" and result.usage_unknown
    assert result.api_calls == 1 and result.text == ""


def test_late_score_cannot_commit_a_final_answer():
    now = [0.0]

    class Late(Scorer):
        async def score(self, *args, **kwargs):
            result = await super().score(*args, **kwargs)
            now[0] = 2.0
            return result

    controller = ReasoningController(
        Backend([[candidate("<final>Late</final>")]]),
        ReasoningConfig(max_seconds=1, max_resamples=0),
        Late(),
        clock=lambda: now[0],
    )
    result = asyncio.run(controller.run(REQUEST))
    assert result.stop_reason == "time_budget" and result.text == "" and result.token_ids == ()


def test_cancellation_waits_for_model_worker_and_preserves_a_cancelled_result():
    started, exited = threading.Event(), threading.Event()

    class Blocking(Backend):
        def propose_frames(self, *args, cancel_event, **kwargs):
            started.set()
            assert cancel_event.wait(5)
            exited.set()
            return Proposal((), 0, 0, 0, 0.01)

    async def exercise():
        controller = ReasoningController(Blocking([]), ReasoningConfig(), Scorer())
        task = asyncio.create_task(controller.run(REQUEST))
        assert await asyncio.to_thread(started.wait, 5)
        task.cancel()
        with pytest.raises(ReasoningCancelled) as error:
            await task
        assert exited.is_set()
        assert error.value.result.stop_reason == "cancelled"
        assert error.value.result.phase == "stopped"

    asyncio.run(exercise())


def test_scorer_cancellation_preserves_unknown_usage_and_does_not_accept_an_answer():
    started = asyncio.Event()

    class Waiting:
        async def score(self, *args, **kwargs):
            started.set()
            await asyncio.Future()

    async def exercise():
        controller = ReasoningController(
            Backend([[candidate("<final>Maybe</final>")]]), ReasoningConfig(), Waiting()
        )
        task = asyncio.create_task(controller.run(REQUEST))
        await asyncio.wait_for(started.wait(), 1)
        task.cancel()
        with pytest.raises(ReasoningCancelled) as error:
            await task
        assert error.value.result.usage_unknown
        assert error.value.result.api_attempts_unknown
        assert error.value.result.text == ""

    asyncio.run(exercise())


def test_path_limit_preserves_partial_steps_without_a_final_answer():
    a = candidate("<step>A</step>")
    result = run(Backend([[a]]), Scorer(), max_path_tokens=len(a.token_ids))
    assert result.stop_reason == "path_budget"
    assert result.steps == ["A"] and result.text == ""


def test_pending_capacity_is_bounded_and_dropped_branches_are_traceable():
    batch = [candidate(f"<step>{letter}</step>") for letter in "ABC"]
    result = run(
        Backend([batch, [candidate("<final>Done</final>")]]),
        Scorer(),
        keep_branches=3,
        max_pending=1,
    )
    assert result.pending_peak == 1
    assert any(entry["event"] == "prune_pending" for entry in result.trace)


def test_wrong_number_of_judgments_cannot_accept_an_unscored_candidate():
    class Wrong:
        async def score(self, *args, **kwargs):
            return Evaluation((), "fake", 2, 1, 1, 0.1, {})

    result = run(Backend([[candidate("<final>Unknown</final>")]]), Wrong())
    assert result.stop_reason == "scorer_error" and result.text == ""


def test_exhausted_resampling_budget_keeps_an_already_validated_step():
    step = candidate("<step>A</step>")
    controller = ReasoningController(
        Backend([[step, step, step]]),
        ReasoningConfig(max_api_calls=1, max_resamples=1),
        Scorer(),
    )
    result = asyncio.run(controller.run(REQUEST))
    assert result.stop_reason == "api_budget"
    assert result.steps == ["A"] and result.token_ids == step.token_ids
    assert result.api_calls == 1 and result.resamples == 0


@pytest.mark.parametrize("support,progress", [(float("nan"), 0.9), (0.9, float("nan")), (2, 0.9)])
def test_invalid_custom_scorer_probability_cannot_accept_a_branch(support, progress):
    result = run(Backend([[candidate("<step>A</step>")]]), Scorer({"A": (support, progress, None)}))
    assert result.stop_reason == "scorer_error" and result.steps == []
