import json
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load():
    return runpy.run_path(str(ROOT / "research/iterations/contextual_memory/training.py"))


def test_matched_training_owns_only_adapter_weights_and_preserves_targets(tmp_path):
    torch = pytest.importorskip("torch")
    from safetensors.torch import load_file

    r = runpy.run_path(str(ROOT / "research/iterations/structured_correction/runtime.py"))
    model = runpy.run_path(str(ROOT / "tests/test_evidence_attention.py"))["tiny"]()

    class Tok:
        def encode(self, text, **kwargs):
            return [4, 5]

        def convert_tokens_to_ids(self, text):
            return 31

    class Runner:
        def __init__(self):
            self.model, self.tok, self.output = model, Tok(), tmp_path
            self.prepared = {
                ident: dict(
                    native=dict(generated_token_ids=[6, 7, 31]),
                    grade=dict(correct=ident == "good", slots=[ident == "good"] * 3),
                    p=[0.2, 0.8, 0.4],
                    prompt=[1, 2, 3],
                    memories=dict(embedding=torch.ones(3, 16), contextual=torch.randn(3, 16)),
                )
                for ident in ("good", "wrong", "dev")
            }
            self.seen = []

        def deadline(self):
            pass

        def answer(self, case, arm, prompt, **kwargs):
            self.seen.append((arm, kwargs["memory"].clone(), kwargs["probabilities"]))
            # An independently specified development tie must select epoch one.
            return dict(text="1. wrong\n2. wrong\n3. wrong")

    runner = Runner()
    before = r["weight_digest"](model)
    train = [dict(id=i, split="train") for i in ("good", "wrong")]
    dev = [dict(id="dev", split="development")]
    specs = [
        ("embedding-scalar", "embedding", "scalar"),
        ("contextual-scalar", "contextual", "scalar"),
    ]
    adapters = load()["train"](
        runner,
        train,
        dev,
        {i: ["hall"] * 3 for i in ("good", "wrong", "dev")},
        specs=specs,
        seeds=[3101],
        epochs=2,
        accumulate=2,
        rank=4,
        layer=1,
    )
    assert r["weight_digest"](model) == before
    assert all(p.grad is None and not p.requires_grad for p in model.parameters())
    selection = json.loads((tmp_path / "selection.json").read_text())["models"]
    assert all(v["epoch"] == 1 for v in selection.values())
    assert len((tmp_path / "training-steps.jsonl").read_text().splitlines()) == 8
    targets = json.loads((tmp_path / "training-targets.json").read_text())
    assert targets["good"]["target_ids"] == [6, 7, 31]
    assert targets["wrong"]["target_ids"] == [4, 5, 31]
    initial = [
        load_file(str(tmp_path / f"{name}-3101-initial.safetensors")) for name, _, _ in specs
    ]
    assert all(torch.equal(initial[0][k], initial[1][k]) for k in initial[0])
    for (name, seed), adapter in adapters.items():
        selected = load_file(str(tmp_path / selection[f"{name}/{seed}"]["file"]))
        assert all(torch.equal(v, selected[k]) for k, v in adapter.state_dict().items())
        assert not any(p.requires_grad for p in adapter.parameters())
    for arm, memory, p in runner.seen:
        kind = arm.split("/")[1].split("-")[0]
        assert torch.equal(memory, runner.prepared["dev"]["memories"][kind])
        assert p == pytest.approx([1.4 / 3] * 3)


def test_training_rejects_test_examples_and_ambiguous_conditions_before_work(tmp_path):
    pytest.importorskip("torch")
    m = load()

    class Runner:
        output = tmp_path

        def deadline(self):
            pytest.fail("Invalid training admitted model work")

    kwargs = dict(specs=[("embedding-scalar", "embedding", "scalar")], seeds=[3101], epochs=2)
    with pytest.raises(ValueError, match="split"):
        m["train"](Runner(), [dict(id="x", split="test")], [], {}, **kwargs)
    with pytest.raises(ValueError, match="conditions"):
        m["train"](
            Runner(),
            [dict(id="x", split="train")],
            [dict(id="y", split="development")],
            {},
            **(kwargs | {"specs": kwargs["specs"] * 2}),
        )


def test_training_never_overwrites_an_earlier_attempt(tmp_path):
    pytest.importorskip("torch")

    class Runner:
        output = tmp_path

    marker = tmp_path / "training-targets.json"
    marker.write_text("earlier evidence")
    with pytest.raises(FileExistsError):
        load()["train"](
            Runner(),
            [dict(id="x", split="train")],
            [dict(id="y", split="development")],
            {"x": ["hall"] * 3, "y": ["hall"] * 3},
            specs=[("embedding-scalar", "embedding", "scalar")],
            seeds=[3101],
            accumulate=1,
        )
    assert marker.read_text() == "earlier evidence"
