import runpy
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")
transformers = pytest.importorskip("transformers")
ROOT = Path(__file__).resolve().parents[1]
M = runpy.run_path(str(ROOT / "research/experiments/evidence_attention.py"))


def tiny():
    from transformers import GraniteMoeHybridConfig, GraniteMoeHybridForCausalLM

    torch.manual_seed(123)
    config = GraniteMoeHybridConfig(
        vocab_size=32,
        hidden_size=16,
        intermediate_size=32,
        num_hidden_layers=2,
        num_attention_heads=4,
        num_key_value_heads=2,
        num_local_experts=0,
        num_experts_per_tok=0,
        layer_types=["attention", "attention"],
        attention_dropout=0.0,
        shared_intermediate_size=32,
        mamba_n_heads=4,
    )
    config._attn_implementation = "sdpa"
    return GraniteMoeHybridForCausalLM(config).eval().requires_grad_(False)


def test_mask_changes_only_selected_head_query_and_source_without_unmasking_future():
    mask = M["steered_mask"](
        None,
        heads=(1,),
        num_heads=4,
        length=5,
        query_start=3,
        token_bias={0: 1.2, 2: 0.7},
        device="cpu",
        dtype=torch.float32,
    )
    assert mask.shape == (1, 4, 5, 5)
    assert mask[0, 1, 3, 0].item() == pytest.approx(1.2)
    assert mask[0, 1, 4, 2].item() == pytest.approx(0.7)
    assert mask[0, 0, 3, 0] == 0
    assert mask[0, 1, 2, 0] == 0
    assert mask[0, 1, 3, 4] < -1e20


def test_zero_identity_nonzero_causal_effect_and_exception_restores_hooks():
    model = tiny()
    ids = torch.tensor([[1, 2, 3, 4, 5]])
    weights = {k: v.clone() for k, v in model.state_dict().items()}
    control = M["EvidenceAttention"](model)
    with torch.inference_mode():
        original = model(ids, use_cache=False).logits
        with control.apply(ids[0].tolist(), query_start=3, heads=[(0, 1)], token_bias={}):
            zero = model(ids, use_cache=False).logits
        assert torch.equal(original, zero)
        with control.apply(ids[0].tolist(), query_start=3, heads=[(0, 1)], token_bias={0: 2.0}):
            changed = model(ids, use_cache=False).logits
            assert control.calls == 1
        # Supplying a 4D mask can change SDPA numerical dispatch even on zero rows.
        torch.testing.assert_close(original[:, :3], changed[:, :3], atol=1e-7, rtol=0)
        assert not torch.equal(original[:, -1], changed[:, -1])
        with pytest.raises(RuntimeError, match="deliberate"):
            with control.apply(ids[0].tolist(), query_start=3, heads=[(0, 1)], token_bias={0: 2.0}):
                raise RuntimeError("deliberate")
        assert torch.equal(original, model(ids, use_cache=False).logits)
    assert all(torch.equal(weights[k], v) for k, v in model.state_dict().items())


def test_request_binding_cache_rejection_and_nested_scope():
    model = tiny()
    control = M["EvidenceAttention"](model)
    kwargs = dict(query_start=3, heads=[(0, 1)], token_bias={0: 1.0})
    with control.apply([1, 2, 3, 4], **kwargs):
        with pytest.raises(ValueError, match="prefix"):
            model(torch.tensor([[1, 2, 9, 4]]), use_cache=False)
        with pytest.raises(ValueError, match="cache"):
            model(torch.tensor([[1, 2, 3, 4]]), use_cache=True)
        with pytest.raises(RuntimeError, match="active"):
            with control.apply([1, 2, 3, 4], **kwargs):
                pass


@pytest.mark.parametrize(
    "heads,bias",
    [([(2, 0)], {0: 1}), ([(0, 4)], {0: 1}), ([(0, 0)], {3: 1}), ([(0, 0)], {0: float("nan")})],
)
def test_invalid_policies_fail_before_hook_registration(heads, bias):
    control = M["EvidenceAttention"](tiny())
    with pytest.raises(ValueError):
        with control.apply([1, 2, 3, 4], query_start=3, heads=heads, token_bias=bias):
            pass
    assert not control.active


def test_offset_mapping_preserves_unicode_repeated_text_and_rejects_uncovered_spans():
    offsets = [(0, 0), (0, 2), (2, 5), (5, 8), (8, 11), (11, 14)]
    assert M["span_token_indices"](offsets, [(2, 5), (8, 11)]) == [[2], [4]]
    with pytest.raises(ValueError):
        M["span_token_indices"](offsets, [(20, 25)])


def test_equal_scores_are_noop_and_bias_is_bounded():
    assert M["bias_from_scores"]([[1], [3]], [0.9, 0.9], 2.0) == {}
    assert M["bias_from_scores"]([[1, 2], [3]], [0.8, 0.2], 2.0) == pytest.approx({1: 1.2, 2: 1.2})
