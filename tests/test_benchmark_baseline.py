"""Behavioral checks for a public baseline without inference dependencies."""

import importlib.util
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[1] / "research/iterations/benchmark_baseline/common.py"
spec = importlib.util.spec_from_file_location("baseline_common", PATH)
C = importlib.util.module_from_spec(spec)
spec.loader.exec_module(C)


def test_final_readout_ignores_reasoning_and_rejects_incomplete():
    assert C.final_text("<think>Final: A</think>Final: B", thinking=True) == (
        "Final: B",
        "complete",
    )
    assert C.final_text("<think>Final: A", thinking=True) == ("", "unfinished_thinking")
    assert C.final_text("analysis Final: A", thinking=True) == ("", "unfinished_thinking")
    assert C.final_text("Final: C", thinking=False) == ("Final: C", "complete")


def test_grader_requires_final_decision_and_numeric_equality():
    assert C.grade({"kind": "choice", "answer": "B", "choices": 3}, "Reasoning A. Final: B")[
        "correct"
    ]
    assert not C.grade({"kind": "choice", "answer": "B", "choices": 3}, "Maybe B or C")["parseable"]
    assert not C.grade({"kind": "choice", "answer": "B", "choices": 3}, "Final: B or C")[
        "parseable"
    ]
    assert not C.grade({"kind": "choice", "answer": "B", "choices": 3}, "Final: Z")["parseable"]
    assert C.grade({"kind": "number", "answer": "1200"}, "#### 1,200.0")["correct"]
    assert not C.grade({"kind": "number", "answer": "12"}, "At first I thought 12 but no.")[
        "parseable"
    ]
    assert not C.grade({"kind": "number", "answer": "12"}, "#### NaN")["parseable"]


def test_model_input_has_no_oracle_and_binding_rejects_changed_question():
    c = {"id": "x", "task": "mmlu", "family": "law", "prompt": "Choose one", "origin_id": "1"}
    C.validate_case(c)
    with pytest.raises(ValueError):
        C.validate_case(dict(c, answer="B"))
    r = {"id": "x", "prompt_sha256": C.digest_text(c["prompt"]), "correct": True}
    C.bind(c, r)
    with pytest.raises(ValueError):
        C.bind(dict(c, prompt="Choose two"), r)


def test_absent_outputs_stay_in_denominator_and_duplicate_outputs_fail():
    cases = [{"id": "a", "task": "t"}, {"id": "b", "task": "t"}]
    rows = [{"id": "a", "task": "t", "correct": True, "status": "complete"}]
    summary = C.summarize(cases, rows)
    assert summary["t"]["planned"] == 2
    assert summary["t"]["correct"] == 1
    assert summary["t"]["accuracy"] == 0.5
    assert summary["t"]["missing"] == 1
    with pytest.raises(ValueError):
        C.summarize(cases, rows + rows)


def test_exact_eos_boundary():
    assert C.trim_ids([2, 9, 0, 0], {9}) == ([2, 9], "eos")
    assert C.trim_ids([2, 3], {9}) == ([2, 3], "length")


def test_manifest_tampering_is_rejected(tmp_path):
    p = tmp_path / "data.json"
    p.write_text("[]")
    C.verify_files(tmp_path, {"data.json": C.sha(p)})
    p.write_text("[1]")
    with pytest.raises(ValueError):
        C.verify_files(tmp_path, {"data.json": "bad"})
    with pytest.raises(ValueError):
        C.verify_files(tmp_path, {"../outside": "bad"})


def test_output_binding_rejects_rewritten_final_text():
    case = {"id": "x", "prompt": "question"}
    row = {
        "id": "x",
        "prompt_sha256": C.digest_text("question"),
        "raw": "</think>Final: B",
        "final": "Final: A",
        "status": "complete",
    }
    with pytest.raises(ValueError):
        C.verify_readout(case, row, thinking=True)
    row["final"] = "Final: B"
    C.verify_readout(case, row, thinking=True)
