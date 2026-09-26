import asyncio
import json
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "research/iterations/contextual_memory"


def test_existing_native_evidence_prevents_replay_after_partial_preparation():
    pytest.importorskip("torch")
    r = runpy.run_path(str(HERE / "runtime.py"))
    runner = object.__new__(r["Runner"])
    runner.prepared = {}
    runner.rows = [dict(id="prior", arm="native")]
    runner.deadline = lambda: None
    case = dict(
        id="prior",
        task="temporal",
        split="train",
        prompt="one two three",
        questions=["one", "two", "three"],
    )
    with pytest.raises(ValueError, match="Duplicate"):
        asyncio.run(runner.drafts([case], {}))


@pytest.mark.parametrize("form,output_count,test_count", [("scalar", 80, 22), ("both", 128, 38)])
def test_serial_candidate_pipeline_binds_memory_and_all_controls(
    tmp_path, form, output_count, test_count
):
    torch = pytest.importorskip("torch")
    from transformers import GraniteMoeHybridConfig, GraniteMoeHybridForCausalLM

    r = runpy.run_path(str(HERE / "runtime.py"))
    config = GraniteMoeHybridConfig(
        vocab_size=256,
        hidden_size=16,
        intermediate_size=32,
        num_hidden_layers=2,
        num_attention_heads=4,
        num_key_value_heads=2,
        num_local_experts=0,
        num_experts_per_tok=0,
        layer_types=["attention", "attention"],
        attention_dropout=0.0,
        shared_intermediate_size=32,
        mamba_n_heads=4,
    )
    config._attn_implementation = "sdpa"
    torch.manual_seed(321)
    model = GraniteMoeHybridForCausalLM(config).eval().requires_grad_(False)

    class Tok:
        def encode(self, text, **kwargs):
            return list(text.encode())

        def decode(self, ids, **kwargs):
            return bytes(ids).decode(errors="replace")

        def convert_tokens_to_ids(self, text):
            return 0

        def apply_chat_template(self, messages, **kwargs):
            return list((messages[0]["content"] + "\nANSWER:\n").encode())

    class Feedback:
        def __init__(self):
            self.seen = []

        async def score(self, case, draft):
            assert set(case) == {"id", "task", "split", "prompt", "questions"}
            self.seen.append((case["id"], draft))
            return [0.1 + int(case["id"][-1]) * 0.1, 0.7, 0.9]

    cases = [
        dict(
            id=f"c{i}",
            task="temporal",
            split=split,
            prompt="Where key?\nWhere coin?\nWhere hat?",
            questions=["Where key?", "Where coin?", "Where hat?"],
        )
        for i, split in enumerate(["train"] * 2 + ["development"] * 2 + ["test"] * 2)
    ]
    refs = {c["id"]: ["hall", "office", "kitchen"] for c in cases}
    manifest = dict(
        informative=form,
        seeds=[3101, 3102],
        epochs=2,
        lr=0.001,
        accumulate=2,
        rank=4,
        layer=1,
        limit=3,
        max_seconds=60,
    )
    feedback = Feedback()
    runner = r["Runner"](model, Tok(), [0], manifest, tmp_path, feedback)
    before = runner.runtime["weight_digest"](model)
    asyncio.run(runner.drafts(cases[:4], refs))
    adapters = runner.train(cases[:2], cases[2:4], refs)
    asyncio.run(runner.drafts(cases[4:], refs))
    runner.test(cases[4:], adapters)
    assert len(runner.rows) == output_count
    assert len(feedback.seen) == 6
    assert runner.runtime["weight_digest"](model) == before
    memories = [json.loads(s) for s in (tmp_path / "memory-records.jsonl").read_text().splitlines()]
    assert len(memories) == 6 and all((tmp_path / m["file"]).is_file() for m in memories)
    for case in cases[4:]:
        rows = [row for row in runner.rows if row["id"] == case["id"]]
        assert len(rows) == test_count and len({row["arm"] for row in rows}) == test_count
        item = runner.prepared[case["id"]]
        for row in rows:
            if row["arm"] in ("native", "blind"):
                assert row["probabilities"] is None and not row["events"]
                continue
            if row["arm"].startswith("oracle/"):
                assert row["probabilities"] == [0.0] * 3
            if row["arm"].startswith(
                ("same_constant/", "embedding-constant/", "contextual-constant/")
            ):
                assert row["probabilities"] == [0.5] * 3
            assert row["prompt_token_ids"] == item["prompt"]
            assert row["events"][0]["positions"] == [len(item["prompt"]) - 1]
    assert all(p.grad is None for p in model.parameters())
    bindings = [
        json.loads(s) for s in (tmp_path / "generation-bindings.jsonl").read_text().splitlines()
    ]
    assert len(bindings) == len(runner.rows)
    digest = runpy.run_path(str(HERE / "provenance.py"))["tensor_digest"]
    for binding in bindings:
        if binding["arm"] in ("native", "blind"):
            assert binding["memory_digest"] is binding["adapter_digest"] is None
        elif binding["arm"].startswith(("same_constant/", "donor/", "oracle/")):
            name, seed = binding["arm"].split("/")[1:]
            kind = name.split("-")[0]
            item = runner.prepared[binding["id"]]
            assert binding["memory_digest"] == digest(item["memories"][kind])
            assert binding["adapter_digest"] == runner.runtime["weight_digest"](
                adapters[name, int(seed)]
            )
    steps = [json.loads(s) for s in (tmp_path / "training-steps.jsonl").read_text().splitlines()]
    for step in steps:
        item = runner.prepared[step["id"]]
        assert step["memory_digest"] == digest(item["memories"][step["memory"]])
        assert len(step["probabilities"]) == 3
    checks = runpy.run_path(str(HERE / "checks.py"))
    natives = {row["id"]: row for row in runner.rows if row["arm"] == "native"}
    checked = checks["check_memories"](
        cases, natives, memories, tmp_path, Tok(), eos=0, width=16, layer=1
    )
    assert checked["count"] == 6
    assert checked["processed_tokens"] == sum(m["processed_tokens"] for m in memories)
    targets = json.loads((tmp_path / "training-targets.json").read_text())
    epochs = [json.loads(s) for s in (tmp_path / "epochs.jsonl").read_text().splitlines()]
    selection = json.loads((tmp_path / "selection.json").read_text())
    receipts = {ident: dict(probabilities=item["p"]) for ident, item in runner.prepared.items()}
    contract = manifest | dict(specs=runner.specs)

    def inspect_training(candidate_steps=steps, candidate_selection=selection):
        return checks["check_training"](
            cases,
            refs,
            natives,
            runner.rows,
            candidate_steps,
            targets,
            epochs,
            candidate_selection,
            checked["digests"],
            receipts,
            tmp_path,
            Tok(),
            contract,
            eos=0,
            width=16,
        )

    trained = inspect_training()
    assert trained["examples"] == len(steps)
    assert trained["updates"] == len(steps) // manifest["accumulate"]
    changed = [dict(s) for s in steps]
    changed[0]["probabilities"] = [0.123] * 3
    with pytest.raises(ValueError, match="training"):
        inspect_training(candidate_steps=changed)
    changed = [dict(s) for s in steps]
    changed[0]["memory_digest"] = "substituted"
    with pytest.raises(ValueError, match="training"):
        inspect_training(candidate_steps=changed)
    with pytest.raises(ValueError, match="training"):
        inspect_training(candidate_steps=steps[1:])
    changed_selection = json.loads(json.dumps(selection))
    first = next(iter(changed_selection["models"].values()))
    first["epoch"] = 3 - first["epoch"]
    with pytest.raises(ValueError, match="selection"):
        inspect_training(candidate_selection=changed_selection)
    admission = runpy.run_path(str(HERE / "admission.py"))["admission"]
    report = admission(model, Tok(), cases[0], natives["c0"], [0], layer=1, rank=4)
    assert report["passed"] and report["initial_identity"] and report["off_identity"]
    assert report["backbone_gradients_absent"] and report["cache_argmax_equal"]
    assert report["contextual_memory_shape"] == [3, 16]
    assert runner.runtime["weight_digest"](model) == before
    audit_records = runpy.run_path(str(HERE / "audit.py"))["audit_records"]
    audited = audit_records(
        cases, refs, runner.rows, receipts, tmp_path, Tok(), contract, eos=0, width=16
    )
    assert audited["outputs"] == output_count and audited["memory_extractions"] == 6
    assert audited["training_steps"] == len(steps)
    assert audited["test_cases"] == 2
    changed_rows = [dict(row) for row in runner.rows]
    changed_rows[-1]["prompt_token_ids"] = [255]
    with pytest.raises(ValueError, match="token"):
        audit_records(
            cases, refs, changed_rows, receipts, tmp_path, Tok(), contract, eos=0, width=16
        )
    corrupted = [dict(row) for row in memories]
    corrupted[0]["input_token_ids"] = [255]
    with pytest.raises(ValueError, match="token"):
        checks["check_memories"](
            cases, natives, corrupted, tmp_path, Tok(), eos=0, width=16, layer=1
        )
    with pytest.raises(ValueError, match="coverage"):
        checks["check_memories"](
            cases, natives, memories[:-1], tmp_path, Tok(), eos=0, width=16, layer=1
        )
