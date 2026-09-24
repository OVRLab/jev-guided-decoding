import runpy
from pathlib import Path

import pytest

PATH = Path(__file__).parents[1] / "research/evaluation/full_short_tasks_v1.py"


def test_ifbench_keeps_exact_prompt_and_separates_constraints():
    m = runpy.run_path(str(PATH))
    row = dict(key=7, prompt="Only return red.\n", instruction_id_list=["synthetic"], kwargs=[{}])
    case, ref = m["ifbench_case"](row, {"ifbench/7"})
    assert case["prompt"] == row["prompt"]
    assert case["split"] == "development"
    assert "kwargs" not in case and ref["kwargs"] == [{}]


def test_related_stories_share_cluster_and_exposure_without_using_answers():
    m = runpy.run_path(str(PATH))
    opening = "One quiet morning in the same small town, three friends met to solve a mystery. " * 3
    rows = [{"narrative": opening + ending} for ending in ("one version", "another version")]
    rows.append({"narrative": "A completely unrelated short narrative."})
    groups = m["story_clusters"](rows, "family")
    assert groups[0] == groups[1] and groups[0] != groups[2]
    row = dict(
        narrative=rows[1]["narrative"],
        question="Who?",
        choices="['Ava', 'Ben']",
        answer_index="1",
        answer_choice="Ben",
    )
    case, ref = m["musr_case"](row, "murder_mystery", 1, groups[1], {groups[0]})
    assert case["split"] == "development" and ref["answer"] == "B"
    with pytest.raises(ValueError, match="answer"):
        m["musr_case"](row | {"answer_choice": "Ava"}, "murder_mystery", 1, groups[1], set())


def test_aime_numeric_contract_and_three_digit_value():
    m = runpy.run_path(str(PATH))
    case, ref = m["aime_case"](dict(id="synthetic", problem="Compute a number.", answer=7))
    assert ref["answer"] == "7" and case["format"] == "number"
    assert "####" in case["prompt"] and "answer" not in case
    with pytest.raises(ValueError):
        m["aime_case"](dict(id="bad", problem="Question", answer=1001))
