import runpy
from pathlib import Path

import pytest

PATH = Path(__file__).parents[1] / "research/evaluation/choice_readout_v2.py"


def grade(ref, text):
    return runpy.run_path(str(PATH))["grade"](ref, text)


def test_recognizes_an_explicit_complete_option_before_an_empty_wrapper():
    ref = dict(kind="choice", options=["cell wall", "cytoplasm", "a nucleus"], answer="C")
    row = grade(ref, "C. a nucleus\n\nFinal:")
    assert row == dict(answer="C", parseable=True, correct=True, method="full_option")
    assert not grade(ref | {"answer": "B"}, "C. a nucleus\n\nFinal:")["correct"]


def test_never_picks_an_answer_from_ambiguous_options_or_a_conflicting_final():
    ref = dict(kind="choice", options=["red", "green", "blue"], answer="C")
    for text in [
        "A. red\nC. blue",
        "C. something else",
        "C. blue\nFinal: A or C",
        "C. blue\nFinal: Z",
    ]:
        assert not grade(ref, text)["parseable"]
    assert grade(ref, "C. blue\nFinal: A")["answer"] == "A"


def test_existing_explicit_answers_stay_unchanged_and_bad_references_fail():
    ref = dict(kind="choice", options=["red", "green", "blue"], answer="C")
    assert grade(ref, "Final: C") == dict(answer="C", parseable=True, correct=True, method="v1")
    with pytest.raises(ValueError, match="reference"):
        grade(ref | {"answer": None}, "")
