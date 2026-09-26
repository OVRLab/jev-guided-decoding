import asyncio
import runpy
from pathlib import Path
from types import SimpleNamespace

import pytest

HERE = Path(__file__).resolve().parents[1] / "research/iterations/contextual_memory"


def test_execution_rejects_existing_attempt_before_loading_model_or_key(tmp_path, monkeypatch):
    pytest.importorskip("torch")
    s = runpy.run_path(str(HERE / "study.py"))
    namespace = s["execute"].__globals__
    monkeypatch.setitem(namespace["FROZEN"], "verify", lambda _: {})
    output = tmp_path / "attempt"
    output.mkdir()
    (output / "partial.json").write_text("preserve")
    args = SimpleNamespace(
        input=tmp_path, output=output, device="cpu", key_file=tmp_path / "absent"
    )
    with pytest.raises(FileExistsError):
        asyncio.run(s["execute"](args))
    assert (output / "partial.json").read_text() == "preserve"


def test_execution_writes_failure_evidence_without_retrying_model_load(tmp_path, monkeypatch):
    pytest.importorskip("torch")
    s = runpy.run_path(str(HERE / "study.py"))
    namespace = s["execute"].__globals__
    monkeypatch.setitem(namespace["FROZEN"], "verify", lambda _: {})
    monkeypatch.setitem(namespace["FROZEN"], "sources", lambda: {})
    calls = []

    def fail(device):
        calls.append(device)
        raise RuntimeError("fixture loading failure")

    monkeypatch.setitem(namespace["OLD"], "load_model", fail)
    for name in ("manifest.json", "cases.json", "references.json", "admission-input.json"):
        (tmp_path / name).write_text("{}")
    args = SimpleNamespace(
        input=tmp_path, output=tmp_path / "attempt", device="cpu", key_file=tmp_path / "missing"
    )
    with pytest.raises(RuntimeError, match="fixture loading failure"):
        asyncio.run(s["execute"](args))
    assert calls == ["cpu"]
    assert (args.output / "failed.json").exists()
    assert not (args.output / "complete.json").exists()
