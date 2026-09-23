import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "research/iterations/gated_repair"


def load(name):
    return runpy.run_path(str(HERE / (name + ".py")))


def test_gate_zero_preserves_and_feedback_changes_only_repair_positions():
    torch = pytest.importorskip("torch")
    m = load("bridge")
    model = runpy.run_path(str(ROOT / "tests/test_evidence_attention.py"))["tiny"]()
    adapter = m["Repair"](16, 4)
    x = torch.tensor([[1, 2, 3, 4]])
    native = model(x, use_cache=False).logits
    with torch.no_grad():
        adapter.up.weight.normal_(std=0.2)
    with m["scope"](model, adapter, 0.0, start=3, layer=1):
        off = model(x, use_cache=False).logits
    with m["scope"](model, adapter, 1.0, start=3, layer=1):
        on = model(x, use_cache=False).logits
        on[0, -1, 0].backward()
    assert torch.equal(off, native)
    assert torch.equal(on[:, :3], native[:, :3])
    assert not torch.equal(on[:, 3:], native[:, 3:])
    assert adapter.up.weight.grad.abs().sum() > 0
    assert all(p.grad is None and not p.requires_grad for p in model.parameters())
    h = torch.randn(1, 2, 16)
    torch.testing.assert_close(adapter(h, 0.5) - h, (adapter(h, 1.0) - h) / 2)
    for gate in (True, -1, float("nan"), 1.1):
        with pytest.raises(ValueError):
            with m["scope"](model, adapter, gate, start=3, layer=1):
                pass
    with pytest.raises(RuntimeError, match="deliberate"):
        with m["scope"](model, adapter, 0.5, start=3, layer=1):
            raise RuntimeError("deliberate")
    assert not model.model.layers[1]._forward_hooks


def test_nonzero_cached_full_agreement():
    torch = pytest.importorskip("torch")
    m = load("bridge")
    model = runpy.run_path(str(ROOT / "tests/test_evidence_attention.py"))["tiny"]()
    adapter = m["Repair"](16, 4)
    with torch.no_grad():
        adapter.up.weight.normal_(std=0.1)
        x = torch.tensor([[1, 2, 3, 4]])
        with m["scope"](model, adapter, 0.7, start=2, layer=1):
            full = model(x, use_cache=False).logits[:, -1]
            first = model(x[:, :3], use_cache=True, past_key_values=m["new_cache"](model))
            last = model(x[:, 3:], use_cache=True, past_key_values=first.past_key_values).logits[
                :, -1
            ]
    torch.testing.assert_close(full, last, atol=1e-6, rtol=1e-5)


def test_contracts_reject_leakage_preserve_exact_draft_and_keep_donors_separate():
    c = load("common")
    case = dict(id="a", task="gsm8k", split="train", prompt="Q?", origin="train/0")
    c["validate_case"](case)
    with pytest.raises(ValueError):
        c["validate_case"](case | {"answer": "42"})

    class T:
        def convert_tokens_to_ids(self, token):
            return 9

        def encode(self, text, add_special_tokens=False):
            return [8, 7]

    prefix = c["repair_prefix"](T(), [1, 2], [3, 9])
    assert prefix == [1, 2, 3, 9, 8, 7]
    cases = [
        case,
        case | {"id": "b"},
        case | {"id": "c", "task": "arc"},
        case | {"id": "d", "task": "arc"},
    ]
    assert c["donors"](cases) == {"a": "b", "b": "a", "c": "d", "d": "c"}
    with pytest.raises(ValueError):
        c["donors"]([case])
    assert c["choose_epoch"]([0.5, 0.5]) == 1
    with pytest.raises(ValueError):
        c["choose_epoch"]([float("nan")])


def test_analysis_keeps_paired_recovery_damage_and_rejects_missing_duplicate():
    c = load("common")
    cases = [dict(id=str(i), task="math") for i in range(4)]
    rows = [
        dict(id=str(i), arm=a, correct=bool(v))
        for a, vals in [("native", [1, 1, 0, 0]), ("live", [1, 0, 1, 1])]
        for i, v in enumerate(vals)
    ]
    out = c["paired"](cases, rows, "live", "native", draws=100)
    assert out["delta_pp"] == 25
    assert out["recovered"] == 2 and out["damaged"] == 1
    for bad in (rows[:-1], rows + rows[:1]):
        with pytest.raises(ValueError):
            c["paired"](cases, bad, "live", "native", draws=100)


def test_runtime_real_tiny_model_loss_and_fresh_cached_generation():
    torch = pytest.importorskip("torch")
    m = load("runtime")
    model = runpy.run_path(str(ROOT / "tests/test_evidence_attention.py"))["tiny"]()
    adapter = m["B"]["Repair"](16, 4)
    before = m["weight_digest"](model)
    loss = m["loss_for"](model, adapter, [1, 2, 3], [4, 5], 0.8, layer=1)
    loss.backward()
    torch.optim.SGD(adapter.parameters(), lr=0.1).step()
    assert m["weight_digest"](model) == before

    class T:
        def decode(self, ids, skip_special_tokens=False):
            return " ".join(map(str, ids))

    args = dict(limit=3, eos=[31], adapter=adapter, gate=0.8, layer=1)
    first = m["generate"](model, T(), [1, 2, 3], **args)
    second = m["generate"](model, T(), [1, 2, 3], **args)
    assert first["generated_token_ids"] == second["generated_token_ids"]
    assert first["prompt_token_ids"] == [1, 2, 3]
    assert first["events"][0]["positions"] == [2]
    with pytest.raises(ValueError):
        m["loss_for"](model, adapter, [1], [], 0.5, layer=1)

    def expired():
        raise TimeoutError("deadline")

    with pytest.raises(TimeoutError):
        m["generate"](model, T(), [1, 2, 3], deadline=expired, **args)
    assert not model.model.layers[1]._forward_hooks


def test_selection_excludes_prior_questions_and_cross_split_duplicates():
    p = load("prepare")
    candidates = []
    for task in ("gsm8k", "arc"):
        for split in ("train", "development", "test"):
            for i in range(500):
                question = f"{task} question {i}" if task == "gsm8k" else f"{task} {split} {i}"
                case = dict(
                    id=f"{task}/{split}/{i}", task=task, split=split, prompt=question, origin=str(i)
                )
                candidates.append((case, {"id": case["id"]}, "target", question))
    selected, excluded = p["select"](candidates, {"gsm8k question 0"})
    assert len(selected) == 640
    prompts = [c["prompt"] for c, _, _ in selected]
    assert len(prompts) == len(set(prompts))
    assert "gsm8k question 0" not in prompts
    assert excluded
