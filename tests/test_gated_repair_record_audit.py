import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_training_record_audit_rejects_test_data_wrong_gate_and_missing_step():
    a = runpy.run_path(str(ROOT / "research/diagnostics/gated_repair_records.py"))
    cases = [dict(id="train/1", split="train"), dict(id="test/1", split="test")]
    settings = dict(seeds=[7], epochs=1, accumulate=1)
    rows = [
        dict(mode=mode, seed=7, epoch=1, step=0, id="train/1", gate=gate, updates=1, loss=0.3)
        for mode, gate in [("constant", 0.5), ("live", 0.2)]
    ]
    assert a["audit_steps"](cases, rows, settings, {"train/1": 0.8})["steps"] == 2
    for bad in (
        rows[:-1],
        rows + rows[:1],
        [rows[0], rows[1] | {"id": "test/1"}],
        [rows[0], rows[1] | {"gate": 0.5}],
    ):
        with pytest.raises(ValueError):
            a["audit_steps"](cases, bad, settings, {"train/1": 0.8})
