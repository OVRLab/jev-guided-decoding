"""Finite R17 intervention grid and reference-free inference-time gate decisions."""

import hashlib
import json
import math
import re

HEADS = [
    [34, 4],
    [38, 11],
    [37, 14],
    [30, 4],
    [23, 8],
    [19, 6],
    [19, 11],
    [19, 15],
    [21, 14],
    [29, 10],
    [20, 11],
]
FEATURES = ("min_probability", "mean_entropy", "copy_fraction")


def identify(value):
    value = {k: v for k, v in value.items() if k != "id"}
    return {
        **value,
        "id": hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()[:16],
    }


def grid():
    return [
        identify(dict(mode=m, envelope=e, strength=s, heads=HEADS, threshold=0.65))
        for m in ("additive", "conserve")
        for e in ("all", "prefill", "fade8")
        for s in (math.log(16), 5.0)
    ]


def strength(policy, step):
    s = policy["strength"]
    if (
        type(s) not in (int, float)
        or not math.isfinite(s)
        or not 0 <= s <= 5
        or type(step) is not int
        or step < 0
        or policy["mode"] not in ("additive", "conserve")
        or policy["envelope"] not in ("all", "prefill", "fade8")
    ):
        raise ValueError("Invalid intervention")
    if policy["envelope"] == "prefill":
        return s if step == 0 else 0.0
    return s * max(0.0, 1 - step / 8) if policy["envelope"] == "fade8" else s


def features(tokens, text, view):
    if not tokens:
        raise ValueError("Gate requires an observed native pilot")
    words = re.findall(r"\w+", text.lower())
    source_words = set(re.findall(r"\w+", " ".join(x["text"] for x in view["sources"]).lower()))
    return {
        "min_probability": min(t["probability"] for t in tokens),
        "mean_entropy": sum(t["entropy"] for t in tokens) / len(tokens),
        "copy_fraction": sum(w in source_words for w in words) / max(1, len(words)),
    }


def gate_decision(gate, observed, ident):
    kind = gate["kind"]
    if kind in ("always", "never"):
        return kind == "always"
    if kind == "random":
        fraction = gate["fraction"]
        if (
            type(fraction) not in (int, float)
            or not math.isfinite(fraction)
            or not 0 <= fraction <= 1
        ):
            raise ValueError("Invalid call fraction")
        value = int(hashlib.sha256(("r17-random/" + ident).encode()).hexdigest()[:16], 16) / 2**64
        return value < fraction
    if (
        kind != "threshold"
        or gate["feature"] not in FEATURES
        or gate["direction"] not in ("le", "gt")
    ):
        raise ValueError("Invalid gate")
    value, threshold = observed[gate["feature"]], gate["threshold"]
    if any(type(x) not in (int, float) or not math.isfinite(x) for x in (value, threshold)):
        raise ValueError("Nonfinite gate feature")
    return value <= threshold if gate["direction"] == "le" else value > threshold


def balanced(rows, field):
    domains = sorted({r["family"] for r in rows})
    if not domains:
        raise ValueError("No development records")
    return sum(
        sum(r[field] for r in rows if r["family"] == d) / sum(r["family"] == d for r in rows)
        for d in domains
    ) / len(domains)


def fit_gates(rows):
    candidates = [{"kind": "never"}, {"kind": "always"}]
    for feature in FEATURES:
        values = sorted(r["features"][feature] for r in rows)
        for q in (0.1, 0.25, 0.5, 0.75, 0.9):
            threshold = values[min(len(values) - 1, int(q * len(values)))]
            for direction in ("le", "gt"):
                candidates.append(
                    dict(
                        kind="threshold", feature=feature, threshold=threshold, direction=direction
                    )
                )
    candidates = {json.dumps(g, sort_keys=True): g for g in candidates}
    scored = []
    for g in candidates.values():
        selected = []
        for i, row in enumerate(rows):
            call = gate_decision(g, row["features"], str(i))
            selected.append(
                {
                    "family": row["family"],
                    "call": int(call),
                    "quality": row["guided_quality"] if call else row["native_quality"],
                }
            )
        quality, calls = balanced(selected, "quality"), balanced(selected, "call")
        scored.append(
            dict(gate=g, quality=quality, call_fraction=calls, utility=quality - 0.02 * calls)
        )

    def choose(candidates):
        return min(
            candidates,
            key=lambda x: (
                -x["utility"],
                x["call_fraction"],
                json.dumps(x["gate"], sort_keys=True),
            ),
        )

    uncertainty = [
        r
        for r in scored
        if r["gate"]["kind"] in ("always", "never")
        or (r["gate"]["feature"] == "min_probability" and r["gate"]["direction"] == "le")
    ]
    return dict(benefit=choose(scored), uncertainty=choose(uncertainty), candidates=scored)


def choose_policy(rows):
    return min(
        rows,
        key=lambda r: (
            -r["quality"],
            {"prefill": 0, "fade8": 1, "all": 2}[r["policy"]["envelope"]],
            r["policy"]["strength"],
            r["policy"]["mode"] == "conserve",
            r["policy"]["id"],
        ),
    )
