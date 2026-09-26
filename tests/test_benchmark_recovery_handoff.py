"""A waiting controller must neither duplicate nor conceal unfinished work."""

import runpy
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

MODULE = (
    Path(__file__).resolve().parents[1] / "research/iterations/benchmark_recovery_v2/handoff.py"
)


def setup(tmp_path):
    api = runpy.run_path(str(MODULE))
    parent, output = tmp_path / "parent", tmp_path / "output"
    parent.mkdir()
    start = datetime(2026, 9, 24, 20, tzinfo=UTC)
    clock = [start]
    calls = []

    def pause():
        clock[0] += timedelta(seconds=45)

    def invoke():
        calls.append("inference")
        output.mkdir()
        (output / "completion.json").write_text("{}")
        return 0

    kwargs = dict(
        parent=parent,
        output=output,
        deadline=start + timedelta(hours=1),
        state=lambda: "inactive",
        pause=pause,
        invoke=invoke,
        now=lambda: clock[0],
    )
    return api["manage"], kwargs, calls


def test_active_parent_finishes_without_new_inference(tmp_path):
    manage, kw, calls = setup(tmp_path)
    states = iter(["active", "deactivating", "inactive"])

    def state():
        value = next(states)
        if value == "inactive":
            (kw["parent"] / "completion.json").write_text("{}")
        return value

    kw["state"] = state
    assert manage(**kw) == (kw["parent"], 0)
    assert not calls and not kw["output"].exists()


def test_incomplete_parent_resumes_once(tmp_path):
    manage, kw, calls = setup(tmp_path)
    assert manage(**kw) == (kw["output"], 0)
    assert calls == ["inference"]
    with pytest.raises(FileExistsError):
        manage(**kw)
    assert calls == ["inference"]


def test_no_run_from_unknown_service_or_after_deadline(tmp_path):
    manage, kw, calls = setup(tmp_path)
    kw["state"] = lambda: "unknown"
    with pytest.raises(RuntimeError):
        manage(**kw)
    kw["state"] = lambda: "active"
    with pytest.raises(TimeoutError):
        manage(**kw)
    assert not calls


def test_worker_failure_and_missing_completion_are_not_success(tmp_path):
    manage, kw, calls = setup(tmp_path)
    kw["invoke"] = lambda: 17
    assert manage(**kw) == (kw["output"], 17)
    kw["invoke"] = lambda: 0
    with pytest.raises(RuntimeError):
        manage(**kw)
