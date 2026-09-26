import copy
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
A = runpy.run_path(str(ROOT / "research/diagnostics/semantic_feedback_audit.py"))


def fixture():
    return {
        "model": "jev-1.13.0",
        "usage": {"input_tokens": 10, "output_tokens": 6},
        "answers": {
            f"{kind}_{i}": {"type": "noul", "noul": value}
            for i, value in enumerate((0.9, 0.1, 0.2))
            for kind in ("support", "assessable")
        },
    }


def test_raw_receipt_reconstruction_does_not_trust_normalized_scores():
    row = {
        "question_order": ["constructed_supported", "granite_draft", "constructed_unsupported"],
        "scores": [0.9, 0.2, 0.1],
        "completeness": [0.9, 0.2, 0.1],
        "jev": {
            "raw_response": fixture(),
            "model": "jev-1.13.0",
            "input_tokens": 10,
            "output_tokens": 6,
            "attempts": 1,
        },
    }
    assert A["receipt_check"](row) == (10, 6)
    bad = copy.deepcopy(row)
    bad["scores"][2] = 1.0
    with pytest.raises(ValueError, match="score"):
        A["receipt_check"](bad)
    bad = copy.deepcopy(row)
    bad["jev"]["raw_response"]["model"] = "different-model"
    with pytest.raises(ValueError, match="model"):
        A["receipt_check"](bad)


def test_audit_does_not_treat_whole_unsupported_prose_as_name():
    assert A["independent_entity"]("Mira", ["Mira", "Ravi"]) == "Mira"
    assert A["independent_entity"]("Mira or Ravi", ["Mira", "Ravi"]) is None
    assert A["independent_entity"]("Mira is not responsible.", ["Mira", "Ravi"]) is None
