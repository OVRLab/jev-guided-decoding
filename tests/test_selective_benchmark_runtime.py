import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
HERE = ROOT / "research/iterations/selective_benchmarks"


def runtime():
    pytest.importorskip("torch")
    return runpy.run_path(str(HERE / "runtime.py"))


class Tokenizer:
    pad_token_id = 0

    def decode(self, ids, skip_special_tokens=False):
        return " ".join(map(str, ids))


def tiny():
    return runpy.run_path(str(ROOT / "tests/test_evidence_attention.py"))["tiny"]()


def test_padded_batch_owns_exact_prefixes_and_counts_actual_forward_slots():
    r = runtime()
    m = tiny()
    prompts = [[1, 2, 3], [4, 5]]
    rows, work = r["generate_batch"](m, Tokenizer(), prompts, limit=3, eos=[31], seed=2601)
    assert [row["prompt_token_ids"] for row in rows] == prompts
    assert all(1 <= len(row["generated_token_ids"]) <= 3 for row in rows)
    assert work["batch_size"] == 2
    assert work["processed_token_slots"] == 2 * 3 + 2 * (work["forwards"] - 1)
    assert work["padded_prompt_tokens"] == 6
    for prompt, row in zip(prompts, rows, strict=True):
        one, _ = r["generate_batch"](m, Tokenizer(), [prompt], limit=3, eos=[31], seed=2601)
        assert row["generated_token_ids"] == one[0]["generated_token_ids"]
    assert not m._forward_pre_hooks


def test_single_request_adapter_gate_zero_and_scope_cleanup():
    r = runtime()
    m = tiny()
    branch = r["B"]["Repair"](16, 4)
    args = dict(limit=3, eos=[31], seed=2601)
    native, _ = r["generate_batch"](m, Tokenizer(), [[1, 2, 3]], **args)
    off, _ = r["generate_batch"](
        m, Tokenizer(), [[1, 2, 3]], adapter=branch, gate=0.0, layer=1, **args
    )
    assert off[0]["generated_token_ids"] == native[0]["generated_token_ids"]
    assert off[0]["events"][0]["positions"] == [2]
    assert not m.model.layers[1]._forward_hooks
    with pytest.raises(ValueError, match="one"):
        r["generate_batch"](m, Tokenizer(), [[1], [2]], adapter=branch, layer=1, **args)
    assert not m._forward_pre_hooks


def test_deadline_stops_before_forward_and_removes_hooks():
    r = runtime()
    m = tiny()

    def expired():
        raise TimeoutError("expired")

    with pytest.raises(TimeoutError, match="expired"):
        r["generate_batch"](
            m, Tokenizer(), [[1, 2]], limit=3, eos=[31], seed=2601, deadline=expired
        )
    assert not m._forward_pre_hooks


def test_model_final_readout_does_not_score_unfinished_thinking():
    r = runtime()
    assert r["final_text"]("thinking Final: B", True) == ("", "unfinished_thinking")
    assert r["final_text"]("thinking Final: B</think>Final: C", True) == ("Final: C", "complete")
    assert r["final_text"]("Final: A", False) == ("Final: A", "complete")


def test_native_batch_needs_no_provider_or_adapter():
    r = runtime()
    m = tiny()
    rows, _ = r["generate_batch"](m, Tokenizer(), [[1, 2]], limit=1, eos=[31], seed=2601)
    assert rows[0]["events"] == []
    for bad in ([], [[]], [[1] * 16385]):
        with pytest.raises(ValueError):
            r["generate_batch"](m, Tokenizer(), bad, limit=2, eos=[31], seed=2601)


def test_standard_qwen_cache_path_works_without_granite_config_fields():
    torch = pytest.importorskip("torch")
    from transformers import Qwen3Config, Qwen3ForCausalLM

    r = runtime()
    torch.manual_seed(7)
    m = Qwen3ForCausalLM(
        Qwen3Config(
            vocab_size=32,
            hidden_size=16,
            intermediate_size=32,
            num_hidden_layers=2,
            num_attention_heads=4,
            num_key_value_heads=2,
            head_dim=4,
        )
    ).eval()
    rows, _ = r["generate_batch"](m, Tokenizer(), [[1, 2], [4]], limit=2, eos=[31], seed=2601)
    assert [x["prompt_token_ids"] for x in rows] == [[1, 2], [4]]
