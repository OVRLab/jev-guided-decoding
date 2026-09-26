import asyncio
import json
import runpy
from pathlib import Path

import pytest

from jev_guided_decoding.experiment_budget import InputTokenBudget

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "research/iterations/musr_transfer"


def load():
    return runpy.run_path(str(HERE / "pipeline.py"))


def fixture():
    cases = [
        dict(
            id=f"case/{i}",
            task="murder_mystery",
            split="test",
            context=f"Story {i}: Alice entered the hall.",
            question="Who entered the hall?",
            choices=["Alice", "Bob"],
        )
        for i in range(4)
    ]
    groups = {c["id"]: f"murder_mystery/{i // 2}" for i, c in enumerate(cases)}
    return cases, groups


def test_donors_preserve_marginals_and_never_pair_related_scenarios():
    p = load()
    cases, groups = fixture()
    donors = p["donors"](cases, groups)
    assert set(donors) == set(donors.values()) == set(groups)
    assert all(groups[a] != groups[b] for a, b in donors.items())
    uneven = groups | {"case/3": "murder_mystery/2"}
    assert all(uneven[a] != uneven[b] for a, b in p["donors"](cases, uneven).items())
    with pytest.raises(ValueError, match="derangement"):
        p["donors"](cases, groups | {"case/2": "murder_mystery/0"})
    with pytest.raises(ValueError):
        p["donors"](cases, groups | {"other": "x"})


def exercise(tmp_path):
    torch = pytest.importorskip("torch")
    p = load()
    tiny = runpy.run_path(str(ROOT / "tests/test_evidence_attention.py"))["tiny"]()
    tiny.config.vocab_size = 256
    model = type(tiny)(tiny.config).eval().requires_grad_(False)
    with torch.no_grad():
        model.lm_head.weight.zero_()  # Every completion is real model EOS; no quality claim.

    class Tok:
        def encode(self, text, **kwargs):
            return list(text.encode())

        def decode(self, ids, **kwargs):
            return bytes(ids).decode(errors="replace")

        def convert_tokens_to_ids(self, text):
            return 0

        def apply_chat_template(self, messages, **kwargs):
            return self.encode("USER:\n" + messages[0]["content"] + "\nASSISTANT:\n")

    class Provider:
        async def _evaluate(self, payload, parser, **kwargs):
            assert payload["state"]["response"] == ""
            probability = (int(payload["state"]["story"].split(":")[0].split()[-1]) + 1) / 5
            raw = dict(
                model="jev-1.13.0",
                answers=dict(correct=dict(type="noul", noul=probability)),
                usage=dict(input_tokens=250, output_tokens=10),
            )
            return parser(raw["answers"]), raw["model"], 250, 10, 1, 0.01, raw

    manifest = dict(
        native_limit=8,
        repair_limit=8,
        context_limit=2048,
        max_seconds=60,
        layer=1,
        api_cap_usd=0.05,
        usd_per_million=0.05,
    )
    out = tmp_path / "attempt"
    runner = p["Runner"](model, Tok(), [0], manifest, out, None)
    cases, groups = fixture()
    with InputTokenBudget(out / "budget.jsonl", max_usd=0.05) as budget:
        runner.feedback = p["F"]["Feedback"](Provider(), budget, out, delay=0)
        asyncio.run(runner.drafts(cases))
        with pytest.raises(ValueError, match="Duplicate"):
            asyncio.run(runner.drafts(cases[:1]))
        assert budget.charged_tokens == 1000 and not budget.unresolved
    adapters = {}
    for kind in ("contextual", "embedding"):
        adapter = runner.runtime["B"]["Repair"](16, 4).eval()
        with torch.no_grad():
            adapter.up.weight.normal_(std=0.2)
        adapters[kind + "-scalar", 1] = adapter
    runner.repairs(cases, groups, adapters)
    rows = [json.loads(s) for s in (out / "outputs.jsonl").read_text().splitlines()]
    bindings = [json.loads(s) for s in (out / "generation-bindings.jsonl").read_text().splitlines()]
    assert len(rows) == len(bindings) == 32
    assert len(list((out / "memories").glob("*.safetensors"))) == 4
    assert all(r["generated_token_ids"] == [0] and r["finish_reason"] == "eos" for r in rows)
    assert all(r["text"] == "" for r in rows)
    assert all(
        b["adapter_digest"] is not None and b["memory_digest"] is not None
        for b in bindings
        if b["arm"] not in ("native", "blind")
    )
    natives = {r["id"]: r for r in rows if r["arm"] == "native"}
    for row in rows:
        if row["arm"] == "native":
            continue
        original = natives[row["id"]]["prompt_token_ids"] + [0]
        assert row["prompt_token_ids"][: len(original)] == original
        if row["arm"] != "blind":
            assert row["events"][0]["positions"] == [len(row["prompt_token_ids"]) - 1]
        if row["arm"].startswith("live/"):
            actual_provider_probability = (int(row["id"].split("/")[-1]) + 1) / 5
            assert row["probabilities"] == [actual_provider_probability] * 3
    with pytest.raises(ValueError, match="Duplicate"):
        runner.repairs(cases, groups, adapters)
    with pytest.raises(FileExistsError):
        p["Runner"](model, Tok(), [0], manifest, out, None)
    return dict(
        cases=cases,
        groups=groups,
        output=out,
        tok=runner.tok,
        manifest=manifest,
        adapter_digests={
            f"{name}/{seed}": runner.runtime["weight_digest"](adapter)
            for (name, seed), adapter in adapters.items()
        },
        width=16,
        vocab=256,
    )


def test_serial_pipeline_retains_all_raw_outputs_memories_and_intervention_bindings(tmp_path):
    exercise(tmp_path)
