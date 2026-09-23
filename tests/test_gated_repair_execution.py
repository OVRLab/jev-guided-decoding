import asyncio
import runpy
from pathlib import Path

import pytest

from jev_guided_decoding.experiment_budget import InputTokenBudget

ROOT = Path(__file__).resolve().parents[1]


def test_reference_never_enters_feedback_and_unknown_charge_is_retained(tmp_path):
    c = runpy.run_path(str(ROOT / "research/iterations/gated_repair/common.py"))
    s = runpy.run_path(str(ROOT / "research/iterations/gated_repair/study.py"))
    case = dict(id="x", task="gsm8k", split="train", prompt="Question?", origin="train/1")

    class Scorer:
        async def _evaluate(self, body, parse, **kwargs):
            assert set(body["state"]) == {"problem", "response"}
            assert kwargs["max_attempts"] == 1
            raise TimeoutError("not a receipt")

    with InputTokenBudget(tmp_path / "budget.jsonl", max_usd=0.01, usd_per_million=0.042) as budget:
        with pytest.raises(TimeoutError):
            asyncio.run(s["request_feedback"](case, "draft", Scorer(), budget, tmp_path))
        assert len(budget.unresolved) == 1 and budget.charged_tokens == 65536
    assert len((tmp_path / "api-requests.jsonl").read_text().splitlines()) == 1
    assert not (tmp_path / "api-responses.jsonl").exists()
    with pytest.raises(ValueError):
        c["feedback_payload"](case | {"target": "secret-reference"}, "draft")


def test_training_targets_and_selection_do_not_accept_leaked_test_case(tmp_path):
    s = runpy.run_path(str(ROOT / "research/iterations/gated_repair/study.py"))
    with pytest.raises(ValueError):
        s["training_target"](dict(id="test/x", split="test"), {"test/x": "42"})
    with pytest.raises(ValueError):
        s["training_target"](dict(id="train/x", split="train"), {})


def test_offline_audit_rejects_missing_artifacts(tmp_path):
    a = runpy.run_path(str(ROOT / "research/iterations/gated_repair/analyze.py"))
    with pytest.raises((ValueError, FileNotFoundError)):
        a["analyze"](tmp_path, tmp_path)


def test_full_precision_revision_preserves_runtime_and_uses_strict_admission():
    pytest.importorskip("torch")
    import inspect

    v2 = runpy.run_path(str(ROOT / "research/iterations/gated_repair_fp32/runtime.py"))
    original = runpy.run_path(str(ROOT / "research/iterations/gated_repair/runtime.py"))
    assert inspect.getsource(v2["generate"]) == inspect.getsource(original["generate"])
    assert inspect.getsource(v2["loss_for"]) == inspect.getsource(original["loss_for"])
    assert v2["ADMISSION_ATOL"] == 1e-4 and v2["ADMISSION_RTOL"] == 1e-4
    c = runpy.run_path(str(ROOT / "research/iterations/gated_repair_fp32/common.py"))
    paths = c["sources"]()
    assert "research/gated-repair-fp32-amendment.md" in paths
    assert "research/iterations/gated_repair/study.py" in paths


def test_float32_fixture_compares_actual_greedy_cached_token_without_mutating_model():
    torch = pytest.importorskip("torch")
    r = runpy.run_path(str(ROOT / "research/iterations/gated_repair_fp32/runtime.py"))
    model = runpy.run_path(str(ROOT / "tests/test_evidence_attention.py"))["tiny"]()
    adapter = r["B"]["Repair"](16, 4)
    with torch.no_grad():
        adapter.up.weight.normal_(std=0.01)
    before = r["weight_digest"](model)
    result = r["comparison"](model, [1, 2, 3], adapter, layer=1)
    assert result["allclose"] and result["argmax_equal"]
    assert r["weight_digest"](model) == before
    assert not model.model.layers[1]._forward_hooks
