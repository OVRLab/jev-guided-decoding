import asyncio
import hashlib
import json
import runpy
from pathlib import Path
from types import SimpleNamespace

import pytest

from jev_guided_decoding.local_claims import ClaimEvaluation, ClaimJudgment
from jev_guided_decoding.types import Request, ScorerError

LIVE = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "research/experiments/live_logit_checkpoint.py")
)


class Runtime:
    def __init__(self):
        self.base = SimpleNamespace(
            revision="pinned",
            encode=lambda r: (1,),
            decode=lambda ids: (
                "<step>Mira is blue.</step>" if ids[-1] == 4 else "<step>Mira is calm.</step>"
            ),
        )

    def inspect(self, prompt, prefix, **kwargs):
        return SimpleNamespace(
            options=((3, 0.6), (4, 0.3)),
            prefix_digest=hashlib.sha256(json.dumps(prompt + prefix).encode()).hexdigest(),
            seconds=0.1,
            prefill_tokens=2,
        )

    def lookahead(self, prompt, prefix, *, first_token, **kwargs):
        return {
            "token_ids": (first_token, first_token),
            "finish_reason": "frame",
            "rest_mean_logprob": -0.1,
            "seconds": 0.1,
            "generated_tokens": 1,
            "decode_token_slots": 1,
            "prefill_tokens": 3,
            "forced_tokens": 1,
        }

    def sample(self, state, bias, **kwargs):
        return 4, 0.3, 0.4


class Scorer:
    budget = object()
    model = "jev-1.13.0"

    async def score(self, request, prefix, candidates, **kwargs):
        assert request.evidence == "Mira is blue." and prefix == ""
        assert [c.text for c in candidates] == ["Mira is calm.", "Mira is blue."]
        return ClaimEvaluation(
            (ClaimJudgment(0.01, 1), ClaimJudgment(0.99, 1)), self.model, 100, 2, 1, 0.1, {}
        )


def run(runtime=None, scorer=None, record=None):
    return asyncio.run(
        LIVE["guide_checkpoint"](
            runtime or Runtime(),
            Request("Continue.", "Mira is blue.", "Test"),
            (1,),
            (2,),
            scorer=scorer or Scorer(),
            seed=42,
            record=record if record is not None else {},
        )
    )


def test_live_pipeline_scores_branches_then_commits_only_one_granite_token():
    record = {}
    accepted = run(record=record)
    assert accepted == (2, 4)
    assert record["selection"]["plan"]["bias"][4] > 0
    assert record["evaluation"]["input_tokens"] == 100
    assert record["status"] == "complete"


def test_service_failure_retains_work_and_commits_no_token():
    class Failed(Scorer):
        async def score(self, *args, **kwargs):
            raise ScorerError("Known test failure", attempts=1, usage_unknown=True)

    record = {}
    with pytest.raises(ScorerError):
        run(scorer=Failed(), record=record)
    assert record["status"] == "failed"
    assert len(record["branches"]) == 2
    assert "selection" not in record and "accepted_ids" not in record


def test_response_cannot_cross_a_model_revision_change():
    runtime = Runtime()

    class Swapped(Scorer):
        async def score(self, *args, **kwargs):
            result = await super().score(*args, **kwargs)
            runtime.base.revision = "changed"
            return result

    with pytest.raises(ValueError, match="revision"):
        run(runtime=runtime, scorer=Swapped())


def test_paid_pipeline_requires_a_durable_budget_before_model_work():
    scorer = Scorer()
    scorer.budget = None
    with pytest.raises(ValueError, match="budget"):
        run(scorer=scorer)


def test_cancellation_preserves_branch_work_without_committing_a_token():
    class Cancelled(Scorer):
        async def score(self, *args, **kwargs):
            raise asyncio.CancelledError()

    record = {}
    with pytest.raises(asyncio.CancelledError):
        run(scorer=Cancelled(), record=record)
    assert record["status"] == "cancelled"
    assert len(record["branches"]) == 2
    assert "accepted_ids" not in record


def test_no_complete_claim_causes_native_noop_without_api_dispatch():
    runtime = Runtime()
    runtime.base.decode = lambda ids: "<step>An unfinished"

    class Uncalled(Scorer):
        async def score(self, *args, **kwargs):
            raise AssertionError("No complete assertion should be scored")

    record = {}
    run(runtime=runtime, scorer=Uncalled(), record=record)
    assert record["selection"]["plan"]["bias"] == {}
    assert "evaluation" not in record
