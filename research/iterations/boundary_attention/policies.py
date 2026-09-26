"""Development-only request-budget threshold fitting for R18 native feature families."""

import hashlib
import json
import math
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
F = runpy.run_path(str(HERE / "features.py"))
OLD = runpy.run_path(str(HERE.parent / "selective_attention/policies.py"))
FEATURES = F["FEATURES"]
PILOT_FEATURES = OLD["FEATURES"]


def decision(gate, features, ident):
    if gate["kind"] in ("always", "never"):
        return gate["kind"] == "always"
    if gate["kind"] == "random":
        fraction = gate["fraction"]
        if (
            type(fraction) not in (int, float)
            or not math.isfinite(fraction)
            or not 0 <= fraction <= 1
        ):
            raise ValueError("Invalid random fraction")
        value = int(hashlib.sha256(("r18-random/" + ident).encode()).hexdigest()[:16], 16) / 2**64
        return value < fraction
    if (
        gate["kind"] != "threshold"
        or gate["feature"] not in (*FEATURES, *PILOT_FEATURES)
        or gate["direction"] not in ("le", "gt")
    ):
        raise ValueError("Invalid gate")
    value, threshold = features[gate["feature"]], gate["threshold"]
    if any(type(v) not in (int, float) or not math.isfinite(v) for v in (value, threshold)):
        raise ValueError("Nonfinite gate feature")
    return value <= threshold if gate["direction"] == "le" else value > threshold


def fit(rows, names=FEATURES, ceiling=0.5):
    if (
        not rows
        or type(ceiling) not in (int, float)
        or not math.isfinite(ceiling)
        or not 0 <= ceiling <= 1
    ):
        raise ValueError("Invalid development data/budget")
    if any(
        type(r[k]) not in (int, float) or not math.isfinite(r[k]) or not 0 <= r[k] <= 1
        for r in rows
        for k in ("native_quality", "guided_quality")
    ):
        raise ValueError("Invalid development quality")
    candidates = [{"kind": "never"}]
    for name in names:
        values = sorted(r["features"][name] for r in rows)
        if any(not math.isfinite(v) for v in values):
            raise ValueError("Nonfinite development feature")
        for i in range(21):
            threshold = values[round(i / 20 * (len(values) - 1))]
            for direction in ("le", "gt"):
                candidates.append(
                    dict(kind="threshold", feature=name, direction=direction, threshold=threshold)
                )
    scored = []
    for gate in candidates:
        calls = [decision(gate, row["features"], row["case_id"]) for row in rows]
        fraction = sum(calls) / len(calls)
        if fraction > ceiling:
            continue
        qualities = [
            {"family": r["domain"], "quality": r["guided_quality"] if call else r["native_quality"]}
            for r, call in zip(rows, calls, strict=True)
        ]
        quality = OLD["balanced"](qualities, "quality")
        scored.append(dict(gate=gate, quality=quality, call_fraction=fraction, calls=sum(calls)))
    return min(
        scored, key=lambda r: (-r["quality"], r["calls"], json.dumps(r["gate"], sort_keys=True))
    )
