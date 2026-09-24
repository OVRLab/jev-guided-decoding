import runpy
from pathlib import Path

PATH = Path(__file__).parents[1] / "research/evaluation/choice_readout_v3.py"


def test_multiline_option_requires_the_complete_option_body():
    grade = runpy.run_path(str(PATH))["grade"]
    ref = dict(
        kind="choice",
        options=["first line\nwrong continuation", "first line\nright continuation"],
        answer="B",
    )
    assert not grade(ref, "B. first line\nFinal:")["parseable"]
    good = grade(ref, "B. first line\nright continuation\n\nFinal:")
    assert good["correct"] and good["answer"] == "B"
    assert not grade(ref, "B. first line\nwrong continuation")["parseable"]
    assert grade(ref | {"answer": "A"}, "B. first line\nright continuation")["answer"] == "B"


def test_multiline_options_do_not_allow_ambiguous_or_conflicting_responses():
    grade = runpy.run_path(str(PATH))["grade"]
    ref = dict(kind="choice", options=["red\nblue", "green\nyellow"], answer="B")
    assert not grade(ref, "A. red\nblue\nB. green\nyellow")["parseable"]
    assert not grade(ref, "B. green\nyellow\nFinal: A or B")["parseable"]
    assert grade(ref, "B. green\nyellow\nFinal: A")["answer"] == "A"
    assert grade(ref, "Final: B")["correct"]


def test_single_line_and_numeric_contracts_remain_identical_to_v2():
    v2 = runpy.run_path(str(PATH.with_name("choice_readout_v2.py")))["grade"]
    v3 = runpy.run_path(str(PATH))["grade"]
    ref = dict(kind="choice", options=["red", "green", "blue"], answer="C")
    for text in ("C. blue\nFinal:", "Final: A", "C. blue\nFinal: C or A", ""):
        assert v3(ref, text) == v2(ref, text)
    assert v3(dict(kind="number", answer="7"), "#### 007") == v2(
        dict(kind="number", answer="7"), "#### 007"
    )
