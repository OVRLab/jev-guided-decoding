import runpy
from pathlib import Path

import pytest

PATH = Path(__file__).parents[1] / "research/iterations/selective_benchmarks/common.py"


def module():
    return runpy.run_path(str(PATH))


def test_retention_preserves_native_without_running_repair():
    calls = []
    native = {"generated_token_ids": [8, 9], "text": "Final: B"}
    for probability in (None, 0.5, 1.0):
        row = module()["select"](native, probability, lambda gate: calls.append(gate))
        assert row["output"] is native
        assert row["decision"] == "retain_native"
        assert not row["repair_executed"]
    assert calls == []


def test_low_probability_executes_bound_repair_once():
    calls = []

    def repair(gate):
        calls.append(gate)
        return {"generated_token_ids": [4, 9], "text": "Final: D"}

    row = module()["select"]({"text": "Final: B"}, 0.02, repair)
    assert calls == [0.98]
    assert row["decision"] == "repair"
    assert row["repair_executed"]
    assert row["output"]["text"] == "Final: D"


@pytest.mark.parametrize("value", [True, -0.1, 1.1, float("nan"), "0.2"])
def test_invalid_probability_does_not_dispatch(value):
    with pytest.raises(ValueError, match="probability"):
        module()["select"]({}, value, lambda _: pytest.fail("dispatched"))


def test_task_specific_repair_preserves_exact_draft_tokens():
    class Tokenizer:
        def convert_tokens_to_ids(self, value):
            assert value == "<|end_of_text|>"
            return 999

        def encode(self, text, add_special_tokens):
            assert not add_special_tokens
            self.suffix = text
            return [len(text), 777]

    tok = Tokenizer()
    prompt, draft = [1, 2], [4, 5, 999]
    ids = module()["repair_prefix"](tok, prompt, draft, "choice")
    assert ids[:5] == [1, 2, 4, 5, 999]
    assert "####" not in tok.suffix
    assert "<letter>" not in tok.suffix
    assert "Final:" in tok.suffix
    assert prompt == [1, 2] and draft == [4, 5, 999]
    module()["repair_prefix"](tok, prompt, [4, 5], "number")
    assert "Final:" not in tok.suffix and "<numeric" not in tok.suffix
    assert "####" in tok.suffix


def test_choice_readout_does_not_randomly_credit_missing_answers():
    grade = module()["grade"]
    ref = {"kind": "choice", "answer": "C", "options": ["red", "green", "blue"]}
    for text in ("", "I cannot determine it.", "Final: Z", "A and C are possible"):
        result = grade(ref, text)
        assert not result["correct"] and not result["parseable"]
    for text in ("Final: C", "The answer is (C).", "**Answer: C**", "blue"):
        assert grade(ref, text)["correct"]


def test_numeric_readout_accepts_final_marker_and_rejects_placeholder():
    grade = module()["grade"]
    ref = {"kind": "number", "answer": "36"}
    for text in ("The total is #### 36", "#### 36", r"Answer: \boxed{36}"):
        assert grade(ref, text)["correct"]
    for text in ("#### <numeric answer>", "I used 36 apples and 12 pears.", "#### 37"):
        assert not grade(ref, text)["correct"]


def test_schema_rejects_reference_leakage():
    case = {
        "id": "fixture/1",
        "task": "math",
        "family": "math",
        "prompt": "2 + 2?",
        "format": "number",
        "origin_id": "1",
        "cluster": "1",
        "split": "test",
    }
    module()["validate_case"](case)
    with pytest.raises(ValueError, match="case"):
        module()["validate_case"](case | {"answer": "4"})
