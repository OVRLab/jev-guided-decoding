import runpy
from pathlib import Path

import pytest

D = runpy.run_path(
    str(
        Path(__file__).resolve().parents[1] / "research/diagnostics/learned_feedback_descriptive.py"
    )
)


def test_pairs_bind_case_identity_and_separate_tokens_from_correctness():
    left = [
        dict(case_id="a", token_ids=[1], grade=dict(correct=True)),
        dict(case_id="b", token_ids=[2], grade=dict(correct=False)),
    ]
    right = [
        dict(case_id="b", token_ids=[3], grade=dict(correct=True)),
        dict(case_id="a", token_ids=[4], grade=dict(correct=True)),
    ]
    assert D["paired"](left, right) == dict(
        n=2, same_tokens=0, same_correctness=1, repairs=1, regressions=0
    )
    with pytest.raises(ValueError, match="coverage"):
        D["paired"](left, right[:1])
    with pytest.raises(ValueError, match="Duplicate"):
        D["paired"](left, [right[0], right[0]])


def test_unassessed_draft_is_not_a_false_claim():
    assert D["draft_kind"](None) == "unassessed"
    assert D["draft_kind"]({"supported": False}) == "unsupported"
    assert D["draft_kind"]({"supported": True}) == "supported"
