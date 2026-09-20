import json
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]


def probe():
    return runpy.run_path(str(ROOT / "experiments/proposal_probe.py"))


def world(**overrides):
    return {
        "id": "test",
        "split": "development",
        "structure": "test",
        "atoms": {
            "a": "P has a badge",
            "b": "P has an escort",
            "g": "P may enter",
            "not_g": "P may not enter",
        },
        "facts": ["a"],
        "rules": [[["a", "b"], "g"]],
        "goal": "g",
        "opposite": "not_g",
    } | overrides


def test_oracle_needs_all_conjuncts_and_does_not_negate_missing_facts():
    oracle = probe()["oracle"]
    assert oracle(world()) == "UNKNOWN"
    assert oracle(world(facts=["a", "b"])) == "ENTAILED"
    assert oracle(world(rules=[[["a"], "not_g"]])) == "CONTRADICTED"


def test_unseeded_cycle_and_reverse_implication_cannot_prove_goal():
    oracle = probe()["oracle"]
    assert oracle(world(rules=[[["g"], "b"], [["b"], "g"]])) == "UNKNOWN"
    assert oracle(world(rules=[[["g"], "a"]])) == "UNKNOWN"


def test_inconsistent_world_is_rejected():
    with pytest.raises(ValueError, match="inconsistent"):
        probe()["oracle"](world(facts=["g", "not_g"]))


def test_render_does_not_leak_gold_labels_or_unrelated_metadata():
    case = probe()["render"](world(private_label="PRIVATE_REFERENCE_CANARY"))
    assert set(case) == {"id", "question", "evidence", "answers"}
    assert case["answers"] == ["UNKNOWN"]
    assert "PRIVATE_REFERENCE_CANARY" not in json.dumps(case)
    assert "P may not enter" not in case["evidence"]
    assert all(label in case["question"] for label in ("ENTAILED", "CONTRADICTED", "UNKNOWN"))


@pytest.mark.parametrize(
    "text,expected",
    [
        ("ENTAILED: the rule applies.", "ENTAILED"),
        ("unknown. Missing a premise.", "UNKNOWN"),
        ("CONTRADICTED\nAn explicit negative is proved.", "CONTRADICTED"),
        ("Not ENTAILED", None),
        ("The answer may be UNKNOWN", None),
        ("", None),
    ],
)
def test_verdict_parser_requires_the_declared_first_word(text, expected):
    assert probe()["verdict"](text) == expected


def test_fixture_splits_are_disjoint_and_all_worlds_are_consistent():
    module = probe()
    worlds = json.loads((ROOT / "experiments/proposal_worlds.json").read_text())
    assert len({w["id"] for w in worlds}) == len(worlds) == 10
    assert len([w for w in worlds if w["split"] == "development"]) == 4
    dev = {w["structure"] for w in worlds if w["split"] == "development"}
    held = {w["structure"] for w in worlds if w["split"] == "evaluation"}
    assert not dev & held
    assert {module["oracle"](w) for w in worlds} == {"ENTAILED", "CONTRADICTED", "UNKNOWN"}


def test_grading_keeps_missing_and_incomplete_runs_in_the_denominator():
    rows = [
        {
            "id": "test",
            "seed": 42,
            "result": {
                "mode": "jev",
                "phase": "stopped",
                "text": "UNKNOWN",
                "stop_reason": "time_budget",
            },
        }
    ]
    grade = probe()["grade_rows"](rows, [world()], [42, 43], ["jev"])
    assert grade["summary"]["jev"] == {
        "planned_runs": 2,
        "not_run": 1,
        "completed": 0,
        "recognized_verdicts": 0,
        "matching_verdicts": 0,
    }


def test_grading_rejects_duplicate_rows_and_checks_actual_verdict():
    row = {
        "id": "test",
        "seed": 42,
        "result": {
            "mode": "jev",
            "phase": "complete",
            "text": "ENTAILED",
            "stop_reason": "complete",
        },
    }
    grade = probe()["grade_rows"]([row], [world()], [42], ["jev"])
    assert grade["summary"]["jev"]["matching_verdicts"] == 0
    with pytest.raises(ValueError, match="duplicate"):
        probe()["grade_rows"]([row, row], [world()], [42], ["jev"])
