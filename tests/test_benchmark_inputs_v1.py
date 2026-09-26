import runpy
from pathlib import Path

import pytest

PATH = Path(__file__).parents[1] / "research/evaluation/benchmark_inputs_v1.py"


def test_gpqa_preserves_duplicate_distractors_with_unique_correct_text():
    m = runpy.run_path(str(PATH))
    row = {
        "Question": "Which is blue?",
        "Correct Answer": "sky",
        "Incorrect Answer 1": "red",
        "Incorrect Answer 2": "red",
        "Incorrect Answer 3": "green",
        "Subdomain": "synthetic",
    }
    case, ref = m["gpqa_case"](row, 0)
    assert len(ref["options"]) == 4 and ref["options"].count("red") == 2
    assert ref["options"][ord(ref["answer"]) - 65] == "sky"
    assert "Correct Answer" not in case["prompt"]
    assert case["split"] == "test"
    with pytest.raises(ValueError, match="ambiguous"):
        m["gpqa_case"](row | {"Incorrect Answer 1": "sky"}, 0)
    with pytest.raises(ValueError, match="blank"):
        m["gpqa_case"](row | {"Incorrect Answer 1": ""}, 0)
