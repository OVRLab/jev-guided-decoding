import copy
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
A = runpy.run_path(str(ROOT / "research/diagnostics/learned_feedback_audit.py"))


def test_raw_feedback_reconstruction_rejects_changed_signal_or_usage():
    order = ["granite_draft", "constructed_supported", "constructed_unsupported"]
    probabilities = [0.2, 0.9, 0.1]
    row = {
        "question_order": order,
        "feedback": {k: [p, 1.0] for k, p in zip(order, probabilities, strict=True)},
        "jev": {
            "model": "jev-1.13.0",
            "attempts": 1,
            "input_tokens": 50,
            "output_tokens": 10,
            "raw_response": {
                "model": "jev-1.13.0",
                "usage": {"input_tokens": 50, "output_tokens": 10},
                "answers": {
                    **{
                        f"support_{i}": {"type": "noul", "noul": p}
                        for i, p in enumerate(probabilities)
                    },
                    **{f"assessable_{i}": {"type": "noul", "noul": 1.0} for i in range(3)},
                },
            },
        },
    }
    assert A["receipt_check"](row) == (50, 10)
    bad = copy.deepcopy(row)
    bad["feedback"]["granite_draft"][0] = 1.0
    with pytest.raises(ValueError, match="feedback"):
        A["receipt_check"](bad)
    bad = copy.deepcopy(row)
    bad["jev"]["input_tokens"] = 0
    with pytest.raises(ValueError, match="usage"):
        A["receipt_check"](bad)


def test_reconstruction_checks_actual_forward_and_allowed_positions():
    row = {
        "token_ids": [5, 2],
        "forwards": 2,
        "processed_tokens": 5,
        "prefill_tokens": 4,
        "finish_reason": "eos",
        "adapter_events": [
            {"layer": 19, "positions": [3], "relative_delta": 0.02, "feedback": [0.2, 1.0]},
            {"layer": 19, "positions": [4], "relative_delta": 0.02, "feedback": [0.2, 1.0]},
        ],
    }
    A["work_check"](row, 4, {2}, [0.2, 1.0], True)
    bad = copy.deepcopy(row)
    bad["adapter_events"][0]["positions"] = [2]
    with pytest.raises(ValueError, match="position"):
        A["work_check"](bad, 4, {2}, [0.2, 1.0], True)
