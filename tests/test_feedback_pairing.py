import asyncio
import json
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "research/iterations/feedback_pairing"


def load(name):
    return runpy.run_path(str(HERE / f"{name}.py"))


def test_fresh_worlds_keep_the_old_task_contract_and_have_independent_answers():
    c = load("common")
    old, old_refs = c["R29"]["make_data"]()
    old_test = [x for x in old if x["split"] == "test"]
    compatible, refs = c["worlds"](96, 29003)
    assert [x["prompt"] for x in compatible] == [x["prompt"] for x in old_test]
    assert [refs[x["id"]] for x in compatible] == [old_refs[x["id"]] for x in old_test]
    fresh, answers = c["worlds"](384, 30001)
    assert len(fresh) == len({x["prompt"] for x in fresh}) == 384
    assert not {x["prompt"] for x in fresh} & {x["prompt"] for x in old}
    replay = runpy.run_path(str(HERE.parent / "structured_correction/audit.py"))["replay_reference"]
    assert all(replay(x) == answers[x["id"]] for x in fresh)
    assert all(set(x) == {"id", "task", "split", "prompt", "questions"} for x in fresh)
    with pytest.raises(ValueError):
        c["worlds"](3, 30001)


def test_probability_controls_preserve_multisets_and_keep_truth_out_of_live_paths():
    c = load("common")
    p = [0.1, 0.4, 0.9]
    left = c["signal"]("rotate_left", p)
    right = c["signal"]("rotate_right", p)
    assert sorted(left) == sorted(right) == p
    assert all(a != b for a, b in zip(p, left, strict=True))
    assert all(a != b for a, b in zip(p, right, strict=True))
    assert p == [0.1, 0.4, 0.9]
    assert c["signal"]("mean", p) == pytest.approx([sum(p) / 3] * 3)
    for mode in ("live", "mean", "rotate_left", "rotate_right", "constant", "scalar_trained"):
        assert c["signal"](mode, p, truth=[True] * 3) == c["signal"](mode, p, truth=[False] * 3)
    assert c["signal"]("type_only", p, draft="1. Office.\n2. red crate\n3. kitchen") == [1, 0, 1]
    assert c["signal"]("oracle", p, truth=[True, False, True]) == [1, 0, 1]
    for mode in ("oracle", "donor"):
        with pytest.raises(ValueError):
            c["signal"](mode, p)
    with pytest.raises(ValueError):
        c["signal"]("live", [float("nan"), 0.2, 0.3])


def test_donors_and_output_coverage_refuse_missing_duplicate_or_cross_family_pairs():
    c = load("common")
    cases, _ = c["worlds"](4, 30001)
    donors = c["donors"](cases)
    by_id = {x["id"]: x for x in cases}
    assert set(donors) == set(donors.values()) == set(by_id)
    assert all(i != d and by_id[i]["task"] == by_id[d]["task"] for i, d in donors.items())
    rows = [{"id": x["id"], "arm": a} for x in cases for a in c["arms"]([2901, 2902])]
    assert len(rows) == 80
    c["coverage"](cases, rows, [2901, 2902])
    for broken in (rows[:-1], rows + [rows[0]], rows + [{"id": "unknown", "arm": "native"}]):
        with pytest.raises(ValueError):
            c["coverage"](cases, broken, [2901, 2902])


def test_checkpoint_lineage_binds_selection_and_bytes_to_the_published_inventory(tmp_path):
    c = load("common")
    models, inventory = {}, {}
    for mode in ("structured", "scalar"):
        for seed in (2901, 2902):
            name = f"{mode}-{seed}-epoch1.safetensors"
            (tmp_path / name).write_bytes(f"fixture-{mode}-{seed}".encode())
            digest = c["sha"](tmp_path / name)
            models[f"{mode}/{seed}"] = {"epoch": 1, "file": name, "sha256": digest}
            inventory[name] = digest
    c["dump"](tmp_path / "selection.json", {"models": models})
    inventory["selection.json"] = c["sha"](tmp_path / "selection.json")
    provenance = {"original_backup_inventory": inventory}
    chosen = c["selected_checkpoints"](tmp_path, provenance)
    assert set(chosen) == set(models)
    (tmp_path / models["structured/2901"]["file"]).write_bytes(b"altered")
    with pytest.raises(ValueError, match="checkpoint"):
        c["selected_checkpoints"](tmp_path, provenance)


def test_statistics_keep_paired_case_units_and_both_interval_families():
    c = load("common")
    cases = [{"id": str(i), "task": "temporal"} for i in range(4)]
    result = c["effect"](
        cases,
        dict(zip("0123", [1, 1, 1, 0], strict=True)),
        dict(zip("0123", [1, 0, 0, 1], strict=True)),
        draws=300,
    )
    assert result["delta_pp"] == 25
    assert result["fixed"] == 2 and result["damaged"] == 1
    assert result["family_ci_pp"][0] <= result["ci95_pp"][0]
    assert result["family_ci_pp"][1] >= result["ci95_pp"][1]
    with pytest.raises(ValueError):
        c["effect"](cases, {"0": 1}, {"0": 0}, draws=300)


