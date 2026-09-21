import copy
import runpy
from pathlib import Path

import pytest

GATE = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "research/experiments/claim_gate.py")
)


def row(index, good_jev=True):
    return {
        "id": str(index),
        "status": "complete",
        "candidates": [
            {
                "mean_logprob": -0.1,
                "oracle": {"correct": False},
                "judgment": {"support": 0.1 if good_jev else 0.9, "assessable": 1},
            },
            {
                "mean_logprob": -0.2,
                "oracle": {"correct": True},
                "judgment": {"support": 0.9 if good_jev else 0.1, "assessable": 1},
            },
        ],
    }


def test_gate_needs_ranking_gain_and_independently_certified_acceptance():
    summary = GATE["analyze"]([row(i) for i in range(100)], planned=100)
    assert summary["admitted"] is True
    assert summary["mixed_batches"] == 100
    assert summary["ranking"]["jev_correct"] == 100
    assert summary["ranking"]["likelihood_correct"] == 0
    assert summary["ranking"]["difference_interval"][0] == 1


def test_no_improvement_or_missing_attempts_cannot_pass():
    bad = [row(i, False) for i in range(100)]
    assert GATE["analyze"](bad, planned=100)["admitted"] is False
    assert GATE["analyze"]([row(i) for i in range(99)], planned=100)["admitted"] is False


def test_unassessed_text_is_not_mislabeled_false_and_cannot_certify_acceptance():
    rows = [row(i) for i in range(100)]
    for r in rows:
        r["candidates"][1]["oracle"] = None
    summary = GATE["analyze"](rows, planned=100)
    assert summary["unassessed_candidates"] == 100
    assert summary["certified_false_candidates"] == 100
    assert summary["admitted"] is False


def test_duplicate_job_ids_fail_before_analysis():
    with pytest.raises(ValueError, match="duplicate"):
        GATE["analyze"]([row(1), copy.deepcopy(row(1))], planned=2)
