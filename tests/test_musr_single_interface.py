import runpy
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1] / "research/iterations/musr_transfer"


def test_readout_never_guesses_or_uses_truth_and_keeps_last_field_ambiguity():
    parse = runpy.run_path(str(HERE / "single.py"))["parse_choice"]
    choices = ["Alice", "Bob", "Charlie"]
    for text, index in (
        ("ANSWER: 2", 1),
        ("ANSWER: (2)", 1),
        ("2", 1),
        ("ANSWER: 2 - Bob", 1),
        ("ANSWER: Bob", 1),
        ("Reasoning mentions 1 and 3.\nANSWER: 2", 1),
    ):
        result = parse(text, choices)
        assert result["index"] == index
        assert text[slice(*result["span"])].strip()
    for text in (
        "",
        "Maybe Alice or Bob",
        "ANSWER: 1 or 2",
        "ANSWER: 9",
        "ANSWER: 2 - Alice",
        "ANSWER: 2\nANSWER: 1 or 3",
        "ANSWER: 23",
    ):
        assert parse(text, choices)["index"] is None
    assert parse("reasoning ANSWER: 2", choices, thinking=True)["index"] is None
    assert parse("Thinking about 1.</think>\nANSWER: 2", choices, thinking=True)["index"] == 1
    assert parse("<think></think>ANSWER: 2", choices)["index"] == 1
    assert parse("<think>ANSWER: 2", choices)["index"] is None
    assert parse("<think>\nANSWER: 2", choices)["index"] is None
    assert parse("ANSWER: Alice", ["Alice", "alice"])["index"] is None
    repeated = ["cooking station", "dining tables", "pantry", "pantry ", "upper cabinet"]
    for answer, index in (("ANSWER: 3", 2), ("ANSWER: 4", 3), ("ANSWER: 4 - pantry", 3)):
        assert parse(answer, repeated)["index"] == index
    assert parse("ANSWER: pantry", repeated)["index"] is None


def test_single_question_memory_preserves_ids_and_excludes_reference_and_ambiguous_answer():
    s = runpy.run_path(str(HERE / "single.py"))

    class Tok:
        def encode(self, text, **kw):
            return list(text.encode())

        def decode(self, ids, **kw):
            return bytes(ids).decode(errors="replace")

        def apply_chat_template(self, messages, **kw):
            return list(("USER:\n" + messages[0]["content"] + "\nASSISTANT:\n").encode())

    case = dict(
        id="development/example",
        task="object_placements",
        split="development",
        context="Zoë moved the key; Bob did not see the move.",
        question="Where would Bob look?",
        choices=["hall", "office"],
    )
    tok = Tok()
    prompt = s["prompt_for"](case)
    assert prompt.count(case["question"]) == 1

    def native(text):
        return dict(
            prompt_token_ids=tok.apply_chat_template([dict(role="user", content=prompt)]),
            generated_token_ids=tok.encode(text) + [0],
            text=text,
        )

    draft = native("ANSWER: 2")
    aligned = s["positions_for"](tok, case, draft, eos=0)
    assert aligned["ids"] == draft["prompt_token_ids"] + draft["generated_token_ids"][:-1]
    assert len(aligned["positions"]) and aligned["positions"] == sorted(set(aligned["positions"]))
    assert any(i >= len(draft["prompt_token_ids"]) for i in aligned["positions"])
    ambiguous = native("ANSWER: 1 or 2")
    positions = s["positions_for"](tok, case, ambiguous, eos=0)["positions"]
    assert max(positions) < len(ambiguous["prompt_token_ids"])
    with pytest.raises(ValueError, match="reference|case"):
        s["positions_for"](tok, case | dict(reference=1), draft, eos=0)
    with pytest.raises(ValueError, match="token"):
        s["positions_for"](tok, case, draft | dict(prompt_token_ids=[255]), eos=0)


def test_repeated_internal_slots_equal_one_slot_for_nonzero_learned_branch():
    torch = pytest.importorskip("torch")
    s = runpy.run_path(str(HERE / "single.py"))
    Repair = runpy.run_path(str(HERE.parent / "structured_correction/bridge.py"))["Repair"]
    torch.manual_seed(321)
    adapter = Repair(8, 3)
    with torch.no_grad():
        adapter.up.weight.normal_(std=0.2)
    hidden = torch.randn(5, 8)
    vector = torch.randn(8)
    for probability in (0.1, 0.5, 0.9, 1.0):
        memory, values = s["as_three_slots"](vector, probability)
        assert memory.shape == (3, 8) and torch.equal(memory[0], memory[2])
        actual = adapter(hidden, memory, values)
        scale = hidden.square().mean(-1, keepdim=True).sqrt()
        normalized = vector / vector.square().mean().sqrt()
        query = adapter.down(hidden / scale)
        single_value = (1 - probability) * torch.tanh(adapter.value(normalized))
        expected = hidden + 0.5 * scale * torch.tanh(adapter.up(torch.tanh(query) * single_value))
        torch.testing.assert_close(actual, expected, atol=1e-6, rtol=1e-6)
        if probability == 1:
            assert torch.equal(actual, hidden)
    for bad in (float("nan"), -1, 2, True):
        with pytest.raises(ValueError):
            s["as_three_slots"](vector, bad)
    with pytest.raises(ValueError):
        s["as_three_slots"](vector.requires_grad_(True), 0.5)
