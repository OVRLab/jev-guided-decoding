import runpy
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")
transformers = pytest.importorskip("transformers")
RUNTIME = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "research/experiments/logit_runtime.py")
)


class Tokenizer:
    eos_token_id = 16
    pad_token_id = 0

    def decode(self, ids, **kwargs):
        return "".join(f" t{i}" for i in ids if i not in (0, 16))


def backend():
    from jev_guided_decoding.backends.transformers import TransformersBackend

    torch.manual_seed(543)
    model = transformers.GPT2LMHeadModel(
        transformers.GPT2Config(
            vocab_size=17,
            n_positions=64,
            n_embd=16,
            n_layer=1,
            n_head=2,
            eos_token_id=16,
            pad_token_id=0,
            bos_token_id=1,
            resid_pdrop=0,
            embd_pdrop=0,
            attn_pdrop=0,
        )
    )
    base = TransformersBackend(model, Tokenizer(), model_id="offline-tiny", temperature=1, top_p=1)
    return RUNTIME["LogitTokenBackend"](base)


def test_model_distribution_and_sparse_bias_change_token_probabilities():
    engine = backend()
    state = engine.inspect((1, 2), (), count=4)
    assert sum(state.probabilities.tolist()) == pytest.approx(1)
    token = state.options[-1][0]
    native = engine.distribution(state, {})
    adjusted = engine.distribution(state, {token: 0.5})
    assert adjusted[token] > native[token]
    assert adjusted[0] == native[0] == 0
    assert torch.all(adjusted[1:] > 0)
    assert not any(p.requires_grad for p in engine.base.model.parameters())


def test_discarded_lookahead_and_global_rng_cannot_change_native_token_sequence():
    engine = backend()
    prefix = (3,)
    state = engine.inspect((1, 2), prefix, count=4)
    before = [engine.sample(state, {}, seed=i)[0] for i in range(40)]
    model_before = {k: v.clone() for k, v in engine.base.model.state_dict().items()}
    engine.lookahead((1, 2), prefix, first_token=4, max_tokens=4, seed=29, max_seconds=10)
    torch.manual_seed(888)
    torch.rand(1000)
    after_state = engine.inspect((1, 2), prefix, count=4)
    after = [engine.sample(after_state, {}, seed=i)[0] for i in range(40)]
    assert before == after
    assert torch.equal(state.probabilities, after_state.probabilities)
    assert all(torch.equal(v, engine.base.model.state_dict()[k]) for k, v in model_before.items())


def test_context_and_invalid_bias_fail_before_sampling():
    engine = backend()
    with pytest.raises(ValueError, match="context"):
        engine.inspect(tuple([1] * 65), (), count=4)
    state = engine.inspect((1, 2), (), count=4)
    for bias in ({999: 1}, {1: float("nan")}, {1: 21}):
        with pytest.raises(ValueError):
            engine.sample(state, bias, seed=1)
