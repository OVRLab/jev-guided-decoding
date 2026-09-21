import runpy
from pathlib import Path

import pytest

pytest.importorskip("torch")
pytest.importorskip("transformers")
ROOT = Path(__file__).resolve().parents[1]
R = runpy.run_path(str(ROOT / "research/experiments/evidence_runtime.py"))
T = runpy.run_path(str(ROOT / "tests/test_evidence_attention.py"))
D = runpy.run_path(str(ROOT / "research/experiments/evidence_data.py"))


def runtime():
    from tokenizers import Tokenizer
    from tokenizers.models import WordLevel
    from tokenizers.pre_tokenizers import Whitespace
    from transformers import PreTrainedTokenizerFast

    from jev_guided_decoding.backends.transformers import TransformersBackend

    vocab = {"[PAD]": 0, "[UNK]": 1, "[EOS]": 2}
    vocab.update({word: i + 3 for i, word in enumerate(D["LABELS"])})
    inner = Tokenizer(WordLevel(vocab, unk_token="[UNK]"))
    inner.pre_tokenizer = Whitespace()
    tokenizer = PreTrainedTokenizerFast(
        tokenizer_object=inner, unk_token="[UNK]", pad_token="[PAD]", eos_token="[EOS]"
    )
    tokenizer.chat_template = (
        "{% for m in messages %}{{ m['role'] + ': ' + m['content'] + '\n' }}{% endfor %}"
        "{% if add_generation_prompt %}assistant: {% endif %}"
    )
    return R["EvidenceRuntime"](
        TransformersBackend(T["tiny"](), tokenizer, model_id="tiny", top_p=1)
    )


def test_full_runtime_preserves_prompt_and_generator_owned_answer():
    r = runtime()
    case = D["context"](D["worlds"]("profile", 6)[0], "clean")
    view = D["model_view"](case)
    encoded = r.encode(view)
    assert len(encoded["span_token_indices"]) == len(case["sources"])
    native = r.forward(encoded)
    zero = r.forward(encoded, heads=[(0, 1)], scores=case["oracle_scores"], strength=0)
    assert native["label_logits"] == zero["label_logits"]
    assert native["generated_token_ids"] == zero["generated_token_ids"]
    assert native["label"] in D["LABELS"]
    assert sum(native["label_probabilities"]) == pytest.approx(1)
    highlighted = r.encode(view, highlights=[case["sources"][0]["id"]])
    assert highlighted["prompt_digest"] != encoded["prompt_digest"]
    assert all(s["text"] in highlighted["rendered_prompt"] for s in case["sources"])
    with pytest.raises(ValueError, match="public"):
        r.encode({**view, "reference": case["reference"]})


def test_full_study_flow_retains_overload_and_continues_only_new_context(tmp_path, monkeypatch):
    import asyncio
    import json

    import httpx

    from jev_guided_decoding.experiment_budget import InputTokenBudget

    S = runpy.run_path(str(ROOT / "research/experiments/evidence_study.py"))
    E = runpy.run_path(str(ROOT / "research/experiments/evidence_scorer.py"))
    calls, waits = [], []

    def reply(request):
        payload = json.loads(request.content)
        calls.append(payload)
        if len(calls) == 1:
            return httpx.Response(529, headers={"retry-after": "60"}, json={"error": "overload"})
        return httpx.Response(
            200,
            json={
                "model": "jev-1.13.0",
                "usage": {"input_tokens": 50, "output_tokens": 4},
                "answers": {
                    key: {"type": "noul", "noul": 0.8 if i == 0 else 0.2}
                    for i, key in enumerate(payload["questions"])
                },
            },
        )

    async def sleep(seconds):
        waits.append(seconds)

    monkeypatch.setattr(asyncio, "sleep", sleep)

    async def exercise():
        r = S["Runner"](runtime(), tmp_path, {"max_seconds": 60, "bootstrap_draws": 100})
        cases = [D["context"](D["worlds"]("profile", 6)[0], c) for c in ("clean", "distracted")]
        with InputTokenBudget(tmp_path / "ledger.jsonl") as budget:
            async with E["EvidenceScorer"](
                "test-key", budget=budget, transport=httpx.MockTransport(reply)
            ) as scorer:
                result = await r.evaluate(
                    cases,
                    {"heads": [(0, 1)], "random_heads": [(1, 2)], "strength": 1.0},
                    scorer,
                    name="test",
                )
            assert not budget.unresolved
            assert budget.charged_tokens == 65536 + 50
        r.close()
        assert result["recorded"] == 16
        assert result["arms"]["jev"]["complete"] == 1
        assert result["arms"]["native"]["complete"] == 2
        assert result["provider_incidents"] == 1
        assert waits == [60]
        assert len(calls) == 2
        rows = [json.loads(s) for s in (tmp_path / "test.jsonl").read_text().splitlines()]
        assert len({(row["id"], row["mode"]) for row in rows}) == 16
        assert sum(row["status"] == "failed" for row in rows) == 4

    asyncio.run(exercise())
