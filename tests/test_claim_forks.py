import runpy
from pathlib import Path
from types import SimpleNamespace

import pytest

FORKS = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "research/experiments/claim_forks.py")
)


@pytest.mark.parametrize(
    "text",
    [
        "Mira is",
        "Mira is not",
        "It is established that Mira is",
        "It is not established that Mira is",
    ],
)
def test_predicate_checkpoint_uses_an_existing_model_generated_prefix(text):
    assert FORKS["predicate_boundary"](text, ["Mira"])


@pytest.mark.parametrize(
    "text", ["It is", "Mira", "Mira is blue.", "Other is", "Mira is blue. Mira is"]
)
def test_checkpoint_does_not_accept_partial_subject_or_another_claim(text):
    assert not FORKS["predicate_boundary"](text, ["Mira"])


def test_extended_parser_handles_established_prefix_but_not_extra_claims():
    case = {
        "facts": ["Mira is blue."],
        "rules": [],
        "entities": ["Mira"],
        "properties": ["blue", "calm"],
    }
    assert FORKS["grade_claim"](case, "It is established that Mira is blue.")["correct"] is True
    assert FORKS["grade_claim"](case, "It is established that Mira is calm.")["correct"] is False
    assert FORKS["grade_claim"](case, "It is not established that Mira is calm.")["correct"] is True
    assert FORKS["grade_claim"](case, "It is established that Mira is blue. Mira is calm.") is None


def test_gate_requires_checkpoint_coverage_in_addition_to_critic_metrics():
    rows = [
        {"id": str(i), "status": "complete", "checkpoint": False, "candidates": []}
        for i in range(100)
    ]
    result = FORKS["analyze"](rows, planned=100)
    assert result["checkpoint_coverage"] == 0
    assert result["gates"]["checkpoint_coverage"] is False
    assert result["admitted"] is False


def test_interrupted_branch_retains_work_and_prefix_provenance():
    class Base:
        eos_ids = {99}

        def encode(self, request):
            return (1,)

        def encode_control(self, text):
            return (2,)

        def decode(self, ids):
            return {(): "", (3,): "Mira is", (2, 3): "<step>Mira is"}.get(
                ids, "<step>Mira is blue.</step>"
            )

    class Runtime:
        def inspect(self, *args, **kwargs):
            return SimpleNamespace(
                prefix_digest="digest", prefill_tokens=3, seconds=0.1, options=((4, 0.6), (5, 0.4))
            )

        def sample(self, *args, **kwargs):
            return 3, 1.0, 1.0

        def lookahead(self, *args, first_token, **kwargs):
            if first_token == 5:
                raise TimeoutError("Second branch failed")
            return {
                "token_ids": (4, 6),
                "finish_reason": "frame",
                "generated_tokens": 1,
                "decode_token_slots": 1,
                "prefill_tokens": 4,
                "seconds": 0.1,
                "rest_mean_logprob": -0.2,
                "forced_tokens": 1,
            }

    record = {}
    with pytest.raises(TimeoutError):
        FORKS["propose"](
            {"entities": ["Mira"]},
            None,
            Base(),
            Runtime(),
            {
                "prefix_tokens": 4,
                "seconds_per_world": 90,
                "candidates": 2,
                "chunk_tokens": 4,
                "seconds_per_lookahead": 15,
            },
            1,
            record=record,
        )
    assert record["checkpoint"]
    assert record["prefix_token_ids"] == (2, 3)
    assert len(record["prefix_trace"]) == 2
    assert record["proposals"][0]["generated_tokens"] == 1
    assert len(record["candidates"]) == 1
