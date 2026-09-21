import copy
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
A = runpy.run_path(str(ROOT / "experiments/analyze_structured_study.py"))
F = runpy.run_path(str(ROOT / "tests/test_structured_controller.py"))


def test_reconstruction_accepts_original_and_rejects_changed_prefix_or_final():
    row = F["run"]("jev", F["Scorer"]())
    assert A["audit_tokens"](row, F["Base"]())
    for mutate in (
        lambda r: r["steps"][0]["trace"][0].update(prefix_digest="wrong"),
        lambda r: r["final"]["candidate"].update(token_ids=(4, 10)),
        lambda r: r["steps"][0]["checkpoint"]["branches"][0].update(body="Mira is calm."),
    ):
        bad = copy.deepcopy(row)
        mutate(bad)
        with pytest.raises(ValueError):
            A["audit_tokens"](bad, F["Base"]())


def test_final_token_loop_prefix_is_audited_separately():
    row = F["run"]("native")
    row["final"]["token_trace"] = {"trace": [{"token": 9, "prefix_digest": "wrong"}]}
    with pytest.raises(ValueError, match="Final trace"):
        A["audit_tokens"](row, F["Base"]())


def test_confusion_diagnostics_retain_invalid_outputs():
    a = F["run"]("native")
    a.update(reference_label="FALSE", depth=3, motif="negative")
    b = F["run"]("native")
    b.update(reference_label="UNKNOWN", label=None, depth=5, motif="missing")
    result = A["diagnostics"]([a, b])
    assert result["confusion"]["native"] == {"FALSE": {"TRUE": 1}, "UNKNOWN": {"INVALID": 1}}
    assert result["strata"]["native"]["depth:5"] == {"jobs": 1, "correct": 0}
