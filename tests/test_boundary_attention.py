import asyncio
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "research/iterations/boundary_attention"


def load(name):
    return runpy.run_path(str(HERE / f"{name}.py"))


def tiny():
    torch = pytest.importorskip("torch")
    old = runpy.run_path(str(ROOT / "tests/test_selective_attention.py"))
    runtime, encoded, view, policy = old["tiny_runtime"]()
    policy = {**policy, "heads": [[1, 2]], "mode": "additive", "envelope": "all"}
    return torch, runtime, encoded, view, policy


def test_features_reconstruct_native_gqa_attention_without_full_query_tensor():
    torch = pytest.importorskip("torch")
    m = load("features")
    q = torch.zeros(1, 4, 3, 2)
    k = torch.zeros(1, 2, 3, 2)
    stats = m["observe"](q, k, None, [[0], [1]], 1.0)
    assert stats["features"]["evidence_mass"] == pytest.approx(2 / 3)
    assert stats["features"]["source_entropy"] == pytest.approx(1.0)
    assert stats["features"]["head_disagreement"] == pytest.approx(0.0, abs=1e-7)
    assert stats["query_rows_computed"] == 1
    torch.testing.assert_close(torch.tensor(stats["head_source_mass"]), torch.full((4, 2), 1 / 3))
    assert m["reconstruct"](stats["head_source_mass"]) == stats["features"]
    mask = torch.tensor([[[[True, False, True]]]])
    blocked = m["observe"](q, k, mask, [[0], [1]], 1.0)
    assert blocked["features"]["evidence_mass"] == pytest.approx(0.5)
    assert blocked["features"]["source_entropy"] == pytest.approx(0.0)
    with pytest.raises(ValueError):
        m["reconstruct"]([[float("nan"), 0.3]])


def test_once_only_boundary_preserves_full_logits_and_every_layer_cache():
    torch, old, encoded, view, policy = tiny()
    r = load("runtime")
    current = r["Runtime"](old.base, boundary=1)
    calls = []

    async def receipt(v):
        calls.append(v)
        return {"status": "complete", "key": "x", "scores": [0.9, 0.1]}

    async def forbidden(v):
        raise AssertionError("No-call branch contacted provider")

    for guided in (False, True):
        reference = old.session(encoded)
        reference_logits = []
        handle = old.base.model.register_forward_hook(
            lambda model, args, output, target=reference_logits: target.append(
                output.logits[0, -1].detach().clone()
            )
        )
        reference.extend(5, policy if guided else None, [0.9, 0.1] if guided else None)
        handle.remove()
        result = asyncio.run(
            r["generate"](
                current,
                encoded,
                view,
                policy,
                receipt if guided else forbidden,
                gate={"kind": "always" if guided else "never"},
                limit=5,
                capture=True,
            )
        )
        assert result["final"]["token_ids"] == reference.result()["token_ids"]
        assert result["model_forwards"] == 5
        assert result["prefills"] == 1 and result["discarded_tokens"] == 0
        assert result["boundary"]["lower_cache_lengths"] == [4]
        assert result["boundary"]["upper_cache_lengths"] == [0]
        assert result["boundary"]["lower_cache_unchanged_during_wait"]
        assert result["layer_token_counts"] == [8, 8]
        for name in ("key_cache", "value_cache"):
            for x, y in zip(
                getattr(result["_debug"]["cache"], name),
                getattr(reference.cache, name),
                strict=True,
            ):
                torch.testing.assert_close(x, y, atol=0, rtol=0)
        for observed, expected in zip(result["_debug"]["logits"], reference_logits, strict=True):
            torch.testing.assert_close(observed, expected, atol=0, rtol=0)
        assert result["boundary"]["decisions"] == 1
    assert len(calls) == 1 and calls[0] == view


def test_failed_receipt_continues_same_prefill_and_malformed_success_is_rejected():
    torch, old, encoded, view, policy = tiny()
    r = load("runtime")
    current = r["Runtime"](old.base, boundary=1)

    async def failure(v):
        return {"status": "failed", "key": "failure", "usage_unknown": True}

    native = old.session(encoded)
    native.extend(3)
    result = asyncio.run(
        r["generate"](current, encoded, view, policy, failure, gate={"kind": "always"}, limit=3)
    )
    assert result["provider_status"] == "failed_fallback"
    assert result["logical_jev_calls"] == 1 and not result["guided_path"]
    assert result["final"]["token_ids"] == native.result()["token_ids"]
    assert result["prefills"] == 1 and result["model_forwards"] == 3

    async def bad(v):
        return {"status": "complete", "key": "bad", "scores": [float("nan"), 0.2]}

    with pytest.raises(ValueError, match="scores"):
        asyncio.run(
            r["generate"](current, encoded, view, policy, bad, gate={"kind": "always"}, limit=1)
        )
    assert not current.busy
    result = asyncio.run(
        r["generate"](current, encoded, view, policy, failure, gate={"kind": "never"}, limit=1)
    )
    assert result["logical_jev_calls"] == 0


