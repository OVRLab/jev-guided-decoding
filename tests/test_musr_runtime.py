import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "research/iterations/musr_transfer"


def runtime():
    return runpy.run_path(str(HERE / "runtime.py"))


def tiny():
    pytest.importorskip("torch")
    return runpy.run_path(str(ROOT / "tests/test_evidence_attention.py"))["tiny"]()


class Tok:
    def decode(self, ids, **kwargs):
        return ",".join(map(str, ids))

    def encode(self, text, **kwargs):
        self.encoded = text
        return [7, 8]

    def convert_tokens_to_ids(self, token):
        return 31


def test_extended_generation_limit_exact_cache_tokens_and_private_sampling_rng():
    torch = pytest.importorskip("torch")
    r, model, tok = runtime(), tiny(), Tok()
    with torch.no_grad():
        model.lm_head.weight.zero_()
    result = r["generate"](model, tok, [1, 2], limit=129, eos=[31], context_limit=256)
    assert result["generated_token_ids"] == [0] * 129
    assert result["processed_tokens"] == 130 and result["finish_reason"] == "length"
    assert result["prompt_token_ids"] == [1, 2] and not result["events"]
    settings = dict(
        limit=8, eos=[31], context_limit=256, sampling=dict(seed=45, temperature=1.0, top_p=0.95)
    )
    before = torch.get_rng_state().clone()
    first = r["generate"](model, tok, [1, 2], **settings)
    second = r["generate"](model, tok, [1, 2], **settings)
    assert first["generated_token_ids"] == second["generated_token_ids"]
    assert torch.equal(before, torch.get_rng_state())
    with pytest.raises(ValueError, match="limit|context"):
        r["generate"](model, tok, [1, 2], limit=256, eos=[31], context_limit=256)
    for ids in ([True], [-1], [32], []):
        with pytest.raises(ValueError):
            r["generate"](model, tok, ids, limit=5, eos=[31])


def test_intervention_owns_exact_final_prefix_positions_and_cleans_on_deadline():
    torch = pytest.importorskip("torch")
    r, model, tok = runtime(), tiny(), Tok()
    adapter = r["B"]["Repair"](16, 4).eval()
    memory = torch.randn(3, 16)
    ids = [1, 2, 3]
    kwargs = dict(limit=4, eos=[31], layer=1, context_limit=256)
    native = r["generate"](model, tok, ids, **kwargs)
    for probability in (0.3, 1.0):
        modified = r["generate"](
            model,
            tok,
            ids,
            adapter=adapter,
            memory=memory,
            probabilities=[probability] * 3,
            **kwargs,
        )
        assert modified["generated_token_ids"] == native["generated_token_ids"]
        assert [p for e in modified["events"] for p in e["positions"]] == list(
            range(2, 2 + len(modified["generated_token_ids"]))
        )
    with torch.no_grad():
        adapter.up.weight.normal_(std=0.1)
    off = r["generate"](
        model, tok, ids, adapter=adapter, memory=memory, probabilities=[1.0] * 3, **kwargs
    )
    assert off["generated_token_ids"] == native["generated_token_ids"]
    assert all(e["relative_delta"] == 0 for e in off["events"])
    calls = 0

    def deadline():
        nonlocal calls
        calls += 1
        if calls == 2:
            raise TimeoutError("fixture")

    with pytest.raises(TimeoutError):
        r["generate"](
            model,
            tok,
            ids,
            adapter=adapter,
            memory=memory,
            probabilities=[0.3] * 3,
            deadline=deadline,
            **kwargs,
        )
    assert not getattr(model, "_jev_feedback_active", False)
    assert not model.model.layers[1]._forward_hooks
    with pytest.raises(ValueError, match="binding"):
        r["generate"](model, tok, ids, adapter=adapter, **kwargs)
    assert (
        r["generate"](model, tok, ids, **kwargs)["generated_token_ids"]
        == native["generated_token_ids"]
    )


def test_single_memory_is_contextual_and_position_matched_with_frozen_weight_ownership():
    torch = pytest.importorskip("torch")
    r, model = runtime(), tiny()
    before = r["weight_digest"](model)
    first = r["extract"](model, [1, 2, 3, 4], [2, 3], layer=1)
    changed = r["extract"](model, [8, 9, 3, 4], [2, 3], layer=1)
    assert torch.equal(first["embedding"], changed["embedding"])
    assert not torch.allclose(first["contextual"], changed["contextual"])
    assert first["contextual"].shape == (16,) and not first["contextual"].requires_grad
    assert first["processed_tokens"] == 4 and first["positions"] == [2, 3]
    assert r["weight_digest"](model) == before
    for positions in ([], [4], [2, 2], [3, 2], [True]):
        with pytest.raises(ValueError):
            r["extract"](model, [1, 2, 3, 4], positions, layer=1)
    original = model.forward

    def fail(*args, **kwargs):
        raise TimeoutError("fixture")

    model.forward = fail
    with pytest.raises(TimeoutError):
        r["extract"](model, [1, 2, 3, 4], [2, 3], layer=1)
    assert not model.model.layers[1]._forward_hooks
    assert not getattr(model, "_jev_feedback_active", False)
    model.forward = original
    assert all(p.grad is None and not p.requires_grad for p in model.parameters())


def test_single_repair_keeps_native_ids_and_never_inserts_three_room_instruction():
    r, tok = runtime(), Tok()
    for draft in ([4, 5], [4, 5, 31]):
        prefix = r["repair_prefix"](tok, [1, 2, 3], draft)
        assert prefix == [1, 2, 3, 4, 5, 31, 7, 8]
        assert "ANSWER:" in tok.encoded and "three" not in tok.encoded
    for draft in ([], [31, 4], [True]):
        with pytest.raises(ValueError):
            r["repair_prefix"](tok, [1, 2, 3], draft)
