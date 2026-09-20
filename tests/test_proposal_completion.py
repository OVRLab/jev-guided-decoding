import runpy
from pathlib import Path

import pytest


def planner():
    return runpy.run_path(str(Path(__file__).parents[1] / "experiments/complete_proposal_jobs.py"))[
        "remaining_jobs"
    ]


def inputs():
    metadata = {"case_ids": ["a"], "seeds": [42, 43], "modes": ["greedy", "jev"]}
    cases = [{"id": "a", "question": "Q", "evidence": "E", "answers": ["UNKNOWN"]}]
    failed = {
        "id": "a",
        "seed": 42,
        "request": {"question": "Q", "evidence": "E"},
        "result": {"mode": "jev", "stop_reason": "scorer_error"},
    }
    return metadata, cases, failed


def test_failed_and_cancelled_attempts_are_never_scheduled_again():
    metadata, cases, failed = inputs()
    assert planner()(metadata, [failed], cases) == [
        ("a", 42, "greedy"),
        ("a", 43, "jev"),
        ("a", 43, "greedy"),
    ]
    failed["result"]["stop_reason"] = "cancelled"
    assert ("a", 42, "jev") not in planner()(metadata, [failed], cases)


def test_completion_refuses_duplicate_or_changed_previous_problems():
    metadata, cases, failed = inputs()
    with pytest.raises(ValueError, match="duplicate"):
        planner()(metadata, [failed, failed], cases)
    failed["request"]["evidence"] = "changed"
    with pytest.raises(ValueError, match="problem"):
        planner()(metadata, [failed], cases)
