import runpy
from pathlib import Path

import pytest

from jev_guided_decoding.types import Candidate, Proposal

CHECK = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "research/experiments/logit_mechanism.py")
)


def test_replay_binding_rejects_misaligned_or_failed_score_records():
    row = {
        "status": "complete",
        "evaluation": {"model": "jev-1.13.0"},
        "root_options": [[4, 0.6], [5, 0.3]],
        "candidates": [
            {"token_ids": [4, 6], "judgment": {"support": 0.7, "assessable": 1}},
            {"token_ids": [5, 6], "judgment": None},
        ],
    }
    assert CHECK["bound_judgments"](row)[4]["support"] == 0.7
    row["candidates"][0]["token_ids"][0] = 9
    with pytest.raises(ValueError, match="branch"):
        CHECK["bound_judgments"](row)
    row["status"] = "scorer_error"
    with pytest.raises(ValueError, match="successful"):
        CHECK["bound_judgments"](row)


def test_final_phase_keeps_exact_granite_tokens_and_uses_the_target_contract():
    class Base:
        def decode(self, ids):
            return {
                (1,): "<step>Mira is blue.</step>",
                (2, 3): "\n<final>TRUE</final>",
                (1, 2, 3): "<step>Mira is blue.</step>\n<final>TRUE</final>",
            }[ids]

        def encode(self, request):
            assert request.question == "Classify the target: Mira is blue."
            return (8, 9)

        def encode_control(self, text):
            assert text == "\n<final>"
            return (2,)

        def propose_frames(self, prompt, prefix, **kwargs):
            assert prompt == (8, 9) and prefix == (1, 2)
            assert kwargs["greedy"] and kwargs["count"] == 1
            return Proposal(
                (Candidate((3,), "TRUE</final>", -0.1, "frame", self.decode((1, 2, 3))),),
                1,
                1,
                4,
                0.1,
            )

    result = CHECK["finish"](
        Base(),
        {"target": "Mira is blue.", "evidence": "Mira is blue."},
        (1,),
        {"final_system": "Test", "final_tokens": 64},
        seed=42,
    )
    assert result["final_token_ids"] == (3,)
    assert result["retained_step_ids"] == (1,)
    assert result["final_frame_valid"]
