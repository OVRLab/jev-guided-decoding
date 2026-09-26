"""A second interruption must not erase ancestry or extend the spending cap."""

import asyncio
import json
import runpy
from datetime import UTC, datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
V1 = runpy.run_path(str(ROOT / "tests/test_benchmark_recovery_v1.py"))
PATH = ROOT / "research/iterations/benchmark_recovery_v2/state.py"


def api():
    return runpy.run_path(str(PATH))


def admission():
    return dict(
        cap_usd=110,
        prior_closed_usd=47.39595151031136,
        settled_jev_usd=0.017775408,
        rate_usd_hour=1.8245808219178083,
        manifests=["abc"],
        stream_created_at=["2026-09-24T10:31:19.980682+00:00", "2026-09-24T10:39:49.578265+00:00"],
        worker_deadline="2026-09-25T02:00:00+00:00",
        cloud_deadline="2026-09-25T02:30:00+00:00",
    )


def resumed_parent(tmp_path):
    initial, row = V1["fixture"](tmp_path)
    parent = tmp_path / "first"
    V1["prepare"](initial, parent)
    return initial, parent, row


def prepare(parent, out, a=None):
    return api()["prepare"](
        parent,
        out,
        manifest_sha256="abc",
        admission=a or admission(),
        now=datetime(2026, 9, 24, 20, tzinfo=UTC),
    )


def test_two_recoveries_preserve_all_ancestors_and_reuse_tokens(tmp_path):
    initial, parent, row = resumed_parent(tmp_path)
    before = {p.name: p.read_bytes() for p in parent.iterdir()}
    second = tmp_path / "second"
    state = prepare(parent, second)
    assert state.cached("model", "native", "one", [1, 2], None) == row
    assert before == {p.name: p.read_bytes() for p in parent.iterdir()}
    assert api()["verify_chain"]([initial, parent, second])["interrupted_jobs"] == 1
    third = tmp_path / "third"
    prepare(second, third)
    assert api()["verify_chain"]([initial, parent, second, third])["continuations"] == 3
    (parent / "outputs.jsonl").write_text("")
    with pytest.raises(ValueError):
        api()["verify_chain"]([initial, parent, second, third])


@pytest.mark.parametrize(
    "change",
    [
        {"cap_usd": 111},
        {"prior_closed_usd": float("nan")},
        {"rate_usd_hour": 0},
        {"cloud_deadline": "2026-09-25T05:30:00+00:00"},
        {"worker_deadline": "2026-09-24T19:00:00+00:00"},
        {"manifests": ["different"]},
        {"stream_created_at": []},
    ],
)
def test_invalid_budget_or_binding_refused_before_copy(tmp_path, change):
    _, parent, _ = resumed_parent(tmp_path)
    with pytest.raises(ValueError):
        prepare(parent, tmp_path / "second", admission() | change)
    assert not (tmp_path / "second").exists()


def test_completed_parent_refused_and_parent_recovery_metadata_retained(tmp_path):
    _, parent, _ = resumed_parent(tmp_path)
    (parent / "completion.json").write_text("{}")
    with pytest.raises(ValueError, match="complete"):
        prepare(parent, tmp_path / "second")
    (parent / "completion.json").unlink()
    out = tmp_path / "second"
    prepare(parent, out)
    assert (out / "recovery.json").read_bytes() == (parent / "recovery.json").read_bytes()
    assert api()["verify_chain"]([tmp_path / "parent", parent, out])["additional_jev_requests"] == 0


def test_reload_record_does_not_overwrite_previous_reload(tmp_path):
    _, parent, _ = resumed_parent(tmp_path)
    h = {"gpu": "L40S", "original_weights_sha256": "ok", "at": "old", "load_seconds": 1}
    (parent / "model-hardware.json").write_text(json.dumps(h))
    (parent / "recovery-model-hardware.json").write_text(json.dumps(h))
    out = tmp_path / "second"
    state = prepare(parent, out)
    state.hardware("model", h | {"at": "new", "load_seconds": 3})
    assert (out / "recovery-model-hardware.json").read_bytes() == (
        parent / "recovery-model-hardware.json"
    ).read_bytes()
    with pytest.raises(ValueError):
        state.hardware("model", h | {"original_weights_sha256": "changed"})


def test_runner_adapter_preserves_old_envelopes_and_rejects_changed_admission(
    tmp_path, monkeypatch
):
    from functools import partial

    initial, parent, _ = resumed_parent(tmp_path)
    old_sources = {"original": "hash"}
    (parent / "recovery-sources.json").write_text(json.dumps(old_sources))
    (parent / "recovery-cache-admission.json").write_text("{}")
    path = tmp_path / "admission.json"
    path.write_text(json.dumps(admission()))
    module = runpy.run_path(str(PATH.parent / "run.py"))
    call = module["run"]
    glob = call.__globals__
    glob["ADMISSION"], glob["ADMISSION_SHA256"] = path, api()["sha"](path)
    # The file inventory remains rooted at the real source tree in this offline fixture.
    glob["ROOT"] = tmp_path
    glob["HERE"] = tmp_path / "source"
    glob["HERE"].mkdir()
    for name in ("run.py", "state.py", "handoff.py"):
        (glob["HERE"] / name).write_text("test source")
    (tmp_path / "research").mkdir()
    (tmp_path / "research/benchmark-interruption-recovery-v2.md").write_text("test protocol")
    glob["STATE"]["prepare"] = partial(api()["prepare"], now=datetime(2026, 9, 24, 20, tzinfo=UTC))
    invocations = []

    async def fake_run(folder, prior, out):
        state_api = fake_run.__globals__["S"]
        state = state_api["prepare"](prior, out, manifest_sha256="abc", max_seconds=39600)
        assert state.end == datetime(2026, 9, 25, 2, tzinfo=UTC)
        state_api["dump"](out / "recovery-sources.json", {"frozen": "hash"})
        state_api["dump"](out / "recovery-cache-admission.json", {"new": True})
        invocations.append(True)

    monkeypatch.setattr(runpy, "run_path", lambda _: {"S": {}, "run": fake_run})
    out = tmp_path / "second"
    asyncio.run(call(tmp_path / "freeze", [initial, parent], out))
    assert json.loads((out / "recovery-sources.json").read_text()) == old_sources
    assert (out / "recovery-cache-admission.json").read_text() == "{}"
    assert json.loads((out / "recovery-chain-2-cache-admission.json").read_text()) == {"new": True}
    assert (
        glob["STATE"]["lines"](out / "recovery-chain-sources.jsonl")[0]["files"]["frozen"] == "hash"
    )
    path.write_text("changed")
    with pytest.raises(ValueError, match="admission file changed"):
        asyncio.run(call(tmp_path / "freeze", [initial, parent], tmp_path / "third"))
    assert invocations == [True]
