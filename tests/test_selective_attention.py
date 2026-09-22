import asyncio
import copy
import runpy
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "research/iterations/selective_attention"


def module(name):
    return runpy.run_path(str(HERE / f"{name}.py"))


def test_mass_conservation_preserves_other_attention_and_causality():
    torch = pytest.importorskip("torch")
    a = module("attention")
    torch.manual_seed(15)
    q, k = torch.randn(1, 4, 5, 4), torch.randn(1, 2, 5, 4)
    original = torch.full((1, 1, 5, 5), float("-inf")).triu(1)
    mask = a["controlled_mask"](
        q,
        k,
        original,
        positions=list(range(5)),
        query_start=3,
        source_keys=[0, 1, 2],
        head_bias={1: {0: 5.0}},
        scaling=0.5,
        conserve=True,
    )
    logits = q @ k.repeat_interleave(2, 1).transpose(-2, -1) * 0.5
    before, after = (logits + original).softmax(-1), (logits + mask).softmax(-1)
    torch.testing.assert_close(after[..., :3].sum(-1), before[..., :3].sum(-1))
    torch.testing.assert_close(after[..., 3:], before[..., 3:])
    assert after[0, 1, 4, 0] > before[0, 1, 4, 0]
    assert after[0, 1, 3, 4] == 0
    torch.testing.assert_close(after[:, [0, 2, 3]], before[:, [0, 2, 3]])
    torch.testing.assert_close(after[:, :, :3], before[:, :, :3])


@pytest.mark.parametrize("mode", ["additive", "conserve"])
def test_interface_noop_cache_equivalence_binding_and_exception_cleanup(mode):
    torch = pytest.importorskip("torch")
    from transformers.modeling_utils import ALL_ATTENTION_FUNCTIONS

    old = ALL_ATTENTION_FUNCTIONS["sdpa"]
    tiny = runpy.run_path(str(ROOT / "tests/test_evidence_attention.py"))["tiny"]
    model = tiny()
    a = module("attention")
    hook = a["SelectiveAttention"](model)
    ids = [1, 2, 3, 4, 5]
    maps = {(0, 1): {0: 2.0}, (1, 2): {1: 4.0}}
    kw = dict(query_start=3, source_keys=[0, 1, 2], mode=mode)
    with torch.inference_mode():
        raw = model(torch.tensor([ids]), use_cache=False).logits
        with hook.apply(ids, maps={}, **kw):
            assert torch.equal(raw, model(torch.tensor([ids]), use_cache=False).logits)
        with hook.apply(ids, maps=maps, **kw):
            full = model(torch.tensor([ids]), use_cache=False).logits
        with hook.apply(ids[:4], maps=maps, **kw):
            first = model(
                torch.tensor([ids[:4]]), past_key_values=a["new_cache"](model), use_cache=True
            )
        with hook.apply([5], maps=maps, past_length=4, **kw):
            cached = model(
                torch.tensor([[5]]), past_key_values=first.past_key_values, use_cache=True
            ).logits
        torch.testing.assert_close(full[:, -1], cached[:, -1], atol=1e-6, rtol=1e-5)
        assert not torch.equal(raw[:, -1], full[:, -1])
        with pytest.raises(ValueError, match="binding"):
            with hook.apply(ids, maps=maps, **kw):
                model(torch.tensor([[1, 2, 3, 4, 9]]), use_cache=False)
        with pytest.raises(RuntimeError, match="active"):
            with hook.apply(ids, maps=maps, **kw):
                with hook.apply(ids, maps=maps, **kw):
                    pass
    assert ALL_ATTENTION_FUNCTIONS["sdpa"] is old and not hook.active


def test_policy_envelopes_and_invalid_values():
    p = module("policies")
    grid = p["grid"]()
    assert len(grid) == 12 and len({x["id"] for x in grid}) == 12
    prefill = next(x for x in grid if x["envelope"] == "prefill")
    assert p["strength"](prefill, 0) > 0 and p["strength"](prefill, 1) == 0
    fade = next(x for x in grid if x["envelope"] == "fade8")
    assert p["strength"](fade, 0) > p["strength"](fade, 4) > 0
    assert p["strength"](fade, 8) == 0
    for bad in (float("nan"), -1, 6, True):
        with pytest.raises(ValueError):
            p["strength"]({**fade, "strength": bad}, 0)


def test_gate_can_learn_helpfulness_instead_of_blindly_calling_on_uncertainty():
    p = module("policies")
    rows = []
    for domain in ("original", "hotpot"):
        for i in range(12):
            rows.append(
                {
                    "family": domain,
                    "features": {
                        "min_probability": (i + 1) / 14,
                        "mean_entropy": 1.0,
                        "copy_fraction": float(i >= 6),
                    },
                    "native_quality": 0.0 if i >= 6 else 1.0,
                    "guided_quality": 1.0 if i >= 6 else 0.0,
                }
            )
    selected = p["fit_gates"](rows)
    benefit = selected["benefit"]["gate"]
    calls = [p["gate_decision"](benefit, r["features"], str(i)) for i, r in enumerate(rows)]
    assert calls == [i % 12 >= 6 for i in range(24)]
    assert selected["benefit"]["call_fraction"] == 0.5
    assert not p["gate_decision"]({"kind": "never"}, {}, "x")
    with pytest.raises(ValueError):
        p["gate_decision"](
            {"kind": "threshold", "feature": "mean_entropy", "threshold": 1, "direction": "gt"},
            {"mean_entropy": float("nan")},
            "x",
        )


