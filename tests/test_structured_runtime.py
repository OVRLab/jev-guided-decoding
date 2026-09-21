import runpy
from pathlib import Path
from types import SimpleNamespace

import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("transformers")
ROOT = Path(__file__).resolve().parents[1]
TINY = runpy.run_path(str(ROOT / "tests/test_logit_runtime.py"))
S = runpy.run_path(str(ROOT / "research/experiments/structured_runtime.py"))


def test_common_syntax_mask_normalizes_only_the_permitted_tokens():
    runtime = S["StructuredRuntime"](TINY["backend"]().base)
    state = runtime.inspect((1, 2), (), allowed=(4, 5), count=4)
    assert state.probabilities.sum().item() == pytest.approx(1)
    assert {t for t, p in state.options} == {4, 5}
    assert torch.count_nonzero(state.probabilities).item() == 2
    assert 0 < state.syntax_mass <= 1
    for seed in range(10):
        assert runtime.sample(state, {}, seed=seed)[0] in {4, 5}


def test_impossible_empty_or_pad_only_mask_fails():
    runtime = S["StructuredRuntime"](TINY["backend"]().base)
    for allowed in [(), (999,), (0,), (4, 4)]:
        with pytest.raises(ValueError):
            runtime.inspect((1, 2), (), allowed=allowed)


def test_greedy_lookahead_returns_exact_grammar_tokens_and_real_work():
    runtime = S["StructuredRuntime"](TINY["backend"]().base)
    grammar = S["GRAMMAR"]["TokenTrie"]([(3, 4, 6), (3, 5, 7)])
    result = runtime.continue_frame(
        (1, 2), (3,), frame_offset=0, grammar=grammar, max_tokens=4, seed=42, greedy=True
    )
    assert grammar.complete((3,) + tuple(result["token_ids"]))
    assert result["generated_tokens"] == 2
    assert result["prefill_tokens"] == 3 + 4
    assert len(result["trace"]) == 2
    assert result["finish_reason"] == "frame"


def test_grammar_keeps_supplied_opening_when_tokenizer_merges_text_boundary():
    mapping = {
        "Mira is blue.</step>": [4],
        "Mira is not blue.</step>": [5],
        "It is not established that Mira is blue.</step>": [6],
    }

    def encode(text, **kwargs):
        return mapping.get(text, [9])

    def decode(ids):
        reverse = {tuple(v): k for k, v in mapping.items()}
        return "<step>" + reverse[tuple(ids[1:])]

    base = SimpleNamespace(
        top_p=1,
        encode_control=lambda _: (3,),
        tokenizer=SimpleNamespace(encode=encode),
        decode=decode,
    )
    grammar, opening = S["StructuredRuntime"](base).make_grammar(["Mira"], ["blue"])
    assert opening == (3,)
    assert grammar.allowed(opening) == (4, 5, 6)
