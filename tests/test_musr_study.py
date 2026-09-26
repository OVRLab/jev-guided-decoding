import asyncio
import json
import runpy
from pathlib import Path
from types import SimpleNamespace

import pytest

HERE = Path(__file__).resolve().parents[1] / "research/iterations/musr_transfer"


def test_worker_refuses_changed_freeze_or_existing_output_before_loading_models_or_keys(
    tmp_path, monkeypatch
):
    study = runpy.run_path(str(HERE / "study.py"))
    execute = study["execute"]
    args = SimpleNamespace(
        input=tmp_path / "missing",
        output=tmp_path / "output",
        device="cuda",
        key_file=tmp_path / "no-key",
    )
    with pytest.raises(FileNotFoundError):
        asyncio.run(execute(args))
    assert not args.output.exists()
    monkeypatch.setitem(execute.__globals__["CONTRACT"], "verify", lambda folder: {})
    args.output.mkdir()
    (args.output / "owner.txt").write_text("another run owns this")
    with pytest.raises(FileExistsError):
        asyncio.run(execute(args))
    assert (args.output / "owner.txt").read_text() == "another run owns this"
    assert not (args.output / "execution.json").exists()


def test_complete_worker_flow_with_tiny_models_fake_provider_and_simulated_device(
    tmp_path, monkeypatch
):
    torch = pytest.importorskip("torch")
    from safetensors.torch import save_file
    from transformers import GraniteConfig, GraniteForCausalLM

    study = runpy.run_path(str(HERE / "study.py"))
    execute = study["execute"]
    namespace = execute.__globals__
    runtime = runpy.run_path(str(HERE / "runtime.py"))
    model = runpy.run_path(str(HERE.parents[2] / "tests/test_evidence_attention.py"))["tiny"]()
    model.config.vocab_size = 256
    model = type(model)(model.config).eval().requires_grad_(False)
    with torch.no_grad():
        model.lm_head.weight.zero_()
    larger = (
        GraniteForCausalLM(
            GraniteConfig(
                hidden_size=16,
                intermediate_size=32,
                num_hidden_layers=2,
                num_attention_heads=2,
                num_key_value_heads=1,
                vocab_size=256,
                max_position_embeddings=16384,
            )
        )
        .eval()
        .requires_grad_(False)
    )
    larger.lm_head = torch.nn.Linear(16, 256, bias=True).eval().requires_grad_(False)
    with torch.no_grad():
        larger.lm_head.weight.zero_()
        larger.lm_head.bias.fill_(-1000)
        larger.lm_head.bias[0] = 0

    class Tok:
        def encode(self, text, **kwargs):
            return list(text.encode())

        def decode(self, ids, **kwargs):
            return bytes(ids).decode(errors="replace")

        def convert_tokens_to_ids(self, text):
            return 0

        def apply_chat_template(self, messages, **kwargs):
            end = (
                "ASSISTANT:\n"
                if "thinking" not in kwargs
                else "<think>\n"
                if kwargs["thinking"]
                else "<think></think>"
            )
            return self.encode("USER:\n" + messages[0]["content"] + "\n" + end)

    class Provider:
        def __init__(self, *args, **kwargs):
            pass

        async def __aexit__(self, *args):
            pass

        async def _evaluate(self, payload, parser, **kwargs):
            assert payload["state"]["selection"] is None
            raw = dict(
                model="jev-1.13.0",
                answers=dict(correct=dict(type="noul", noul=0.2)),
                usage=dict(input_tokens=250, output_tokens=10),
            )
            return parser(raw["answers"]), raw["model"], 250, 10, 1, 0.01, raw

    # Device admission is simulated only in this offline test. Actual tensors stay
    # on CPU, so the real completed-study auditor would reject this as CUDA evidence.
    real_to = torch.nn.Module.to

    def cpu_to(self, *args, **kwargs):
        if args and args[0] == "cuda":
            args = ("cpu",) + args[1:]
        return real_to(self, *args, **kwargs)

    monkeypatch.setattr(torch.nn.Module, "to", cpu_to)
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(torch.cuda, "get_device_name", lambda: "offline-simulation")
    monkeypatch.setattr(torch.cuda, "empty_cache", lambda: None)
    monkeypatch.setitem(namespace, "load_original", lambda device: (model, Tok(), [0]))
    monkeypatch.setitem(namespace, "load_larger", lambda device: (larger, Tok(), [0]))
    monkeypatch.setitem(namespace, "JevScorer", Provider)
    cases, groups = runpy.run_path(str(HERE.parents[2] / "tests/test_musr_pipeline.py"))[
        "fixture"
    ]()
    inputs = tmp_path / "input"
    inputs.mkdir()
    (inputs / "adapters").mkdir()
    specs = [["contextual-scalar", 3101], ["embedding-scalar", 3101]]
    selection = {}
    for name, seed in specs:
        adapter = runtime["B"]["Repair"](16, 4).eval().requires_grad_(False)
        file = f"{name}-{seed}.safetensors"
        save_file(adapter.state_dict(), str(inputs / "adapters" / file))
        selection[f"{name}/{seed}"] = dict(file=file)
    prompt = Tok().apply_chat_template(
        [dict(role="user", content=study["PIPE"]["S"]["prompt_for"](cases[0]))]
    )
    manifest = dict(
        backbone_digest=runtime["weight_digest"](model),
        layer=1,
        rank=4,
        specs=specs,
        native_limit=8,
        repair_limit=8,
        context_limit=2048,
        max_seconds=60,
        api_cap_usd=0.05,
        usd_per_million=0.05,
        api_delay_seconds=0,
        larger_profiles=["nonthinking", "thinking"],
        planned_cases=4,
        planned_outputs=40,
        planned_requests=4,
    )
    for name, value in (
        ("manifest", manifest),
        ("cases", cases),
        ("groups", groups),
        ("selection", selection),
        (
            "admission-input",
            dict(
                case=cases[0],
                native=dict(prompt_token_ids=prompt, generated_token_ids=[0], text=""),
            ),
        ),
    ):
        (inputs / f"{name}.json").write_text(json.dumps(value))
    monkeypatch.setitem(namespace["CONTRACT"], "verify", lambda folder: manifest)
    monkeypatch.setitem(namespace["CONTRACT"], "sources", lambda: {"scope": "offline-fixture"})
    key = tmp_path / "fake-key"
    key.write_text("unit-test-key")
    output = tmp_path / "worker"
    asyncio.run(execute(SimpleNamespace(input=inputs, output=output, device="cuda", key_file=key)))
    complete = json.loads((output / "complete.json").read_text())
    assert (
        complete["outputs"] == 40
        and complete["requests"] == 4
        and complete["charged_input_tokens"] == 1000
    )
    assert not (output / "failed.json").exists()
    assert len((output / "original/outputs.jsonl").read_text().splitlines()) == 32
    assert len((output / "larger/outputs.jsonl").read_text().splitlines()) == 8
    assert not any(b._forward_hooks for b in model.model.layers)
