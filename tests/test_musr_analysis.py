import runpy
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1] / "research/iterations/musr_transfer"


def test_reference_grading_distinguishes_index_accuracy_from_duplicate_text_sensitivity():
    g = runpy.run_path(str(HERE / "analysis.py"))["grade"]
    choices = ["hall", "pantry", "pantry "]
    actual = g("ANSWER: 3", choices, 1)
    assert actual["correct"] is False and actual["equivalent_choice"] is True
    assert actual["ambiguous_options"] and actual["parsed_index"] == 2
    assert not g("ANSWER: pantry", choices, 1)["correct"]
    assert not g("ANSWER: pantry", choices, 1)["equivalent_choice"]
    assert g("ANSWER: 2", choices, 1)["correct"]
    assert not g("<think>\nANSWER: 2", choices, 1, thinking=True)["correct"]
    assert g("<think></think>ANSWER: 2", choices, 1)["correct"]
    for invalid in (True, -1, 3, "1"):
        with pytest.raises(ValueError):
            g("ANSWER: 2", choices, invalid)


def test_grouped_paired_uncertainty_does_not_treat_repeated_story_questions_as_independent():
    effect = runpy.run_path(str(HERE / "analysis.py"))["effect"]
    cases = [
        dict(id=f"case/{i}", task="murder_mystery" if i < 2 else "team_allocation")
        for i in range(4)
    ]
    groups = {c["id"]: c["id"] for c in cases}
    differences = {c["id"]: v for c, v in zip(cases, [1, 0, -1, 1], strict=True)}
    first = effect(cases, groups, differences, draws=1000)
    assert first["delta_pp"] == 25 and first["groups"] == 4
    expanded, larger_groups, larger_differences = [], {}, {}
    for c in cases:
        for j in range(4):
            ident = c["id"] + f"/{j}"
            expanded.append(c | dict(id=ident))
            larger_groups[ident] = groups[c["id"]]
            larger_differences[ident] = differences[c["id"]]
    second = effect(expanded, larger_groups, larger_differences, draws=1000)
    assert second["n"] == 16 and second["groups"] == 4
    assert first["ci95_pp"] == second["ci95_pp"]
    assert first["family_ci_pp"] == second["family_ci_pp"]
    assert second["family_ci_pp"][0] <= second["ci95_pp"][0]
    with pytest.raises(ValueError):
        effect(cases, groups, differences | {"extra": 0}, draws=1000)
    with pytest.raises(ValueError):
        effect(cases, groups, differences | {"case/0": float("nan")}, draws=1000)
    with pytest.raises(ValueError, match="famil"):
        effect(cases, groups | {"case/2": "case/0"}, differences, draws=1000)
