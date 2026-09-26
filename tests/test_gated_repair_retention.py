import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_retention_routes_without_reference_or_quality_information():
    r = runpy.run_path(str(ROOT / "research/diagnostics/gated_repair_retention.py"))
    assert r["route"](0.5) == "native"
    assert r["route"](0.95) == "native"
    assert r["route"](0.49) == "repair"
    for value in [True, None, -0.1, 1.1, float("nan")]:
        with pytest.raises(ValueError):
            r["route"](value)
    rows = [
        dict(id="wrong", arm="native", correct=False),
        dict(id="wrong", arm="live", correct=True),
        dict(id="correct", arm="native", correct=True),
        dict(id="correct", arm="live", correct=False),
    ]
    selected = r["replay"](rows, {"wrong": 0.9, "correct": 0.1}, "live")
    assert selected == [
        dict(id="correct", arm="retained_live", correct=False),
        dict(id="wrong", arm="retained_live", correct=False),
    ]
    with pytest.raises(ValueError):
        r["replay"](rows[:-1], {"wrong": 0.9, "correct": 0.1}, "live")
