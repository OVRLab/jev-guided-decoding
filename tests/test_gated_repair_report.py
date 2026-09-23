import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    cases = [dict(id="a", task="gsm8k"), dict(id="b", task="arc")]
    rows, grades = [], []
    answers = {"native": [True, False], "live/1": [False, True], "live/2": [True, True]}
    for arm, values in answers.items():
        for case, correct in zip(cases, values, strict=True):
            rows.append(
                dict(
                    id=case["id"],
                    arm=arm,
                    generated_token_ids=[int(correct)],
                    seconds=2,
                    processed_tokens=5,
                    finish_reason="eos",
                )
            )
            grades.append(dict(id=case["id"], arm=arm, correct=correct, parseable=True))
    return cases, rows, grades


def test_recovery_damage_pair_seeds_within_case_and_keep_missing_native():
    mod = runpy.run_path(str(ROOT / "research/diagnostics/gated_repair_report.py"))
    cases, rows, grades = fixture()
    result = mod["summarize"](cases, rows, grades, {"a": None, "b": 0.1}, ["live/1", "live/2"])
    assert result["cases"] == 2
    assert result["correct"] == 1.5
    assert result["recovered"] == 1
    assert result["damaged"] == 0.5
    assert result["accuracy"] == 0.75
    assert result["actual_repair_generation_seconds_seed_mean"] == 4
    retained = mod["summarize"](
        cases, rows, grades, {"a": None, "b": 0.1}, ["live/1", "live/2"], retain=True
    )
    assert retained["correct"] == 2
    assert retained["damaged"] == 0
    assert retained["repair_cases"] == 1
    assert retained["missing_feedback_cases"] == 1
    assert retained["actual_repair_generation_seconds_seed_mean"] == 4
    assert retained["measured_execution_savings"] is False


def test_report_rejects_incomplete_or_duplicate_component_coverage():
    mod = runpy.run_path(str(ROOT / "research/diagnostics/gated_repair_report.py"))
    cases, rows, grades = fixture()
    for invalid in (rows[:-1], rows + [rows[0]]):
        with pytest.raises(ValueError):
            mod["summarize"](cases, invalid, grades, {"a": 0.9, "b": 0.1}, ["live/1", "live/2"])
    with pytest.raises(ValueError):
        mod["summarize"](cases, rows, grades, {"a": 0.9}, ["live/1", "live/2"])
