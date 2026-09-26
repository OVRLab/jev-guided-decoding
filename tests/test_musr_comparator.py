import json
import runpy
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1] / "research/iterations/musr_transfer"


def test_larger_profiles_have_explicit_supported_limits_and_case_local_sampling():
    c = runpy.run_path(str(HERE / "comparator.py"))
    a = c["profile"]("nonthinking", "case/a")
    b = c["profile"]("thinking", "case/a")
    assert a["limit"] == 2048 and b["limit"] == 8192
    assert a["thinking"] is False and b["thinking"] is True
    assert a["sampling"]["temperature"] == 1 and a["sampling"]["top_p"] == 0.95
    assert a == c["profile"]("nonthinking", "case/a")
    assert a["sampling"]["seed"] != c["profile"]("nonthinking", "case/b")["sampling"]["seed"]
    with pytest.raises(ValueError):
        c["profile"]("short-thinking", "case/a")


def test_larger_serial_runner_keeps_exact_templates_and_every_completion(tmp_path):
    torch = pytest.importorskip("torch")
    from transformers import GraniteConfig, GraniteForCausalLM

    c = runpy.run_path(str(HERE / "comparator.py"))
    config = GraniteConfig(
        hidden_size=16,
        intermediate_size=32,
        num_hidden_layers=2,
        num_attention_heads=2,
        num_key_value_heads=1,
        vocab_size=256,
        max_position_embeddings=16384,
    )
    model = GraniteForCausalLM(config).eval().requires_grad_(False)
    model.lm_head = torch.nn.Linear(16, 256, bias=True).eval().requires_grad_(False)
    with torch.no_grad():
        model.lm_head.weight.zero_()
        model.lm_head.bias.fill_(-1000)
        model.lm_head.bias[0] = 0

    class Tok:
        def apply_chat_template(self, messages, **kwargs):
            assert kwargs["tokenize"] and kwargs["add_generation_prompt"]
            end = "<think>\n" if kwargs["thinking"] else "<think></think>"
            return list((messages[0]["content"] + end).encode())

        def decode(self, ids, **kwargs):
            return bytes(ids).decode(errors="replace")

    case = dict(
        id="case/a",
        task="team_allocation",
        split="development",
        context="Alice can cook; Bob can drive.",
        question="Who cooks?",
        choices=["Alice", "Bob"],
    )
    output = tmp_path / "larger"
    runner = c["Comparator"](model, Tok(), [0], output, max_seconds=30)
    runner.run([case], ["nonthinking", "thinking"])
    rows = [json.loads(line) for line in (output / "outputs.jsonl").read_text().splitlines()]
    assert len(rows) == 2 and all(r["generated_token_ids"] == [0] for r in rows)
    assert all(r["events"] == [] and r["probabilities"] is None for r in rows)
    assert all(r["sampling"]["top_k"] == 50 for r in rows)
    assert rows[0]["prompt_token_ids"][-len("<think></think>") :] == list(b"<think></think>")
    assert rows[1]["prompt_token_ids"][-len("<think>\n") :] == list(b"<think>\n")
    assert json.loads((output / "complete.json").read_text())["outputs"] == 2
    assert json.loads((output / "mechanical-admission.json").read_text())["cache_argmax_equal"]
    audit = runpy.run_path(str(HERE / "audit.py"))["check_comparator"]
    assert (
        audit([case], ["nonthinking", "thinking"], output, Tok(), eos=0, vocab=256)["outputs"] == 2
    )
    changed = [dict(r) for r in rows]
    changed[0]["sampling"] = changed[0]["sampling"] | {"seed": 3}
    (output / "outputs.jsonl").write_text("".join(json.dumps(r) + "\n" for r in changed))
    with pytest.raises(ValueError, match="generation|sampling"):
        audit([case], ["nonthinking", "thinking"], output, Tok(), eos=0, vocab=256)
    (output / "outputs.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    with pytest.raises(ValueError, match="Duplicate"):
        runner.run([case], ["thinking"])
    with pytest.raises(FileExistsError):
        c["Comparator"](model, Tok(), [0], output, max_seconds=30)
    bad = c["Comparator"](model, Tok(), [0], tmp_path / "bad", max_seconds=30)
    with pytest.raises(ValueError, match="case|reference"):
        bad.run([case | {"reference": 0}], ["thinking"])
    assert not (tmp_path / "bad/outputs.jsonl").exists()
    assert not any(block._forward_hooks for block in model.model.layers)