def test_cancellation_drains_worker_and_restores_dispatch_before_reuse():
    torch, old, encoded, view, policy = tiny()
    from transformers.modeling_utils import ALL_ATTENTION_FUNCTIONS

    original = ALL_ATTENTION_FUNCTIONS["sdpa"]
    r = load("runtime")
    current = r["Runtime"](old.base, boundary=1)

    async def scenario():
        entered, release = asyncio.Event(), asyncio.Event()

        async def receipt(v):
            entered.set()
            await release.wait()
            return {"status": "complete", "key": "one", "scores": [0.9, 0.1]}

        task = asyncio.create_task(
            r["generate"](current, encoded, view, policy, receipt, gate={"kind": "always"}, limit=3)
        )
        await asyncio.wait_for(entered.wait(), 3)
        task.cancel()
        await asyncio.sleep(0)
        assert current.busy
        with pytest.raises(RuntimeError, match="active"):
            await r["generate"](
                current, encoded, view, policy, receipt, gate={"kind": "never"}, limit=1
            )
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert not current.busy
        assert ALL_ATTENTION_FUNCTIONS["sdpa"] is original

    asyncio.run(scenario())


def test_early_eos_and_boundary_after_first_controlled_layer_rejected():
    torch, old, encoded, view, policy = tiny()
    r = load("runtime")
    current = r["Runtime"](old.base, boundary=1)
    first = old.session(encoded)
    first.extend(1)
    old.base.eos_ids.add(first.tokens[0]["token_id"])

    async def forbidden(v):
        raise AssertionError

    result = asyncio.run(
        r["generate"](current, encoded, view, policy, forbidden, gate={"kind": "never"})
    )
    assert result["model_forwards"] == 1 and result["final"]["finish_reason"] == "eos"
    with pytest.raises(ValueError, match="boundary"):
        asyncio.run(
            r["generate"](
                current,
                encoded,
                view,
                {**policy, "heads": [[0, 1]]},
                forbidden,
                gate={"kind": "never"},
            )
        )


def test_repeated_cancellation_keeps_ownership_until_provider_worker_drains():
    torch, old, encoded, view, policy = tiny()
    r = load("runtime")
    current = r["Runtime"](old.base, boundary=1)

    async def scenario():
        entered, release = asyncio.Event(), asyncio.Event()

        async def receipt(v):
            entered.set()
            await release.wait()
            return {"status": "complete", "key": "one", "scores": [0.9, 0.1]}

        task = asyncio.create_task(
            r["generate"](current, encoded, view, policy, receipt, gate={"kind": "always"}, limit=1)
        )
        await asyncio.wait_for(entered.wait(), 3)
        task.cancel()
        await asyncio.sleep(0)
        task.cancel()
        await asyncio.sleep(0)
        still_owned = current.busy
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await task
        await asyncio.sleep(0.01)
        assert still_owned, "Repeated cancellation released an active model worker"

    asyncio.run(scenario())


def test_boundary_scope_rejects_nested_legacy_attention_before_dispatch_changes():
    torch, old, encoded, view, policy = tiny()
    r = load("runtime")
    current = r["Runtime"](old.base, boundary=1)

    async def receipt(v):
        with pytest.raises(RuntimeError, match="active"):
            with old.hook.apply(
                encoded["input_ids"],
                query_start=3,
                source_keys=[0, 1],
                maps={(1, 2): {0: 2.0}},
                mode="additive",
            ):
                pass
        return {"status": "complete", "key": "one", "scores": [0.9, 0.1]}

    asyncio.run(
        r["generate"](current, encoded, view, policy, receipt, gate={"kind": "always"}, limit=1)
    )


def test_recorded_boundary_output_survives_json_and_rejects_work_or_cache_tampering():
    import copy
    import json

    torch, old, encoded, view, policy = tiny()
    r, s, a = load("runtime"), load("study"), load("analyze")
    current = r["Runtime"](old.base, boundary=1)
    old.base.tokenizer.eos_token_id = -1

    async def success(v):
        return {"status": "complete", "key": "one", "scores": [0.9, 0.1]}

    with s["Profile"](old.base) as profile:
        row = asyncio.run(
            r["generate"](current, encoded, view, policy, success, gate={"kind": "always"})
        )
    row.update(
        arm="boundary_always", case_id=view["id"], policy=policy, forward_events=profile.events
    )
    row = json.loads(json.dumps(row))
    manifest = {"num_layers": 2, "boundary": 1}
    a["check_output"](row, encoded, old.base.tokenizer, manifest)
    for corrupt in ("cache", "work", "feature", "call"):
        changed = copy.deepcopy(row)
        if corrupt == "cache":
            changed["boundary"]["lower_cache_lengths"][0] += 1
        elif corrupt == "work":
            changed["layer_token_counts"][0] += 1
        elif corrupt == "feature":
            changed["features"]["evidence_mass"] += 0.1
        else:
            changed["logical_jev_calls"] = 0
        with pytest.raises(ValueError):
            a["check_output"](changed, encoded, old.base.tokenizer, manifest)


def test_auditor_rejects_forged_early_eos():
    import copy

    torch, old, encoded, view, policy = tiny()
    r, s, a = load("runtime"), load("study"), load("analyze")
    current = r["Runtime"](old.base, boundary=1)
    old.base.tokenizer.eos_token_id = -1

    async def success(v):
        return {"status": "complete", "key": "one", "scores": [0.9, 0.1]}

    with s["Profile"](old.base) as profile:
        row = asyncio.run(
            r["generate"](current, encoded, view, policy, success, gate={"kind": "always"})
        )
    row.update(
        arm="boundary_always", case_id=view["id"], policy=policy, forward_events=profile.events
    )
    manifest = {"num_layers": 2, "boundary": 1, "eos_ids": [-1]}
    changed = copy.deepcopy(row)
    changed["final"]["finish_reason"] = "eos"
    with pytest.raises(ValueError, match="EOS"):
        a["check_output"](changed, encoded, old.base.tokenizer, manifest)
