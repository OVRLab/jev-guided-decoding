import runpy
from pathlib import Path

import pytest

P = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "research/iterations/public_critic.py")
)


def test_no_reference_fields_can_enter_request():
    c = {"id": "x", "task": "musr", "prompt": "A story", "response": "A. room"}
    payload = P["payload"](c)
    assert set(payload["state"]) == {"problem", "response"}
    assert "x" not in payload["state"].values()
    with pytest.raises(ValueError):
        P["payload"](dict(c, correct=True))


def test_error_signal_polarity_and_false_rejection():
    x = P["metrics"]([True, True, False, False], [0.9, 0.3, 0.8, 0.2])
    assert x["errors_detected"] == 1 and x["errors"] == 2
    assert x["correct_rejected"] == 1 and x["correct"] == 2
    assert x["error_recall"] == 0.5 and x["error_precision"] == 0.5
    assert x["auroc"] == 0.75


def test_ties_and_absent_class():
    assert P["metrics"]([True, False], [0.5, 0.5])["auroc"] == 0.5
    assert P["metrics"]([True], [0.9])["auroc"] is None
    with pytest.raises(ValueError):
        P["metrics"]([True], [float("nan")])
