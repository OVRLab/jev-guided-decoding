import asyncio
import hashlib
import json
import runpy
from pathlib import Path
from types import SimpleNamespace

import pytest

from jev_guided_decoding.local_claims import ClaimEvaluation, ClaimJudgment
from jev_guided_decoding.types import Candidate, Proposal, ScorerError

ROOT = Path(__file__).resolve().parents[1]
C = runpy.run_path(str(ROOT / "research/experiments/structured_controller.py"))
G = runpy.run_path(str(ROOT / "research/experiments/claim_grammar.py"))


class Base:
    revision = "frozen"

    def encode(self, request):
        assert "reference_label" not in request.question
        return (99,)

    def encode_control(self, text):
        return (1,) if text == "<step>" else (8,)

    def decode(self, ids):
        return "".join(
            {
                1: "<step>",
                2: "Mira is",
                3: " blue",
                4: " calm",
                5: ".</step>",
                8: "<final>",
                9: "TRUE",
            }.get(i, "")
            for i in ids
        )

    def propose_frames(self, prompt, prefix, **kwargs):
        return Proposal(
            (Candidate((9, 10), "TRUE", -0.1, "eos", self.decode(prefix) + "TRUE"),),
            2,
            2,
            len(prompt) + len(prefix),
            0.01,
        )


class Runtime:
    def __init__(self):
        self.base = Base()
        self.before_forward = None

    def make_grammar(self, *args):
        return G["TokenTrie"]([(1, 2, 3, 5), (1, 2, 4, 5)]), (1,)

    def inspect(self, prompt, prefix, *, allowed, count=4):
        if self.before_forward:
            self.before_forward(len(prompt) + len(prefix))
        options = tuple((t, 1 / len(allowed)) for t in allowed)
        return SimpleNamespace(
            options=options,
            prefix_digest=hashlib.sha256(json.dumps(prompt + prefix).encode()).hexdigest(),
            prefill_tokens=len(prompt) + len(prefix),
            seconds=0.01,
            syntax_mass=0.8,
            allowed_count=len(allowed),
        )

    def sample(self, state, bias, *, seed):
        # Test double preserves no-op identity and responds to positive bias.
        token = max(bias, key=bias.get) if bias else state.options[0][0]
        return token, 0.5, 0.5

    def continue_frame(self, prompt, prefix, *, grammar, frame_offset, record, **kwargs):
        state = self.inspect(prompt, prefix, allowed=grammar.allowed(prefix[frame_offset:]))
        token = state.options[0][0]
        record.update(
            token_ids=[token],
            generated_tokens=1,
            decode_token_slots=1,
            prefill_tokens=state.prefill_tokens,
            logprob_sum=0.0,
            finish_reason="frame",
            trace=[],
        )
        return record


class Scorer:
    model = "jev-1.13.0"
    budget = object()

    async def score(self, request, prefix, candidates, **kwargs):
        assert prefix == "" and request.evidence == "Mira is calm."
        assert [c.text for c in candidates] == ["Mira is blue.", "Mira is calm."]
        return ClaimEvaluation(
            (ClaimJudgment(0.01, 1), ClaimJudgment(0.99, 1)), self.model, 100, 2, 1, 0.01, {}
        )


VIEW = dict(
    id="a",
    entities=["Mira"],
    properties=["blue", "calm"],
    evidence="Mira is calm.",
    target="Mira is calm.",
)


def run(mode, scorer=None, record=None, limits=None):
    return asyncio.run(
        C["run_job"](
            VIEW, Runtime(), mode=mode, seed=42, scorer=scorer, record=record, limits=limits
        )
    )


def test_baselines_need_no_key_and_zero_bias_preserves_exact_token_path():
    staged = run("staged")
    zero = run("zero", Scorer())
    assert staged["accepted_ids"] == zero["accepted_ids"]
    assert staged["final"]["candidate"]["token_ids"] == zero["final"]["candidate"]["token_ids"]
    assert staged["label"] == "TRUE" and staged["status"] == "complete"
    assert run("native")["steps"] == []


def test_jev_changes_root_only_and_final_tokens_are_from_granite():
    result = run("jev", Scorer())
    assert result["steps"][0]["checkpoint"]["selection"]["token"] == 4
    assert result["accepted_ids"] == [1, 2, 4, 5, 1, 2, 4, 5]
    assert result["final"]["candidate"]["token_ids"] == (9, 10)
    assert result["work"]["forced_root_tokens"] == 4


def test_provider_failure_records_partial_work_and_no_final_or_selected_root():
    class Failed(Scorer):
        async def score(self, *args, **kwargs):
            raise ScorerError("offline failed", usage_unknown=True)

    record = {}
    with pytest.raises(ScorerError):
        run("jev", Failed(), record)
    assert record["status"] == "failed"
    assert len(record["steps"][0]["checkpoint"]["branches"]) == 2
    assert "final" not in record
    assert "selection" not in record["steps"][0]["checkpoint"]


def test_reasoning_budget_exhaustion_preserves_reserved_final_generation():
    result = run("staged", limits={"reasoning_forwards": 1})
    assert result["reasoning_stop"] == "budget"
    assert result["accepted_ids"] == []
    assert result["label"] == "TRUE"


def test_paid_mode_requires_durable_budget_and_rejects_oracle_fields():
    bad = Scorer()
    bad.budget = None
    with pytest.raises(ValueError, match="budget"):
        run("jev", bad)
    with pytest.raises(ValueError, match="view"):
        asyncio.run(
            C["run_job"]({**VIEW, "reference_label": "TRUE"}, Runtime(), mode="native", seed=42)
        )


def test_bad_final_provenance_is_not_an_answer():
    runtime = Runtime()
    runtime.base.propose_frames = lambda *a, **k: Proposal(
        (Candidate((9, 10), "TRUE", 0.0, "eos", "fabricated"),), 2, 2, 3, 0.01
    )
    with pytest.raises(ValueError, match="provenance"):
        asyncio.run(C["run_job"](VIEW, runtime, mode="native", seed=42))


def test_cancelled_provider_has_no_late_commit():
    class Cancelled(Scorer):
        async def score(self, *a, **k):
            raise asyncio.CancelledError()

    record = {}
    with pytest.raises(asyncio.CancelledError):
        run("jev", Cancelled(), record)
    assert record["status"] == "cancelled" and record["accepted_ids"] == []


def test_constrained_final_uses_its_own_reserved_forward_budget():
    runtime = Runtime()

    def final(prompt, accepted, **kwargs):
        runtime.inspect(prompt, tuple(accepted) + (8,), allowed=(9,))
        return runtime.base.propose_frames(prompt, tuple(accepted) + (8,)), {
            "trace": [],
            "syntax": "all-three-labels",
        }

    runtime.propose_final = final
    result = asyncio.run(
        C["run_job"](
            VIEW,
            runtime,
            mode="staged",
            seed=42,
            limits={"reasoning_forwards": 1},
            final_grammar=True,
        )
    )
    assert result["reasoning_stop"] == "budget" and result["label"] == "TRUE"
    assert result["work"]["reasoning_forwards"] == 1 and result["work"]["final_forwards"] == 1
