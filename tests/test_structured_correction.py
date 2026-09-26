import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "research/iterations/structured_correction"


def load(name):
    return runpy.run_path(str(HERE / (name + ".py")))


def test_worlds_are_disjoint_and_oracle_checks_partial_duplicate_and_extra_answers():
    c = load("common")
    cases, refs = c["make_data"]()
    assert len(cases) == 256
    assert len({x["prompt"] for x in cases}) == 256
    assert len({x["id"] for x in cases}) == 256
    assert {s: sum(x["split"] == s for x in cases) for s in ("train", "development", "test")} == {
        "train": 128,
        "development": 32,
        "test": 96,
    }
    for case in cases:
        ref = refs[case["id"]]
        assert c["grade"](c["target"](ref), ref)["correct"]
        assert c["grade"](c["target"](ref).upper(), ref)["correct"]
        assert not c["grade"](c["target"](ref) + "\n1. elsewhere", ref)["correct"]
        assert not c["grade"]("", ref)["correct"]
        assert not c["grade"]("1. " + ref[0], ref)["correct"]
        payload = c["payload"](case, "1. elsewhere")
        assert len(payload["questions"]) == 3
        assert set(payload["state"]) == {"problem", "response"}
        assert "reference" not in payload["state"]
        with pytest.raises(ValueError):
            c["payload"](case | {"answer": ref}, "draft")
    assert c["grade"]("Explanation\n" + c["target"](refs[cases[0]["id"]]), refs[cases[0]["id"]])[
        "correct"
    ]


def test_preservation_targets_and_probability_controls_never_leak_test_targets():
    c = load("common")
    assert c["target_ids"]("train", True, [3, 4, 9], [8], 9) == [3, 4, 9]
    assert c["target_ids"]("train", True, [3, 4], [8], 9) == [3, 4]
    assert c["target_ids"]("train", False, [3, 4], [8], 9) == [8, 9]
    with pytest.raises(ValueError):
        c["target_ids"]("test", False, [1], [2], 9)
    assert c["signal"]("scalar", [0.2, 0.5, 0.8]) == [0.5] * 3
    assert c["signal"]("constant", [0.2, 0.5, 0.8]) == [0.5] * 3
    with pytest.raises(ValueError):
        c["signal"]("structured", [float("nan"), 0.5, 0.5])
    assert c["choose_threshold"]([0.2, 0.8], [True, False], [False, False]) == 0
    assert c["choose_threshold"]([0.2, 0.8], [False, True], [True, False]) == 0.4


def test_internal_memory_changes_only_repair_positions_and_has_exact_off_state():
    torch = pytest.importorskip("torch")
    b = load("bridge")
    model = runpy.run_path(str(ROOT / "tests/test_evidence_attention.py"))["tiny"]()
    adapter = b["Repair"](16, 4)
    memory = torch.randn(3, 16)
    x = torch.tensor([[1, 2, 3, 4]])
    native = model(x, use_cache=False).logits
    with b["scope"](model, adapter, memory, [0.1, 0.8, 0.5], start=3, layer=1):
        zero = model(x, use_cache=False).logits
    assert torch.equal(zero, native)
    with torch.no_grad():
        adapter.up.weight.normal_(std=0.2)
    with b["scope"](model, adapter, memory, [1, 1, 1], start=3, layer=1):
        off = model(x, use_cache=False).logits
    assert torch.equal(off, native)
    with b["scope"](model, adapter, memory, [0.1, 0.8, 0.5], start=3, layer=1):
        live = model(x, use_cache=False).logits
        live[0, -1, 0].backward()
    with b["scope"](model, adapter, memory, [0.8, 0.1, 0.5], start=3, layer=1):
        swapped = model(x, use_cache=False).logits
    assert torch.equal(live[:, :3], native[:, :3])
    assert not torch.equal(live[:, 3:], swapped[:, 3:])
    assert adapter.up.weight.grad.abs().sum() > 0
    assert all(p.grad is None and not p.requires_grad for p in model.parameters())
    with pytest.raises(RuntimeError, match="active"):
        with b["scope"](model, adapter, memory, [0.5] * 3, start=3, layer=1):
            with b["scope"](model, adapter, memory, [0.5] * 3, start=3, layer=1):
                pass
    assert not model.model.layers[1]._forward_hooks


def test_cached_generation_matches_full_prefix_with_feedback_and_cleans_up():
    torch = pytest.importorskip("torch")
    b = load("bridge")
    model = runpy.run_path(str(ROOT / "tests/test_evidence_attention.py"))["tiny"]()
    adapter = b["Repair"](16, 4)
    memory = torch.randn(3, 16)
    with torch.no_grad():
        adapter.up.weight.normal_(std=0.1)
        x = torch.tensor([[1, 2, 3, 4]])
        with b["scope"](model, adapter, memory, [0.2, 0.7, 0.4], start=2, layer=1):
            full = model(x, use_cache=False).logits[:, -1]
            first = model(x[:, :3], use_cache=True, past_key_values=b["new_cache"](model))
            last = model(x[:, 3:], use_cache=True, past_key_values=first.past_key_values).logits[
                :, -1
            ]
    torch.testing.assert_close(full, last, atol=1e-6, rtol=1e-5)
    with pytest.raises(ValueError):
        with b["scope"](model, adapter, memory, [float("nan")] * 3, start=3, layer=1):
            pass
    with pytest.raises(TimeoutError):
        with b["scope"](model, adapter, memory, [0.5] * 3, start=3, layer=1):
            raise TimeoutError()
    assert not model.model.layers[1]._forward_hooks


