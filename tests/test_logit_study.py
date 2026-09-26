import runpy
from pathlib import Path

import pytest

ANALYSIS = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "research/analysis/logit_study.py")
)


def test_opportunity_keeps_unassessed_and_absent_checkpoints_in_denominators():
    case = {
        "facts": ["Mira is blue."],
        "rules": [],
        "entities": ["Mira"],
        "properties": ["blue", "calm"],
    }
    rows = [
        {
            "id": "a",
            "case": case,
            "checkpoint": True,
            "candidates": [{"body": "Mira is blue."}, {"body": "Mira is calm."}, {"body": None}],
        },
        {"id": "b", "case": case, "checkpoint": False, "candidates": []},
    ]
    result = ANALYSIS["opportunity"](rows, planned=3)
    assert result["checkpoint_coverage"] == 1 / 3
    assert result["assessed_candidates"] == 2
    assert result["canonical_coverage"] == 2 / 3
    assert result["any_correct_and_incorrect"] == 1
    assert result["fully_assessed_mixed"] == 0
    assert result["missing_worlds"] == 1
    with pytest.raises(ValueError):
        ANALYSIS["opportunity"](rows + [rows[0]], planned=3)
