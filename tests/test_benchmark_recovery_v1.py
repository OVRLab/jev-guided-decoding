"""Recovery must preserve durable results and refuse ambiguous attempts."""

import json
import runpy
from datetime import UTC, datetime
from pathlib import Path

import pytest

MODULE = Path(__file__).resolve().parents[1] / "research/iterations/benchmark_recovery_v1/state.py"


def api():
    return runpy.run_path(str(MODULE))


def write(path, rows):
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))


def fixture(tmp_path):
    parent = tmp_path / "parent"
    parent.mkdir()
    (parent / "start.json").write_text(
        json.dumps({"at": "2026-09-24T10:00:00+00:00", "manifest_sha256": "abc"})
    )
    start = dict(event="start", batch_id="done", model="model", arm="native", ids=["one"], at="a")
    row = dict(
        batch_id="done",
        model="model",
        arm="native",
        id="one",
        generated_token_ids=[4, 5],
        prompt_token_ids=[1, 2],
        gate=None,
    )
    write(
        parent / "jobs.jsonl",
        [
            start,
            start | {"event": "finish", "at": "b"},
            start | {"batch_id": "lost", "ids": ["two"], "at": "c"},
        ],
    )
    write(parent / "batches.jsonl", [dict(batch_id="done", model="model", arm="native")])
    write(parent / "outputs.jsonl", [row])
    write(parent / "decisions.jsonl", [])
    return parent, row


def prepare(parent, output):
    return api()["prepare"](
        parent,
        output,
        manifest_sha256="abc",
        max_seconds=39600,
        now=datetime(2026, 9, 24, 14, tzinfo=UTC),
    )


def test_preserves_parent_and_reuses_tokens_without_generation(tmp_path):
    parent, row = fixture(tmp_path)
    before = {p.name: p.read_bytes() for p in parent.iterdir()}
    output = tmp_path / "continuation"
    state = prepare(parent, output)
    assert state.cached("model", "native", "one", [1, 2], None) == row
    assert state.cached("model", "native", "two", [1, 2], None) is None
    assert before == {p.name: p.read_bytes() for p in parent.iterdir()}
    assert (
        json.loads((output / "recovery.json").read_text())["interrupted_jobs"][0]["batch_id"]
        == "lost"
    )
    assert len((output / "jobs.jsonl").read_text().splitlines()) == 2
    assert (output / "outputs.jsonl").read_bytes() == before["outputs.jsonl"]
    with pytest.raises(ValueError, match="prefix|gate"):
        state.cached("model", "native", "one", [1, 9], None)
    with pytest.raises(FileExistsError):
        prepare(parent, output)


@pytest.mark.parametrize(
    "kind",
    [
        "duplicate",
        "partial_output",
        "batch_without_output",
        "finished_without_output",
        "multiple_interrupted",
    ],
)
def test_refuses_ambiguous_or_corrupt_records(tmp_path, kind):
    parent, row = fixture(tmp_path)
    if kind == "duplicate":
        with (parent / "outputs.jsonl").open("a") as f:
            f.write(json.dumps(row) + "\n")
    elif kind == "partial_output":
        with (parent / "outputs.jsonl").open("a") as f:
            f.write('{"unfinished":')
    elif kind == "batch_without_output":
        with (parent / "batches.jsonl").open("a") as f:
            f.write(json.dumps(dict(batch_id="lost", model="model", arm="native")) + "\n")
    else:
        with (parent / "jobs.jsonl").open("a") as f:
            f.write(
                json.dumps(
                    dict(
                        event="finish" if kind == "finished_without_output" else "start",
                        batch_id="lost" if kind == "finished_without_output" else "another",
                        model="model",
                        arm="native",
                        ids=["two"],
                        at="d",
                    )
                )
                + "\n"
            )
    with pytest.raises(ValueError):
        prepare(parent, tmp_path / "continuation")
    assert not (tmp_path / "continuation").exists()


def test_refuses_changed_manifest_and_expired_deadline(tmp_path):
    parent, _ = fixture(tmp_path)
    for binding, time in [("wrong", 14), ("abc", 22)]:
        with pytest.raises(ValueError):
            api()["prepare"](
                parent,
                tmp_path / "out",
                manifest_sha256=binding,
                max_seconds=39600,
                now=datetime(2026, 9, 24, time, tzinfo=UTC),
            )
    assert not (tmp_path / "out").exists()


def test_decision_reuse_rejects_changed_selection(tmp_path):
    parent, _ = fixture(tmp_path)
    decision = dict(
        id="one", arm="live", selected_arm="native", selected_tokens_sha256="xyz", at="old"
    )
    write(parent / "decisions.jsonl", [decision])
    out = tmp_path / "out"
    state = prepare(parent, out)
    state.decision(decision | {"at": "new"})
    assert (out / "decisions.jsonl").read_bytes() == (parent / "decisions.jsonl").read_bytes()
    with pytest.raises(ValueError, match="decision"):
        state.decision(decision | {"selected_arm": "live"})


def test_hardware_reuse_refuses_changed_weights_and_tracks_reload(tmp_path):
    parent, _ = fixture(tmp_path)
    hardware = dict(
        profile={"dtype": "float32"},
        original_weights_sha256="abc",
        files={"model": "x"},
        gpu="L40S",
        at="old",
        load_seconds=1,
    )
    (parent / "model-hardware.json").write_text(json.dumps(hardware))
    state = prepare(parent, tmp_path / "out")
    with pytest.raises(ValueError, match="hardware|weight"):
        state.hardware("model", hardware | {"original_weights_sha256": "bad"})
    state.hardware("model", hardware | {"at": "new", "load_seconds": 4})
    assert json.loads((state.output / "model-hardware.json").read_text()) == hardware
    assert (state.output / "recovery-model-hardware.json").exists()


def test_derived_audit_detects_parent_tampering_and_lost_durable_outputs(tmp_path):
    parent, _ = fixture(tmp_path)
    out = tmp_path / "out"
    prepare(parent, out)
    assert api()["verify_lineage"](parent, out)["interrupted_jobs"] == 1
    original = (out / "outputs.jsonl").read_bytes()
    (out / "outputs.jsonl").write_text("")
    with pytest.raises(ValueError, match="preserved"):
        api()["verify_lineage"](parent, out)
    (out / "outputs.jsonl").write_bytes(original)
    with (parent / "outputs.jsonl").open("a") as f:
        f.write("{}\n")
    with pytest.raises(ValueError, match="parent"):
        api()["verify_lineage"](parent, out)