def test_runtime_trains_only_branch_preserves_prompt_and_stops_on_deadline():
    torch = pytest.importorskip("torch")
    r = load("runtime")
    model = runpy.run_path(str(ROOT / "tests/test_evidence_attention.py"))["tiny"]()
    adapter = r["B"]["Repair"](16, 4)
    memory = torch.randn(3, 16)
    before = r["weight_digest"](model)
    loss = r["loss_for"](model, adapter, [1, 2, 3], [4, 5], memory, [0.2, 0.5, 0.9], layer=1)
    loss.backward()
    torch.optim.SGD(adapter.parameters(), lr=0.1).step()
    assert before == r["weight_digest"](model)

    class Tok:
        def decode(self, ids, skip_special_tokens=False):
            return " ".join(map(str, ids))

    row = r["generate"](
        model,
        Tok(),
        [1, 2, 3],
        limit=3,
        eos=[31],
        adapter=adapter,
        memory=memory,
        probabilities=[0.2, 0.5, 0.9],
        layer=1,
    )
    assert row["prompt_token_ids"] == [1, 2, 3]
    assert row["events"][0]["feedback"] == [0.2, 0.5, 0.9]
    assert row["events"][0]["positions"] == [2]

    def expired():
        raise TimeoutError("deadline")

    with pytest.raises(TimeoutError):
        r["generate"](
            model,
            Tok(),
            [1, 2],
            limit=1,
            eos=[31],
            adapter=adapter,
            memory=memory,
            probabilities=[0.5] * 3,
            layer=1,
            deadline=expired,
        )
    assert not model.model.layers[1]._forward_hooks


def test_feedback_reserves_before_dispatch_and_never_repeats_unknown_call(tmp_path):
    import asyncio

    from jev_guided_decoding.experiment_budget import InputTokenBudget

    f = load("feedback")
    case = load("common")["make_data"]()[0][0]

    class Scorer:
        calls = 0

        async def _evaluate(self, payload, parse_answers, **kwargs):
            self.calls += 1
            assert kwargs["max_attempts"] == 1
            assert budget.unresolved
            raise TimeoutError("ambiguous delivery")

    scorer = Scorer()
    with InputTokenBudget(tmp_path / "budget.jsonl", max_usd=0.02) as budget:
        client = f["Feedback"](scorer, budget, tmp_path, delay=0)
        with pytest.raises(TimeoutError):
            asyncio.run(client.score(case, "draft"))
        assert len(budget.unresolved) == 1
        with pytest.raises(ValueError, match="Duplicate"):
            asyncio.run(client.score(case, "draft"))
        assert scorer.calls == 1


def test_independent_reference_replay_tracks_transfers_and_container_motion():
    a = load("audit")
    case = {
        "prompt": "Initially, the key is in the red crate.\n"
        "Initially, the red crate is in the office.\n"
        "Initially, the blue crate is in the kitchen.\n"
        "Event 1: the key is moved to the blue crate.\n"
        "Event 2: the red crate is moved to the garage.\n"
        "Event 3: the blue crate is moved to the attic.",
        "questions": ["Which room contains the key after the final event?"] * 3,
    }
    assert a["replay_reference"](case) == ["attic"] * 3
    cases, refs = load("common")["make_data"]()
    assert all(a["replay_reference"](c) == refs[c["id"]] for c in cases)


def test_paired_summary_counts_damage_and_rejects_incomplete_results():
    a = load("audit")
    cases = [{"id": str(i), "task": "temporal"} for i in range(4)]
    grades = {
        "native": {str(i): float(v) for i, v in enumerate([1, 1, 0, 0])},
        "structured": {str(i): float(v) for i, v in enumerate([1, 0, 1, 1])},
    }
    out = a["contrast"](cases, grades["structured"], grades["native"], draws=100)
    assert out["delta_pp"] == 25
    assert out["fixed"] == 2 and out["damaged"] == 1
    with pytest.raises(ValueError):
        a["contrast"](cases, {"0": 1}, grades["native"], draws=100)


def test_tiny_training_pipeline_writes_selection_and_exact_preservation_targets(tmp_path):
    import asyncio
    import json

    pytest.importorskip("torch")
    s = load("study")
    cases, refs = load("common")["make_data"]()
    train, dev = cases[:8], cases[128:130]
    model = runpy.run_path(str(ROOT / "tests/test_evidence_attention.py"))["tiny"]()

    class Tok:
        def apply_chat_template(self, *args, **kwargs):
            return [1, 2, 3]

        def convert_tokens_to_ids(self, token):
            return 31

        def encode(self, text, add_special_tokens=False):
            return [4, 5]

        def decode(self, ids, skip_special_tokens=False):
            return " ".join(map(str, ids))

    class Feedback:
        async def score(self, case, draft):
            return [0.2, 0.5, 0.8]

    manifest = dict(
        max_seconds=60,
        limit=3,
        layer=1,
        rank=4,
        seeds=[2901],
        modes=["constant", "structured"],
        epochs=1,
        lr=0.001,
        accumulate=8,
    )
    runner = s["Runner"](model, Tok(), [31], manifest, tmp_path, Feedback())
    asyncio.run(runner.drafts(train + dev, refs))
    # Exercise preservation separately from ordinary incorrect native drafts.
    first = runner.prepared[train[0]["id"]]
    first["grade"]["correct"] = True
    adapters = runner.train(train, dev, refs)
    targets = json.loads((tmp_path / "training-targets.json").read_text())
    assert targets[train[0]["id"]]["target_ids"] == first["native"]["generated_token_ids"]
    selection = json.loads((tmp_path / "selection.json").read_text())
    assert selection["models"]["structured/2901"]["epoch"] == 1
    assert set(adapters) == {("constant", 2901), ("structured", 2901)}
    assert all(p.grad is None for p in model.parameters())
