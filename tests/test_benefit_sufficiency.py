import asyncio
import copy
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "research/iterations/benefit_sufficiency"


def load(name):
    return runpy.run_path(str(HERE / f"{name}.py"))


def test_joint_questions_exclude_labels_and_ask_sufficiency_separately():
    s = load("scorer")
    view = dict(id="x", family="hotpot", question="Who won?", sources=[dict(id="s", text="A won.")])
    payload = s["payload_for"](view, "jev-1.13.0")
    assert set(payload["state"]) == {"question", "sources"}
    assert set(payload["questions"]) == {"relevance_0", "sufficient"}
    assert payload["questions"]["sufficient"]["type"] == "noul"
    with pytest.raises(ValueError):
        s["payload_for"]({**view, "reference": "A"}, "jev-1.13.0")


def test_sufficiency_branches_preserve_free_choice_and_do_not_confuse_service_failure():
    p = load("policies")
    encoded = dict(span_token_indices=[[2], [3]], abstention_token_indices=[0, 1], query_start=4)
    policy = dict(heads=[[1, 2]], strength=5, threshold=0.65)
    for value, action in [(0.1, "abstention"), (0.5, "native"), (0.9, "relevance")]:
        maps, observed = p["maps_for"](policy, encoded, [0.9, 0.1], value, "dual", 2)
        assert observed == action
        if action == "abstention":
            assert maps == {1: {2: {0: 2, 1: 2}}}
        elif action == "native":
            assert maps == {}
        else:
            assert maps == {1: {2: {2: 5}}}
    assert p["maps_for"](policy, encoded, [0.9, 0.1], 0.9, "sufficiency", 2) == ({}, "native")
    for invalid in [None, True, -0.1, float("nan")]:
        with pytest.raises(ValueError):
            p["maps_for"](policy, encoded, [0.9, 0.1], invalid, "dual", 2)


def test_predictor_learns_treatment_benefit_without_case_identity_or_labels_at_inference():
    pytest.importorskip("numpy")
    p = load("policies")
    rows = [
        dict(x=[i / 10, 0, 0, 1, 4, 0], delta=0.5 if i > 5 else -0.5, domain="synthetic")
        for i in range(12)
    ]
    model = p["fit_ridge"](rows, 1)
    assert p["predict"](model, rows[-1]["x"]) > p["predict"](model, rows[0]["x"])
    assert len(model["means"]) == 6
    changed = copy.deepcopy(rows)
    changed[0]["x"][0] = float("nan")
    with pytest.raises(ValueError):
        p["fit_ridge"](changed, 1)
    with pytest.raises(ValueError):
        p["predict"](model, [0] * 5)


def tiny():
    old = runpy.run_path(str(ROOT / "tests/test_boundary_attention.py"))
    torch, runtime, encoded, view, policy = old["tiny"]()
    # One pre-existing instruction key, disjoint from evidence keys.
    encoded = {**encoded, "abstention_token_indices": [2]}
    return torch, runtime, encoded, view, policy


def test_new_native_and_failed_paths_match_r18_exactly_and_keep_one_prefill():
    torch, old, encoded, view, policy = tiny()
    r = load("runtime")
    current = r["Runtime"](old.base, boundary=1)

    async def failure(v):
        return {"status": "failed", "key": "x"}

    reference = old.session(encoded)
    reference.extend(3)
    for gate in ({"kind": "never"}, {"kind": "always"}):
        result = asyncio.run(
            r["generate"](
                current,
                encoded,
                view,
                policy,
                failure,
                gate=gate,
                mode="dual",
                instruction_strength=2,
                limit=3,
                capture=True,
            )
        )
        assert result["final"]["token_ids"] == reference.result()["token_ids"]
        assert result["prefills"] == 1 and result["discarded_tokens"] == 0
        assert result["intervention_action"] == "native"
        for name in ("key_cache", "value_cache"):
            for actual, expected in zip(
                getattr(result["_debug"]["cache"], name),
                getattr(reference.cache, name),
                strict=True,
            ):
                torch.testing.assert_close(actual, expected, rtol=0, atol=0)


