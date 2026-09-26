import runpy
from pathlib import Path

import pytest

P = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "research/iterations/public_critic.py")
)


def test_no_reference_fields_can_enter_request():
    c = {"id": "x", "task": "musr", "prompt": "A story", "response": "A. room"}
    payload = P["payload"](c)
    assert set(payload["state"]) == {"problem", "response"}
    assert "x" not in payload["state"].values()
    with pytest.raises(ValueError):
        P["payload"](dict(c, correct=True))


def test_error_signal_polarity_and_false_rejection():
    x = P["metrics"]([True, True, False, False], [0.9, 0.3, 0.8, 0.2])
    assert x["errors_detected"] == 1 and x["errors"] == 2
    assert x["correct_rejected"] == 1 and x["correct"] == 2
    assert x["error_recall"] == 0.5 and x["error_precision"] == 0.5
    assert x["auroc"] == 0.75


def test_ties_and_absent_class():
    assert P["metrics"]([True, False], [0.5, 0.5])["auroc"] == 0.5
    assert P["metrics"]([True], [0.9])["auroc"] is None
    with pytest.raises(ValueError):
        P["metrics"]([True], [float("nan")])


def fake_freeze(tmp_path, cap):
    import json

    f = tmp_path / "freeze"
    f.mkdir()
    (f / "inputs.json").write_text(
        json.dumps([{"id": "x", "task": "musr", "prompt": "Story", "response": "A. room"}])
    )
    (f / "manifest.json").write_text(
        json.dumps(
            {
                "sources": P["sources"](),
                "datasets": {"inputs.json": P["C"]["sha"](f / "inputs.json")},
                "max_usd": cap,
                "usd_per_million": 0.042,
            }
        )
    )
    return f


def test_unknown_provider_failure_stops_without_retry_or_settlement(tmp_path, monkeypatch):
    import asyncio
    import json

    from jev_guided_decoding.types import ScorerError

    calls = []

    class Fake:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def _evaluate(self, *args, **kwargs):
            calls.append(1)
            raise ScorerError("mock timeout", attempts=1, usage_unknown=True)

    g = P["execute"].__globals__
    monkeypatch.setitem(g, "JevScorer", Fake)
    monkeypatch.setitem(g, "load_api_key", lambda path: "fake-test-key")
    f = fake_freeze(tmp_path, 0.1)
    out = tmp_path / "run"
    with pytest.raises(ScorerError):
        asyncio.run(P["execute"](f, out))
    events = [json.loads(s)["event"] for s in (out / "budget.jsonl").read_text().splitlines()]
    assert calls == [1] and events == ["terms", "reserve"]
    assert json.loads((out / "000-failure.json").read_text())["usage_unknown"]
    with pytest.raises(FileExistsError):
        asyncio.run(P["execute"](f, out))
    assert calls == [1]


def test_budget_exhaustion_prevents_paid_attempt(tmp_path, monkeypatch):
    import asyncio

    from jev_guided_decoding.experiment_budget import BudgetExhausted

    calls = []

    class Fake:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def _evaluate(self, *args, **kwargs):
            calls.append(1)

    g = P["execute"].__globals__
    monkeypatch.setitem(g, "JevScorer", Fake)
    monkeypatch.setitem(g, "load_api_key", lambda path: "fake-test-key")
    with pytest.raises(BudgetExhausted):
        asyncio.run(P["execute"](fake_freeze(tmp_path, 0.0001), tmp_path / "run"))
    assert calls == []


def test_audit_rejects_duplicated_or_missing_receipt(tmp_path):
    import json
    import shutil

    freeze = tmp_path / "freeze"
    freeze.mkdir()
    output = tmp_path / "output"
    output.mkdir()
    cases = [
        {"id": f"x{i}", "task": "musr", "prompt": f"story {i}", "response": "A. room"}
        for i in range(2)
    ]
    labels = [
        {
            "id": c["id"],
            "correct": True,
            "input_sha256": P["C"]["digest_text"](json.dumps(c, sort_keys=True)),
        }
        for c in cases
    ]
    for n, v in [("inputs.json", cases), ("labels.json", labels)]:
        P["C"]["dump"](freeze / n, v)
    P["C"]["dump"](
        freeze / "manifest.json",
        {
            "protocol": "test",
            "usd_per_million": 0.042,
            "datasets": {n: P["C"]["sha"](freeze / n) for n in ("inputs.json", "labels.json")},
        },
    )
    events = []
    for i, c in enumerate(cases):
        reservation = f"r{i}"
        P["C"]["dump"](
            output / f"{i:03d}-request.json",
            {"id": c["id"], "payload": P["payload"](c), "reservation": reservation},
        )
        raw = {
            "model": P["MODEL"],
            "answers": {"correct": {"type": "noul", "noul": 0.8}},
            "usage": {"input_tokens": 10, "output_tokens": 20},
        }
        P["C"]["dump"](
            output / f"{i:03d}-response.json",
            {
                "id": c["id"],
                "reservation": reservation,
                "model": P["MODEL"],
                "attempts": 1,
                "probability_correct": 0.8,
                "input_tokens": 10,
                "output_tokens": 20,
                "seconds": 0.1,
                "raw": raw,
            },
        )
        events.extend(
            [
                {"event": "reserve", "id": reservation},
                {"event": "settle", "id": reservation, "input_tokens": 10},
            ]
        )
    (output / "budget.jsonl").write_text("\n".join(json.dumps(e) for e in events) + "\n")
    assert P["analyze"](freeze, output)["audited"]
    shutil.copyfile(output / "000-response.json", output / "001-response.json")
    with pytest.raises(ValueError):
        P["analyze"](freeze, output)
    (output / "001-response.json").unlink()
    with pytest.raises(FileNotFoundError):
        P["analyze"](freeze, output)
