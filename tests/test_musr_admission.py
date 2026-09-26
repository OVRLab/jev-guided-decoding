import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_single_question_mechanical_admission_on_tiny_frozen_model():
    pytest.importorskip("torch")
    m = runpy.run_path(str(ROOT / "research/iterations/musr_transfer/admission.py"))
    model = runpy.run_path(str(ROOT / "tests/test_evidence_attention.py"))["tiny"]()
    result = m["admission"](model, [1, 2, 3, 4], [2, 3], [1, 2, 3, 4, 5, 6], layer=1, rank=4)
    assert result["passed"] and result["api_calls"] == 0
    assert result["initial_identity"] and result["off_identity"]
    assert result["cache_argmax_equal"] and result["cache_max_logit_error"] <= 0.001
    assert result["backbone_before"] == result["backbone_after"]
    assert result["memory_shape"] == [16]
    assert result["device"] == "cpu" and result["extraction_processed_tokens"] == 4
    assert all(not layer._forward_hooks for layer in model.model.layers)
