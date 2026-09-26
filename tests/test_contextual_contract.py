import runpy
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1] / "research/iterations/contextual_memory"


def test_full_factorial_requires_every_case_and_control():
    c = runpy.run_path(str(HERE / "common.py"))
    cases = [
        dict(id=str(i), split=split) for i, split in enumerate(("train", "development", "test"))
    ]
    contract = dict(informative="both", seeds=[3101, 3102], epochs=2)
    expected = c["expected_outputs"](cases, contract)
    assert len(expected) == 1 + 25 + 38
    rows = [dict(id=i, arm=a) for i, a in expected]
    c["coverage"](cases, rows, contract)
    with pytest.raises(ValueError, match="coverage"):
        c["coverage"](cases, rows[:-1], contract)
    with pytest.raises(ValueError, match="coverage"):
        c["coverage"](cases, rows + [rows[0]], contract)
    with pytest.raises(ValueError, match="coverage"):
        c["coverage"](cases + [cases[0]], rows, contract)
    assert "donor/contextual-structured/3101" in c["test_arms"](contract)
    assert "donor/contextual-scalar/3101" in c["test_arms"](contract)


def test_paired_interaction_and_primary_family_are_case_based():
    effect = runpy.run_path(str(HERE / "common.py"))["effect"]
    cases = [dict(id=str(i), task="temporal" if i % 2 else "compositional") for i in range(4)]
    # Identical paired advantage in both families; repeated seeds do not double n.
    values = {str(i): 0.5 for i in range(4)}
    result = effect(cases, values, draws=100)
    assert result["n"] == 4 and result["delta_pp"] == 50
    assert result["ci95_pp"] == result["family_ci_pp"] == [50, 50]
    assert result["family_confidence"] == 0.9875
    assert effect(cases, {i: -v for i, v in values.items()}, draws=100)["delta_pp"] == -50
    with pytest.raises(ValueError):
        effect(cases, {"0": 0.5}, draws=100)
    with pytest.raises(ValueError):
        effect(cases, {i: float("nan") for i in values}, draws=100)


def test_summary_preserves_primary_family_and_reports_memory_feedback_interaction():
    a = runpy.run_path(str(HERE / "audit.py"))
    m = dict(informative="both", seeds=[3101, 3102], epochs=2)
    cases = [
        dict(id=str(i), task="temporal" if i % 2 else "compositional", split="test")
        for i in range(4)
    ]
    rows = []
    for case in cases:
        for arm in a["N"]["test_arms"](m):
            base = arm.rsplit("/", 1)[0] if "/" in arm else arm
            passes = {
                "native": {"0"},
                "contextual-structured": {"0", "1"},
                "embedding-structured": {"0", "1"},
                "contextual-scalar": {"1"},
                "embedding-scalar": {"0"},
                "donor/contextual-structured": {"1"},
            }
            correct = case["id"] in passes.get(base, set())
            rows.append(
                dict(
                    id=case["id"],
                    task=case["task"],
                    arm=arm,
                    correct=correct,
                    slots=[correct] * 3,
                    format=True,
                    finish_reason="eos",
                )
            )
    result = a["summarize"](cases, rows, m, draws=100)
    assert result["scores"]["contextual-structured"]["accuracy"] == 0.5
    primary = {k: v for k, v in result["contrasts"].items() if v["primary"]}
    assert len(primary) == 4
    assert primary["contextual-scalar-minus-native"]["delta_pp"] == 0
    assert primary["contextual-structured-minus-contextual-scalar"]["delta_pp"] == 25
    memory = result["contrasts"]["contextual-structured-minus-embedding-structured"]
    assert memory["delta_pp"] == 0 and memory["primary"] is False
    assert result["memory_feedback_interaction"]["delta_pp"] == 0
    assert result["preservation"]["contextual-structured/3101"] == dict(fixed=1, damaged=0)