def tiny_runtime():
    torch = pytest.importorskip("torch")
    model = runpy.run_path(str(ROOT / "tests/test_evidence_attention.py"))["tiny"]()

    class Tokenizer:
        def decode(self, ids, **kwargs):
            return " ".join(str(i) for i in ids)

    base = SimpleNamespace(
        model=model,
        tokenizer=Tokenizer(),
        device=torch.device("cpu"),
        eos_ids=set(),
        _sync=lambda: None,
    )
    runtime = module("runtime")["Runtime"](base)
    encoded = {
        "input_ids": [1, 2, 3, 4],
        "query_start": 3,
        "span_token_indices": [[0], [1]],
        "prompt_digest": "test",
    }
    view = {
        "id": "x",
        "family": "original",
        "question": "Where?",
        "sources": [{"id": "A", "text": "First fact"}, {"id": "B", "text": "Second fact"}],
    }
    policy = {
        "id": "tiny",
        "mode": "conserve",
        "envelope": "fade8",
        "strength": 2,
        "heads": [[0, 1], [1, 2]],
        "threshold": 0.65,
    }
    return runtime, encoded, view, policy


def test_skipped_gate_never_calls_provider_and_continues_identical_native_cache():
    runtime, encoded, view, policy = tiny_runtime()
    r = module("runtime")

    async def forbidden(v):
        raise AssertionError("A skipped gate must not call Jev")

    native = asyncio.run(r["generate"](runtime, encoded, view, None, forbidden))
    skipped = asyncio.run(
        r["generate"](runtime, encoded, view, policy, forbidden, gate={"kind": "never"})
    )
    assert native["final"]["token_ids"] == skipped["final"]["token_ids"]
    assert skipped["pilot_reused"] and skipped["logical_jev_calls"] == 0
    assert skipped["model_forwards"] == len(skipped["final"]["token_ids"])


def test_gated_success_discards_pilot_and_failure_falls_back_without_second_call():
    runtime, encoded, view, policy = tiny_runtime()
    r = module("runtime")
    calls = []

    async def success(v):
        calls.append(copy.deepcopy(v))
        return {"status": "complete", "key": "receipt", "scores": [0.9, 0.1]}

    guided = asyncio.run(
        r["generate"](runtime, encoded, view, policy, success, gate={"kind": "always"})
    )
    assert len(calls) == 1 and set(calls[0]) == set(view)
    assert not guided["pilot_reused"] and guided["pilot"]["token_ids"]
    assert guided["model_forwards"] == len(guided["pilot"]["token_ids"]) + len(
        guided["final"]["token_ids"]
    )
    assert (
        guided["final"]["input_and_output_ids"]
        == encoded["input_ids"] + guided["final"]["token_ids"]
    )
    assert all(x["token_id"] == x["argmax_id"] for x in guided["final"]["tokens"])

    async def failure(v):
        calls.append(v)
        return {"status": "failed", "key": "failed", "usage_unknown": True}

    fallback = asyncio.run(
        r["generate"](runtime, encoded, view, policy, failure, gate={"kind": "always"})
    )
    assert len(calls) == 2 and fallback["provider_status"] == "failed_fallback"
    assert fallback["pilot_reused"] and fallback["logical_jev_calls"] == 1
    assert fallback["model_forwards"] == len(fallback["final"]["token_ids"])


def test_early_eos_is_a_completion_and_does_not_trigger_extra_generation():
    runtime, encoded, view, policy = tiny_runtime()
    r = module("runtime")
    session = runtime.session(encoded)
    session.extend(1)
    runtime.base.eos_ids.add(session.tokens[0]["token_id"])

    async def forbidden(v):
        raise AssertionError

    result = asyncio.run(
        r["generate"](runtime, encoded, view, policy, forbidden, gate={"kind": "never"})
    )
    assert result["model_forwards"] == 1 and result["final"]["finish_reason"] == "eos"


@pytest.mark.parametrize("envelope,active_forwards", [("all", 12), ("prefill", 1), ("fade8", 8)])
def test_real_tiny_model_stops_intervening_at_the_phase_boundary(envelope, active_forwards):
    runtime, encoded, _, policy = tiny_runtime()
    session = runtime.session(encoded)
    session.extend(12, {**policy, "envelope": envelope}, [0.9, 0.1])
    result = session.result()
    assert sum(t["active_heads"] > 0 for t in result["tokens"]) == active_forwards
    assert result["hook_calls"] == 2 * active_forwards
    assert result["model_forwards"] == 12


def test_uniform_source_judgments_are_an_exact_noop_with_unchanged_weights():
    torch = pytest.importorskip("torch")
    runtime, encoded, _, policy = tiny_runtime()
    before = {k: v.clone() for k, v in runtime.base.model.state_dict().items()}
    native, equal = runtime.session(encoded), runtime.session(encoded)
    native.extend(12)
    equal.extend(12, policy, [0.9, 0.9])
    assert native.result()["token_ids"] == equal.result()["token_ids"]
    assert equal.result()["hook_calls"] == 0
    assert all(torch.equal(v, before[k]) for k, v in runtime.base.model.state_dict().items())


def test_additive_attention_matches_the_prior_r16_hook_exactly():
    torch = pytest.importorskip("torch")
    runtime, encoded, _, _ = tiny_runtime()
    old = module("attention")["OLD"]["AdaptiveAttention"](runtime.base.model)
    ids = encoded["input_ids"]
    maps = {(0, 1): {0: 2.0}, (1, 2): {1: 4.0}}
    with torch.inference_mode():
        with old.apply(ids, query_start=3, maps=maps):
            prior = runtime.base.model(torch.tensor([ids]), use_cache=False).logits
        with runtime.hook.apply(ids, query_start=3, source_keys=[0, 1], maps=maps, mode="additive"):
            current = runtime.base.model(torch.tensor([ids]), use_cache=False).logits
    assert torch.equal(prior, current)
