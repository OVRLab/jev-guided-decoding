"""R28 reference-free routing and paired potential-outcome policy evaluation."""

import hashlib
import math
import random
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = runpy.run_path(str(ROOT / "research/iterations/selective_benchmarks/common.py"))
validate_case, sha, dump, digest = (BASE[k] for k in ("validate_case", "sha", "dump", "digest"))


def order(ids, salt):
    return sorted(ids, key=lambda i: (hashlib.sha256(f"{salt}/{i}".encode()).hexdigest(), i))


def admit_cost(prior, reserve, cap):
    if any(
        type(x) not in (int, float) or not math.isfinite(x) or x < 0 for x in (prior, reserve, cap)
    ):
        raise ValueError("Invalid cost admission")
    if reserve <= 0 or prior + reserve > cap:
        raise ValueError("Cumulative spending cap exceeded")


def make_plan(ids, probabilities, confidence):
    if (
        len(ids) < 8
        or len(set(ids)) != len(ids)
        or any(not isinstance(i, str) or not i for i in ids)
        or set(ids) != set(probabilities)
        or set(ids) != set(confidence)
    ):
        raise ValueError("Incomplete or duplicate routing inputs")
    for p in probabilities.values():
        BASE["probability"](p)
    for value in confidence.values():
        if value is not None and (
            type(value) not in (int, float) or not math.isfinite(value) or value > 0
        ):
            raise ValueError("Invalid native confidence")
    blocks = []
    policies = {
        p: {i: "native" for i in sorted(ids)}
        for p in (
            "native",
            "always_constant",
            "jev_constant",
            "confidence_constant",
            "random_constant",
            "jev_live",
            "jev_shuffled",
        )
    }
    policies["always_constant"] = dict.fromkeys(sorted(ids), "constant")
    balanced = order(ids, "block/2800")
    for index in range(2):
        group = sorted(balanced[index::2])
        k = len(group) // 2
        tie = {i: n for n, i in enumerate(order(group, "tie/2800"))}
        selected = dict(
            jev=sorted(group, key=lambda i: (probabilities[i], tie[i]))[:k],
            confidence=sorted(
                group, key=lambda i: (-1e30 if confidence[i] is None else confidence[i], tie[i])
            )[:k],
            random=order(group, "random/2801")[:k],
        )
        donors_order = order(selected["jev"], "donor/2802")
        donors = {i: donors_order[(j + 1) % k] for j, i in enumerate(donors_order)}
        for selector in selected:
            policies[selector + "_constant"].update(dict.fromkeys(selected[selector], "constant"))
        policies["jev_live"].update(dict.fromkeys(selected["jev"], "live"))
        policies["jev_shuffled"].update(dict.fromkeys(selected["jev"], "shuffled"))
        blocks.append(dict(index=index, ids=group, selected=selected, donors=donors))
    return dict(blocks=blocks, policies=policies)


def required_outputs(plan):
    return {(ident, arm) for policy in plan["policies"].values() for ident, arm in policy.items()}


def select_outputs(plan, rows):
    keys = [(r["id"], r["arm"]) for r in rows]
    if len(set(keys)) != len(keys) or set(keys) != required_outputs(plan):
        raise ValueError("Missing, duplicate or unexpected potential outcomes")
    lookup = dict(zip(keys, rows, strict=True))
    return {
        name: [lookup[i, arm] for i, arm in policy.items()]
        for name, policy in plan["policies"].items()
    }


def paired(a, b, blocks, *, draws=20000):
    if (
        not a
        or len(a) != len(b)
        or len(a) != len(blocks)
        or any(type(v) is not bool for v in a + b)
        or type(draws) is not int
        or draws < 100
    ):
        raise ValueError("Invalid paired outcomes")
    delta = [int(x) - int(y) for x, y in zip(a, b, strict=True)]
    groups = [
        [d for d, g in zip(delta, blocks, strict=True) if g == block]
        for block in sorted(set(blocks))
    ]
    rng = random.Random(2800)
    boot = sorted(
        100 * sum(rng.choice(g) for g in groups for _ in g) / len(a) for _ in range(draws)
    )

    def interval(alpha):
        return [boot[int(alpha / 2 * draws)], boot[min(draws - 1, int((1 - alpha / 2) * draws))]]

    return dict(
        n=len(a),
        delta_pp=100 * sum(delta) / len(a),
        wins=delta.count(1),
        losses=delta.count(-1),
        ci95_pp=interval(0.05),
        ci9875_pp=interval(0.0125),
        block_delta_pp=[100 * sum(g) / len(g) for g in groups],
    )
