"""A partial or incompatible evaluation cannot become a ten-task victory."""

import runpy
from pathlib import Path

import pytest

S = runpy.run_path(str(Path(__file__).resolve().parents[1] / "research/evaluation/scorecard.py"))


def records():
    return [
        dict(
            model=m,
            benchmark=b,
            score=60 + i,
            scope="full",
            status="complete",
            contract="c",
            dataset_revision="d",
            evaluator_revision="e",
            model_revision=m + "-weights",
        )
        for i, m in enumerate(("native", "guided"))
        for b in S["BENCHMARKS"]
    ]


def test_missing_task_prevents_aggregate_but_preserves_visible_scores():
    rows = records()[:-1]
    result = S["compose"](rows, ["native", "guided"])
    assert result["models"]["native"]["ten_task_mean"] == 60
    assert result["models"]["guided"]["ten_task_mean"] is None
    assert result["models"]["guided"]["missing"] == ["swe_bench_verified"]
    assert result["paired_mean_difference"] is None


def test_development_scores_cannot_fill_final_scorecard():
    rows = records()
    rows[0]["scope"] = "development"
    with pytest.raises(ValueError):
        S["compose"](rows, ["native", "guided"])


def test_mismatched_evaluator_or_duplicate_cannot_compare():
    rows = records()
    rows[-1]["evaluator_revision"] = "different"
    with pytest.raises(ValueError):
        S["compose"](rows, ["native", "guided"])
    with pytest.raises(ValueError):
        S["compose"](records() + records()[:1], ["native", "guided"])


def test_different_backbone_across_tasks_is_not_one_model():
    rows = records()
    rows[-1]["model_revision"] = "bigger-weights"
    with pytest.raises(ValueError):
        S["compose"](rows, ["native", "guided"])


def test_full_comparable_suite_uses_equal_benchmark_weights():
    result = S["compose"](records(), ["native", "guided"])
    assert result["paired_mean_difference"] == 1
    assert result["models"]["guided"]["direct_task_mean"] == 61
    assert result["models"]["guided"]["agent_task_mean"] == 61
    assert result["superiority_established"] is False
