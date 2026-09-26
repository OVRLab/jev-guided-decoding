"""Independent cached replay of relevance and instruction bias before live Jev dispatch."""

import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = runpy.run_path(str(HERE / "runtime.py"))
D = runpy.run_path(str(HERE / "data.py"))
J = runpy.run_path(str(HERE.parent / "adaptive_attention/journal.py"))


async def admission(base, cases, output, policy, boundary=19):
    old = R["OLD"]["Runtime"](base)
    current = R["Runtime"](base, boundary=boundary)
    checks = []
    for case in cases:
        view = D["public_view"](case)
        encoded = R["encode"](base.tokenizer, view)
        scores = [float(i % 2 == 0) for i in range(len(view["sources"]))]
        for mode in ("native", "failed", "relevance", "abstention"):
            reference_encoded = encoded
            reference_policy = policy if mode == "relevance" else None
            reference_scores = scores if mode == "relevance" else None
            if mode == "abstention":
                reference_encoded = {
                    **encoded,
                    "span_token_indices": [
                        encoded["abstention_token_indices"],
                        [k for span in encoded["span_token_indices"] for k in span],
                    ],
                }
                reference_policy = {**policy, "strength": 2}
                reference_scores = [1.0, 0.0]
            reference = old.session(reference_encoded)
            logits = []
            handle = base.model.register_forward_hook(
                lambda m, a, o, target=logits: target.append(o.logits[0, -1].detach().clone())
            )
            try:
                reference.extend(4, reference_policy, reference_scores)
            finally:
                handle.remove()

            async def receipt(v, mode=mode, scores=scores):
                if mode == "native":
                    raise AssertionError("Unexpected provider dispatch")
                return (
                    dict(status="failed", key="admission")
                    if mode == "failed"
                    else dict(
                        status="complete",
                        key="admission",
                        scores=scores,
                        sufficient=0.1 if mode == "abstention" else 0.9,
                    )
                )

            result = await R["generate"](
                current,
                encoded,
                view,
                policy,
                receipt,
                gate={"kind": "never" if mode == "native" else "always"},
                mode="dual",
                instruction_strength=2,
                limit=4,
                capture=True,
            )
            debug = result.pop("_debug")
            ld = max(
                float((x - y).abs().max()) for x, y in zip(logits, debug["logits"], strict=True)
            )
            cd = max(
                float((x - y).abs().max())
                for name in ("key_cache", "value_cache")
                for x, y in zip(
                    getattr(reference.cache, name), getattr(debug["cache"], name), strict=True
                )
            )
            n = len(result["final"]["token_ids"])
            passed = (
                ld <= 1e-4
                and cd <= 1e-4
                and result["final"]["token_ids"] == reference.result()["token_ids"]
                and result["layer_calls"] == [n] * len(current.layers)
                and result["layer_token_counts"]
                == [len(encoded["input_ids"]) + n - 1] * len(current.layers)
                and result["boundary"]["lower_cache_unchanged_during_wait"]
            )
            row = dict(
                case_id=case["id"],
                mode=mode,
                passed=passed,
                logit_max_difference=ld,
                cache_max_difference=cd,
                tokens=result["final"]["token_ids"],
                action=result["intervention_action"],
                applied_maps=result["applied_maps"],
            )
            J["append"](output / "admission-checks.jsonl", row)
            checks.append(row)
            if not passed:
                raise ValueError("R19 admission failed")
    D["dump"](output / "admission.json", dict(passed=True, live_jev_calls=0, checks=checks))
