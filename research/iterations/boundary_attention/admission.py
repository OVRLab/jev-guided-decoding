"""Real-checkpoint parity admission; canned relevance and failures make no API calls."""

import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = runpy.run_path(str(HERE / "runtime.py"))
D = runpy.run_path(str(HERE / "data.py"))
J = runpy.run_path(str(HERE.parent / "adaptive_attention/journal.py"))


async def admission(base, cases, output, policy, boundary=19):
    old, current = R["OLD"]["Runtime"](base), R["Runtime"](base, boundary=boundary)
    checks = []
    for c in cases:
        encoded = R["encode"](base.tokenizer, D["public_view"](c))
        scores = [float(i % 2 == 0) for i in range(len(c["sources"]))]
        for mode in ("native", "guided", "failed_receipt"):
            reference = old.session(encoded)
            logits = []

            def save(module, args, value, target=logits):
                target.append(value.logits[0, -1].detach().clone())

            handle = base.model.register_forward_hook(save)
            try:
                reference.extend(
                    4, policy if mode == "guided" else None, scores if mode == "guided" else None
                )
            finally:
                handle.remove()
            calls = []

            async def canned(view, calls=calls, mode=mode, scores=scores):
                calls.append(view["id"])
                if mode == "native":
                    raise AssertionError("No-call admission dispatched")
                return (
                    {"status": "failed", "key": "mechanics-failure"}
                    if mode == "failed_receipt"
                    else {"status": "complete", "key": "mechanics-scores", "scores": scores}
                )

            result = await R["generate"](
                current,
                encoded,
                D["public_view"](c),
                policy,
                canned,
                gate={"kind": "never" if mode == "native" else "always"},
                limit=4,
                capture=True,
            )
            debug = result.pop("_debug")
            logit_delta = max(
                float((a - b).abs().max()) for a, b in zip(logits, debug["logits"], strict=True)
            )
            cache_delta = max(
                float((a - b).abs().max())
                for name in ("key_cache", "value_cache")
                for a, b in zip(
                    getattr(reference.cache, name), getattr(debug["cache"], name), strict=True
                )
            )
            same_ids = reference.result()["token_ids"] == result["final"]["token_ids"]
            lengths = R["cache_lengths"](reference.cache) == R["cache_lengths"](debug["cache"])
            count = len(result["final"]["token_ids"])
            correct_work = (
                result["prefills"] == 1
                and result["discarded_tokens"] == 0
                and result["layer_calls"] == [count] * len(current.layers)
                and result["layer_token_counts"]
                == [len(encoded["input_ids"]) + count - 1] * len(current.layers)
            )
            passed = (
                logit_delta <= 0.0001
                and cache_delta <= 0.0001
                and same_ids
                and lengths
                and correct_work
                and len(calls) == int(mode != "native")
                and result["boundary"]["lower_cache_unchanged_during_wait"]
            )
            row = dict(
                case_id=c["id"],
                mode=mode,
                logit_max_difference=logit_delta,
                cache_max_difference=cache_delta,
                same_tokens=same_ids,
                same_cache_lengths=lengths,
                single_prefill_work=correct_work,
                canned_calls=len(calls),
                tokens=result["final"]["token_ids"],
                prompt_tokens=len(encoded["input_ids"]),
                boundary=result["boundary"],
                passed=passed,
            )
            J["append"](output / "admission-checks.jsonl", row)
            checks.append(row)
            if not passed:
                D["dump"](
                    output / "admission-failed.json",
                    dict(at=J["now"](), checks=checks, passed=False),
                )
                raise ValueError(f"Boundary admission failed in {mode}")
    D["dump"](
        output / "admission.json",
        dict(at=J["now"](), checks=checks, passed=True, live_jev_calls=0, tolerance=0.0001),
    )
