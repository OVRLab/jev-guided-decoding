import runpy
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")
ROOT = Path(__file__).resolve().parents[1]
M = runpy.run_path(str(ROOT / "research/iterations/learned_feedback/bridge.py"))


def tiny():
    model = runpy.run_path(str(ROOT / "tests/test_evidence_attention.py"))["tiny"]()
    return model, M["Bridge"](16, rank=4), torch.tensor([[1, 2, 3, 4]])


def test_zero_bridge_is_identical_and_nonzero_changes_only_allowed_positions():
    model, adapter, x = tiny()
    native = model(x, use_cache=False).logits
    with M["scope"](model, adapter, [0.9, 1.0], start=3, layer=1):
        zero = model(x, use_cache=False).logits
    assert torch.equal(native, zero)
    with torch.no_grad():
        adapter.up.weight.fill_(0.1)
    with M["scope"](model, adapter, [0.9, 1.0], start=3, layer=1):
        changed = model(x, use_cache=False).logits
    assert torch.equal(native[:, :3], changed[:, :3])
    assert not torch.equal(native[:, 3:], changed[:, 3:])


def test_only_new_parameters_receive_gradients_and_scope_cleans_up():
    model, adapter, x = tiny()
    with M["scope"](model, adapter, [0.1, 0.9], start=3, layer=1):
        model(x, use_cache=False).logits[0, -1, 5].backward()
        with pytest.raises(RuntimeError, match="active"):
            with M["scope"](model, adapter, [0.1, 0.9], start=3, layer=1):
                pass
    assert adapter.up.weight.grad.abs().sum() > 0
    assert all(p.grad is None and not p.requires_grad for p in model.parameters())
    with pytest.raises(RuntimeError, match="intentional"):
        with M["scope"](model, adapter, [0.1, 0.9], start=3, layer=1):
            raise RuntimeError("intentional")
    assert not model.model.layers[1]._forward_hooks
    for bad in ([float("nan"), 1], [-1, 1], [1], [True, 1]):
        with pytest.raises(ValueError):
            with M["scope"](model, adapter, bad, start=3, layer=1):
                pass


def test_nonzero_bridge_cached_step_matches_full_prefix():
    model, adapter, x = tiny()
    with torch.no_grad():
        adapter.up.weight.normal_(std=0.1)
    cache = M["new_cache"](model)
    assert cache.get_seq_length() == 0
    with torch.no_grad(), M["scope"](model, adapter, [0.1, 0.9], start=2, layer=1):
        full = model(x, use_cache=False).logits[:, -1]
        first = model(x[:, :3], use_cache=True, past_key_values=cache)
        last = model(x[:, 3:], use_cache=True, past_key_values=first.past_key_values).logits[:, -1]
    torch.testing.assert_close(full, last, atol=1e-6, rtol=1e-5)


def test_final_phase_preserves_exact_draft_and_rejects_incomplete_answer_credit():
    r = runpy.run_path(str(ROOT / "research/iterations/learned_feedback/runtime.py"))

    class Tokenizer:
        def encode(self, text, add_special_tokens=False):
            return [7, 8]

        def convert_tokens_to_ids(self, token):
            return 9

    prefix, draft = [1, 2], [4, 5, 9]
    result = r["final_prefix"](Tokenizer(), prefix, draft, "Which color?")
    assert result["ids"][:5] == prefix + draft
    assert result["ids"][5:] == result["framing_ids"]
    for text in ("[E02]", "not red", "red or blue", "The color is"):
        assert not r["grade"]("red", text)["correct"]
    assert r["grade"]("red", " Red.\n")["correct"]
