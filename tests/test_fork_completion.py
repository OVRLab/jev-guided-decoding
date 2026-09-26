import runpy
from pathlib import Path

import pytest

COMPLETION = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "research/experiments/fork_completion.py")
)


def test_completion_never_replays_a_completed_or_failed_attempt():
    cases = [{"id": str(i)} for i in range(4)]
    rows = [{"id": "0", "status": "complete"}, {"id": "1", "status": "scorer_error"}]
    assert COMPLETION["remaining_cases"](cases, rows) == cases[2:]
    with pytest.raises(ValueError):
        COMPLETION["remaining_cases"](cases, rows + [rows[0]])
    with pytest.raises(ValueError):
        COMPLETION["remaining_cases"](cases, [{"id": "extra"}])
