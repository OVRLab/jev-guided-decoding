import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
HERE = ROOT / "research/iterations/benchmark_execution_v2"


def contract():
    return runpy.run_path(str(HERE / "contract.py"))


def test_terminal_detection_waits_for_a_complete_line_outside_thinking():
    end = contract()["terminal_line"]
    assert end("Reasoning\nFinal: C\n", "choice", False)
    assert not end("Final: C", "choice", False)
    assert not end("Final: C or D\n", "choice", False)
    assert not end("Final: C\n", "choice", True)
    assert end("Final: B\n</think>\nFinal: C\n", "choice", True)
    assert not end("#### 12", "number", False)
    assert not end("#### 12.", "number", False)
    assert end("#### 12.5\n", "number", False)
    assert not end("Write Final: C\n", "instruction", False)


def test_prompt_contract_preserves_instruction_content_and_keeps_truth_out():
    c = contract()
    assert c["task_prompt"]("Do exactly this.", "instruction") == "Do exactly this."
    text = c["task_prompt"]("Which color?\nA. red\nB. blue", "choice")
    assert "Which color?\nA. red\nB. blue" in text
    assert "Final:" in text
    with pytest.raises(ValueError):
        c["task_prompt"]("", "choice")
    with pytest.raises(ValueError):
        c["task_prompt"]("x", "unknown")


def test_case_seed_is_order_independent_and_repair_shares_randomness():
    seed = contract()["case_seed"]
    assert seed("example/1", 2701) == seed("example/1", 2701)
    assert seed("example/1", 2701) != seed("example/2", 2701)


def test_pilot_conversion_is_exposed_only_and_preserves_reference_binding():
    prepare = runpy.run_path(str(HERE / "prepare.py"))
    cases, refs = prepare["pilot_cases"]()
    assert len(cases) == len(refs) == 18
    assert all(c["split"] == "development" for c in cases)
    assert len({c["id"] for c in cases}) == 18
    for case, ref in zip(cases, refs, strict=True):
        assert ref["id"] == case["id"]
        assert ref["prompt_sha256"] == prepare["C"]["digest"](case["prompt"])
        assert "answer" not in case


def test_gpqa_shuffle_is_deterministic_with_separate_references():
    prepare = runpy.run_path(str(HERE / "prepare.py"))
    row = {
        "Question": "Which word is a color?",
        "Correct Answer": "blue",
        "Incorrect Answer 1": "desk",
        "Incorrect Answer 2": "cup",
        "Incorrect Answer 3": "shoe",
        "Subdomain": "synthetic",
    }
    c, r = prepare["gpqa_case"](row, 0)
    assert (c, r) == prepare["gpqa_case"](row, 0)
    assert r["options"][ord(r["answer"]) - 65] == "blue"
    assert c["split"] == "test" and c["format"] == "choice"
    assert "Correct Answer" not in c["prompt"] and "answer" not in c
    with pytest.raises(ValueError, match="options"):
        prepare["gpqa_case"](row | {"Incorrect Answer 1": "blue"}, 0)


def test_serial_runtime_stops_at_terminal_and_counts_real_work():
    pytest.importorskip("torch")
    r = runpy.run_path(str(HERE / "runtime.py"))
    tiny = runpy.run_path(str(ROOT / "tests/test_evidence_attention.py"))["tiny"]

    class Tok:
        pad_token_id = 0

        def decode(self, ids, skip_special_tokens=False):
            return "Final: A\n" if len(ids) >= 2 else "Final:"

    model = tiny()
    rows, work = r["generate_batch"](
        model,
        Tok(),
        [[1, 2, 3]],
        limit=4,
        eos=[100],
        seed=2701,
        kind="choice",
        thinking=False,
    )
    assert len(rows[0]["generated_token_ids"]) == 2
    assert rows[0]["finish_reason"] == "terminal_line"
    assert work["generated_token_slots"] == 2
    assert work["processed_token_slots"] == 4
    assert not model._forward_pre_hooks
    with pytest.raises(ValueError, match="serial"):
        r["generate_batch"](model, Tok(), [[1], [2]], limit=2, eos=[100], seed=2701)


def test_serial_runtime_zero_gate_and_exception_cleanup():
    pytest.importorskip("torch")
    r = runpy.run_path(str(HERE / "runtime.py"))
    tiny = runpy.run_path(str(ROOT / "tests/test_evidence_attention.py"))["tiny"]
    tok = runpy.run_path(str(ROOT / "tests/test_selective_benchmark_runtime.py"))["Tokenizer"]()
    model = tiny()
    branch = r["B"]["Repair"](16, 4)
    args = dict(limit=3, eos=[31], seed=2701)
    native, _ = r["generate_batch"](model, tok, [[1, 2]], **args)
    off, _ = r["generate_batch"](model, tok, [[1, 2]], adapter=branch, gate=0.0, layer=1, **args)
    assert off[0]["generated_token_ids"] == native[0]["generated_token_ids"]

    def expired():
        raise TimeoutError("expired")

    with pytest.raises(TimeoutError):
        r["generate_batch"](model, tok, [[1]], deadline=expired, **args)
    assert not model._forward_pre_hooks
    assert not model.model.layers[1]._forward_hooks
