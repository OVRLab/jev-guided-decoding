import runpy
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def module():
    return runpy.run_path(str(ROOT / "research/diagnostics/gated_repair_feedback.py"))


def test_feedback_diagnostic_preserves_missing_and_threshold_ties():
    rows = [
        dict(id="e1", correct=False, parseable=True, probability=0.2),
        dict(id="e2", correct=False, parseable=True, probability=0.5),
        dict(id="c1", correct=True, parseable=True, probability=0.5),
        dict(id="c2", correct=True, parseable=True, probability=0.8),
        dict(id="e3", correct=False, parseable=False, probability=None),
    ]
    result = module()["summarize"](rows)
    assert result["cases"] == 5 and result["missing_feedback"] == 1
    assert result["available"] == 4
    assert result["errors_flagged"] == 1 and result["errors_missed"] == 1
    assert result["correct_flagged"] == 0 and result["correct_retained"] == 2
    assert result["error_detection_auroc"] == 0.875
    assert result["error_recall"] == 0.5


def test_feedback_diagnostic_has_no_auroc_with_one_class_or_no_observations():
    summarize = module()["summarize"]
    assert summarize([])["error_detection_auroc"] is None
    result = summarize([dict(id="c", correct=True, parseable=True, probability=0.1)])
    assert result["error_recall"] is None and result["correct_flagged"] == 1
    assert result["error_detection_auroc"] is None
    for probability in [True, -0.1, 1.1, float("nan"), "0.5"]:
        with pytest.raises(ValueError):
            summarize([dict(id="x", correct=True, parseable=True, probability=probability)])


def test_feedback_diagnostic_rejects_duplicate_rows():
    row = dict(id="same", correct=False, parseable=True, probability=0.2)
    with pytest.raises(ValueError):
        module()["summarize"]([row, row])


def test_feedback_diagnostic_rejects_tampered_frozen_cases(tmp_path):
    folder = tmp_path / "freeze"
    shutil.copytree(ROOT / "research/protocols/gated-repair-retry-v4", folder)
    with (folder / "cases.json").open("a") as stream:
        stream.write(" ")
    with pytest.raises(ValueError):
        module()["run"](folder, tmp_path / "output", tmp_path / "primary.json")
