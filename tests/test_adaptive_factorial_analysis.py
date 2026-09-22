import runpy
from pathlib import Path

import pytest

pytest.importorskip("numpy")

ROOT = Path(__file__).resolve().parents[1]


def module():
    return runpy.run_path(str(ROOT / "research/diagnostics/adaptive_factorial_analysis.py"))


def test_factor_effect_does_not_confuse_conditional_effect_with_average():
    # Strength helps only when neither of the other interventions is present.
    outcomes = {
        f"s{s}-h{h}-t{t}": [float(s == 1 and h == 0 and t == 0)] * 3
        for s in (0, 1)
        for h in (0, 1)
        for t in (0, 1)
    }
    effects = module()["effects"](outcomes)
    assert effects["averaged"]["strength"]["difference"] == 0.25
    assert effects["conditional"]["strength/h0/t0"]["difference"] == 1.0
    assert effects["conditional"]["strength/h1/t1"]["difference"] == 0.0
    assert effects["interactions"]["strength:head"]["difference"] == -0.5


def test_factor_effect_rejects_incomplete_world_pairing():
    outcomes = {f"s{s}-h{h}-t{t}": [0.0, 1.0] for s in (0, 1) for h in (0, 1) for t in (0, 1)}
    outcomes["s1-h1-t1"].pop()
    with pytest.raises(ValueError, match="paired"):
        module()["effects"](outcomes)
