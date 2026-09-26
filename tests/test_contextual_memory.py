import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load():
    return runpy.run_path(str(ROOT / "research/iterations/contextual_memory/memory.py"))


def test_token_alignment_imports_without_optional_inference_packages(monkeypatch):
    import builtins

    original = builtins.__import__

    def without_inference(name, *args, **kwargs):
        if name.split(".")[0] in {"torch", "transformers"}:
            raise ModuleNotFoundError(name)
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", without_inference)
    tok, case, row = fixture()
    assert load()["positions_for"](tok, case, row, eos=0)["slots"]


class ByteTokenizer:
    def decode(self, ids, **kwargs):
        return bytes(ids).decode("utf-8", errors="replace")

    def apply_chat_template(self, messages, **kwargs):
        return list((messages[0]["content"] + "\nANSWER:\n").encode())


def fixture(draft="1. café\n2. hall\n3. office"):
    tok = ByteTokenizer()
    questions = ["Where is key?", "Where is coin?", "Where is hat?"]
    case = dict(
        id="case", task="temporal", split="train", prompt="\n".join(questions), questions=questions
    )
    native = dict(
        prompt_token_ids=tok.apply_chat_template([dict(content=case["prompt"])]),
        generated_token_ids=list(draft.encode()) + [0],
        text=draft,
    )
    return tok, case, native


def test_positions_preserve_original_unicode_tokens_and_exclude_eos():
    m = load()
    tok, case, row = fixture()
    result = m["positions_for"](tok, case, row, eos=0)
    assert result["ids"] == row["prompt_token_ids"] + row["generated_token_ids"][:-1]
    for index, slot in enumerate(result["slots"]):
        text = tok.decode([result["ids"][i] for i in slot])
        assert text == case["questions"][index] + ("café", "hall", "office")[index]
    row["generated_token_ids"].pop()
    assert m["positions_for"](tok, case, row, eos=0) == result


def test_ambiguous_fields_use_question_only_and_invalid_provenance_is_rejected():
    m = load()
    tok, case, row = fixture("1. hall\n1. kitchen\n3. office")
    result = m["positions_for"](tok, case, row, eos=0)
    for i in (0, 1):
        assert tok.decode([result["ids"][p] for p in result["slots"][i]]) == case["questions"][i]
    with pytest.raises(ValueError, match="reference"):
        m["positions_for"](tok, case | {"references": ["hall"] * 3}, row, eos=0)
    with pytest.raises(ValueError, match="draft"):
        m["positions_for"](tok, case, row | {"text": "different"}, eos=0)
    with pytest.raises(ValueError, match="prompt"):
        m["positions_for"](tok, case, row | {"prompt_token_ids": [2]}, eos=0)
    repeated = case | {"prompt": case["prompt"] + "\n" + case["questions"][0]}
    with pytest.raises(ValueError, match="ambiguous"):
        row2 = row | {
            "prompt_token_ids": tok.apply_chat_template([dict(content=repeated["prompt"])])
        }
        m["positions_for"](tok, repeated, row2, eos=0)


def test_context_memory_uses_world_history_but_matched_embeddings_do_not():
    torch = pytest.importorskip("torch")
    m = load()
    model = runpy.run_path(str(ROOT / "tests/test_evidence_attention.py"))["tiny"]()
    slots = [[2], [3], [4]]
    before = {n: p.clone() for n, p in model.state_dict().items()}
    first = m["memories"](model, [1, 2, 3, 4, 5], slots, layer=1)
    changed = m["memories"](model, [8, 9, 3, 4, 5], slots, layer=1)
    assert torch.equal(first["embedding"], changed["embedding"])
    assert not torch.allclose(first["contextual"], changed["contextual"])
    for kind in ("embedding", "contextual"):
        assert first[kind].shape == (3, 16)
        assert not first[kind].requires_grad and torch.isfinite(first[kind]).all()
    assert first["processed_tokens"] == 5
    assert first["positions"] == slots
    assert all(torch.equal(p, before[n]) for n, p in model.state_dict().items())
    assert all(p.grad is None for p in model.parameters())
    assert not model.model.layers[1]._forward_hooks


def test_context_memory_rejects_invalid_state_and_cleans_up_after_exception():
    torch = pytest.importorskip("torch")
    m = load()
    model = runpy.run_path(str(ROOT / "tests/test_evidence_attention.py"))["tiny"]()
    slots = [[0], [1], [2]]
    for invalid in ([[0], [], [2]], [[0], [1], [3]], [[0], [1], [True]]):
        with pytest.raises(ValueError):
            m["memories"](model, [1, 2, 3], invalid, layer=1)
    model._jev_feedback_active = True
    with pytest.raises(RuntimeError, match="active"):
        m["memories"](model, [1, 2, 3], slots, layer=1)
    del model._jev_feedback_active
    next(model.parameters()).requires_grad_(True)
    with pytest.raises(ValueError, match="frozen"):
        m["memories"](model, [1, 2, 3], slots, layer=1)
    model.requires_grad_(False)
    original = model.forward

    def fail(*args, **kwargs):
        raise TimeoutError("fixture")

    model.forward = fail
    with pytest.raises(TimeoutError):
        m["memories"](model, [1, 2, 3], slots, layer=1)
    assert not model.model.layers[1]._forward_hooks
    assert not getattr(model, "_jev_feedback_active", False)
    model.forward = original
    assert torch.isfinite(m["memories"](model, [1, 2, 3], slots, layer=1)["contextual"]).all()