def test_low_sufficiency_changes_attention_without_replacing_generated_tokens():
    torch, old, encoded, view, policy = tiny()
    r = load("runtime")
    current = r["Runtime"](old.base, boundary=1)
    calls = []

    async def receipt(v):
        calls.append(v)
        return dict(status="complete", key="x", scores=[0.9, 0.1], sufficient=0.1)

    result = asyncio.run(
        r["generate"](
            current,
            encoded,
            view,
            policy,
            receipt,
            gate={"kind": "always"},
            mode="dual",
            instruction_strength=2,
            limit=3,
            capture=True,
        )
    )
    assert len(calls) == 1
    assert result["intervention_action"] == "abstention"
    assert result["applied_maps"] == {1: {2: {2: 2}}}
    assert result["final"]["token_ids"] == [int(x.argmax()) for x in result["_debug"]["logits"]]
    assert result["boundary"]["lower_cache_unchanged_during_wait"]
    assert result["layer_calls"] == [3, 3]
    with pytest.raises(ValueError):
        asyncio.run(
            r["generate"](
                current,
                {**encoded, "abstention_token_indices": [0]},
                view,
                policy,
                receipt,
                gate={"kind": "always"},
                mode="dual",
                instruction_strength=2,
                limit=1,
            )
        )


def test_cancellation_retains_new_runtime_ownership_until_receipt_finishes():
    _, old, encoded, view, policy = tiny()
    r = load("runtime")
    current = r["Runtime"](old.base, boundary=1)

    async def scenario():
        entered, release = asyncio.Event(), asyncio.Event()

        async def receipt(v):
            entered.set()
            await release.wait()
            return dict(status="complete", key="x", scores=[0.9, 0.1], sufficient=0.1)

        task = asyncio.create_task(
            r["generate"](
                current,
                encoded,
                view,
                policy,
                receipt,
                gate={"kind": "always"},
                mode="dual",
                instruction_strength=2,
                limit=2,
            )
        )
        await asyncio.wait_for(entered.wait(), 3)
        task.cancel()
        await asyncio.sleep(0)
        task.cancel()
        await asyncio.sleep(0)
        assert current.busy
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert not current.busy

    asyncio.run(scenario())


def test_new_authored_splits_have_disjoint_worlds_names_and_expected_balance():
    d = load("data")
    splits = {
        name: d["synthetic"](name, count)
        for name, count in [("fit", 108), ("calibration", 72), ("test", 144)]
    }
    names = []
    import re

    for split, rows in splits.items():
        assert len(rows) == (288 if split == "test" else 108 if split == "fit" else 72)
        assert sum(c["missing"] for c in rows) == len(rows) // 2
        names.append(set(re.findall(r"(?:parcel|crate|locker|task) ([a-z]{8})", str(rows))))
    assert all(not a & b for i, a in enumerate(names) for b in names[i + 1 :])


def test_one_joint_receipt_is_charged_once_and_missing_sufficiency_is_not_a_judgment(tmp_path):
    from jev_guided_decoding.experiment_budget import InputTokenBudget
    from jev_guided_decoding.types import ScorerError

    s = load("scorer")

    class Client:
        model = "jev-1.13.0"
        calls = 0

        async def _evaluate(self, payload, parse, **kwargs):
            self.calls += 1
            assert kwargs["max_attempts"] == 1
            raise ScorerError("missing sufficiency", attempts=1, usage_unknown=True)

    client = Client()
    view = dict(id="x", family="hotpot", question="Who won?", sources=[dict(id="s", text="A won.")])
    with InputTokenBudget(tmp_path / "ledger", max_usd=1, usd_per_million=0.05) as budget:
        store = s["ReceiptStore"](tmp_path / "receipts", client, budget)
        first = asyncio.run(store.get(view))
        assert first["status"] == "failed" and first["usage_unknown"]
        assert "sufficient" not in first
        assert asyncio.run(store.get(view)) == first
        assert client.calls == 1 and budget.charged_tokens > 0


def test_audit_rejects_instruction_map_token_gate_and_cache_tampering():
    _, old, encoded, view, policy = tiny()
    r, a = load("runtime"), load("analyze")
    current = r["Runtime"](old.base, boundary=1)

    async def receipt(v):
        return dict(status="complete", key="x", scores=[0.9, 0.1], sufficient=0.1)

    row = asyncio.run(
        r["generate"](
            current,
            encoded,
            view,
            policy,
            receipt,
            gate={"kind": "always"},
            mode="dual",
            instruction_strength=2,
        )
    )
    row["policy"] = policy
    manifest = dict(num_layers=2, boundary=1, eos_ids=list(old.base.eos_ids))
    a["check_output"](row, encoded, view, old.base.tokenizer, manifest)
    for kind in ("map", "token", "gate", "cache"):
        bad = copy.deepcopy(row)
        if kind == "map":
            bad["applied_maps"][1][2][2] = 5
        elif kind == "token":
            bad["final"]["token_ids"][0] += 1
        elif kind == "gate":
            bad["call_decision"] = False
        else:
            bad["final"]["tokens"][0]["cache_lengths"][0] += 1
        with pytest.raises(ValueError):
            a["check_output"](bad, encoded, view, old.base.tokenizer, manifest)
