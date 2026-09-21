import runpy
from pathlib import Path

import pytest


def test_descriptive_metrics_count_fixes_regressions_and_false_relevance():
    module = runpy.run_path(
        str(Path(__file__).resolve().parents[1] / "research/analysis/evidence_metrics.py")
    )
    cases = {
        "a": {"missing": False, "reference": "red", "oracle_scores": [1, 0]},
        "b": {"missing": True, "reference": "UNKNOWN", "oracle_scores": [0, 0]},
    }
    rows = [
        {"id": "a", "mode": "native", "status": "complete", "label": "blue"},
        {"id": "a", "mode": "jev", "status": "complete", "label": "red"},
        {"id": "b", "mode": "native", "status": "complete", "label": "UNKNOWN"},
        {"id": "b", "mode": "jev", "status": "complete", "label": "red"},
    ]
    scores = [
        {
            "id": "a",
            "status": "complete",
            "evaluation": {
                "scores": [0.9, 0.6],
                "seconds": 0.1,
                "input_tokens": 20,
                "output_tokens": 3,
            },
        },
        {
            "id": "b",
            "status": "complete",
            "evaluation": {
                "scores": [0.5, 0.1],
                "seconds": 0.2,
                "input_tokens": 30,
                "output_tokens": 3,
            },
        },
    ]
    result = module["describe"](rows, scores, cases)
    assert result["jev_native_fixes"] == result["jev_native_regressions"] == 1
    assert result["span_confusion"] == {"tp": 1, "fp": 1, "tn": 2, "fn": 0}
    assert result["brier"] == pytest.approx((0.01 + 0.36 + 0.25 + 0.01) / 4)
    assert result["constant_unknown_accuracy"] == 0.5
    assert result["test_api_usage"]["input_tokens"] == 50
    with pytest.raises(ValueError, match="Incomplete"):
        module["describe"]([{**rows[0], "status": "failed"}], scores, cases)