def test_manifest_admission_rejects_an_unbounded_or_missing_checkpoint_run(tmp_path):
    c, s = load("common"), load("study")
    cases, refs = c["worlds"]()
    c["dump"](tmp_path / "cases.json", cases)
    c["dump"](tmp_path / "references.json", refs)
    m = dict(
        sources=c["sources"](),
        planned_cases=384,
        data_seed=30001,
        files={p.name: c["sha"](p) for p in tmp_path.iterdir()},
        checkpoints={},
        api_cap_usd=100,
        max_seconds=999999,
    )
    c["dump"](tmp_path / "manifest.json", m)
    with pytest.raises(ValueError, match="contract"):
        s["verify"](tmp_path)


def test_tiny_fixed_checkpoint_execution_preserves_parameters_and_exact_feedback(tmp_path):
    pytest.importorskip("torch")
    s = load("study")
    c = load("common")
    cases, refs = c["worlds"](4, 30001)
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
            return [0.1, 0.4, 0.9]

    manifest = dict(max_seconds=60, limit=2, layer=1, rank=4, seeds=[2901])
    runner = s["R29"]["Runner"](model, Tok(), [31], manifest, tmp_path, Feedback())
    adapters = {
        (mode, 2901): runner.runtime["B"]["Repair"](16, 4).requires_grad_(False)
        for mode in ("structured", "scalar")
    }
    before = runner.runtime["weight_digest"](model)
    asyncio.run(runner.drafts(cases, refs))
    s["run_repairs"](runner, cases, adapters)
    rows = [json.loads(line) for line in (tmp_path / "outputs.jsonl").read_text().splitlines()]
    c["coverage"](cases, rows, [2901])
    assert runner.runtime["weight_digest"](model) == before
    assert all(p.grad is None for p in model.parameters())
    table = {(r["id"], r["arm"]): r for r in rows}
    first = cases[0]["id"]
    assert table[first, "rotate_left/2901"]["probabilities"] == [0.4, 0.9, 0.1]
    assert (
        table[first, "rotate_right/2901"]["prompt_token_ids"]
        == table[first, "live/2901"]["prompt_token_ids"]
    )
    assert not model.model.layers[1]._forward_hooks


def test_audit_receipts_reject_changed_drafts_duplicates_and_unresolved_charges():
    import copy

    a, c = load("audit"), load("common")
    cases, _ = c["worlds"](4, 30001)
    natives, requests, responses, ledger = {}, [], [], []
    for i, case in enumerate(cases):
        native = {"text": "1. office\n2. kitchen\n3. garage", "at": "a"}
        natives[case["id"]] = native
        reservation = f"r{i}"
        requests.append(
            dict(
                id=case["id"],
                payload=c["R29"]["payload"](case, native["text"]),
                reservation=reservation,
                at="b",
            )
        )
        raw = dict(
            model="jev-1.13.0",
            answers={f"q{k}": dict(type="noul", noul=0.5) for k in (1, 2, 3)},
            usage=dict(input_tokens=100, output_tokens=9),
        )
        responses.append(
            dict(
                id=case["id"],
                probabilities=[0.5] * 3,
                raw=raw,
                model="jev-1.13.0",
                attempts=1,
                input_tokens=100,
                output_tokens=9,
                seconds=0.1,
                reservation=reservation,
                at="c",
            )
        )
        ledger.extend(
            [
                dict(event="reserve", id=reservation),
                dict(event="settle", id=reservation, input_tokens=100),
            ]
        )
    assert a["check_receipts"](cases, natives, requests, responses, ledger) == 400
    bad = copy.deepcopy(requests)
    bad[0]["payload"]["state"]["response"] = "different draft"
    with pytest.raises(ValueError):
        a["check_receipts"](cases, natives, bad, responses, ledger)
    with pytest.raises(ValueError):
        a["check_receipts"](cases, natives, requests, responses + responses[:1], ledger)
    with pytest.raises(ValueError):
        a["check_receipts"](cases, natives, requests, responses, ledger[:-1])


def test_audit_detects_wrong_pairing_and_changed_final_token_provenance():
    import copy

    a = load("audit")

    class Tok:
        def decode(self, ids, skip_special_tokens=False):
            return "room" if ids == [3] else "changed"

    row = dict(
        prompt_token_ids=[1, 2],
        generated_token_ids=[3, 31],
        text="room",
        finish_reason="eos",
        probabilities=[0.4, 0.9, 0.1],
        events=[dict(layer=19, positions=[1, 2], feedback=[0.4, 0.9, 0.1])],
    )
    a["check_generation"](row, [1, 2], [0.4, 0.9, 0.1], Tok(), 31, 128, 19)
    with pytest.raises(ValueError):
        a["check_generation"](row, [1, 2], [0.1, 0.4, 0.9], Tok(), 31, 128, 19)
    broken = copy.deepcopy(row)
    broken["generated_token_ids"] = [4, 31]
    with pytest.raises(ValueError):
        a["check_generation"](broken, [1, 2], [0.4, 0.9, 0.1], Tok(), 31, 128, 19)
    broken = copy.deepcopy(row)
    broken["events"][0]["positions"] = [0, 1]
    with pytest.raises(ValueError):
        a["check_generation"](broken, [1, 2], [0.4, 0.9, 0.1], Tok(), 31, 128, 19)
