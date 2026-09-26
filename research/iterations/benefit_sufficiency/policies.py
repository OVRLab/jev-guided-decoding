"""Separate expected treatment benefit from evidence sufficiency; no model-weight training."""

import hashlib
import json
import math
import re
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD = runpy.run_path(str(HERE.parent / "boundary_attention/policies.py"))
CLAUSE = "If the evidence does not establish an answer, explain that briefly in your own words."


def probability(value):
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError("Invalid probability")
    return value


def validate_spans(encoded):
    keys = encoded["abstention_token_indices"]
    sources = {k for span in encoded["span_token_indices"] for k in span}
    if (
        not keys
        or len(keys) != len(set(keys))
        or any(
            type(k) is not int or not 0 <= k < encoded["query_start"] or k in sources for k in keys
        )
    ):
        raise ValueError("Invalid instruction span binding")


def maps_for(policy, encoded, scores, sufficient, mode, instruction_strength):
    validate_spans(encoded)
    probability(sufficient)
    if mode not in ("relevance", "dual", "sufficiency") or instruction_strength not in (2, 5):
        raise ValueError("Invalid intervention")
    if len(scores) != len(encoded["span_token_indices"]):
        raise ValueError("Source scores mismatch")
    for score in scores:
        probability(score)
    values, action = {}, "native"
    if mode != "relevance" and sufficient <= 0.35:
        values = dict.fromkeys(encoded["abstention_token_indices"], instruction_strength)
        action = "abstention"
    elif mode == "relevance" or (mode == "dual" and sufficient >= 0.65):
        selected = [x > policy["threshold"] for x in scores]
        # Keep the exact R18 uniform-source no-op convention.
        if any(selected) and not all(selected):
            values = {
                k: policy["strength"]
                for keep, span in zip(selected, encoded["span_token_indices"], strict=True)
                if keep
                for k in span
            }
        action = "relevance"
    maps = {}
    if values:
        for layer, head in policy["heads"]:
            maps.setdefault(layer, {})[head] = dict(values)
    return maps, action


def vector(features, encoded, view):
    question = set(re.findall(r"[a-z0-9]+", view["question"].lower()))
    lexical = []
    for source in view["sources"]:
        words = set(re.findall(r"[a-z0-9]+", source["text"].lower()))
        lexical.append(len(question & words) / max(1, len(question | words)))
    x = [features[k] for k in ("evidence_mass", "source_entropy", "head_disagreement")]
    x += [
        math.log1p(len(view["sources"])),
        math.log1p(len(encoded["input_ids"])),
        max(lexical, default=0),
    ]
    validate_x(x)
    return x


def validate_x(x):
    if len(x) != 6 or any(type(v) not in (int, float) or not math.isfinite(v) for v in x):
        raise ValueError("Invalid benefit features")


def expand(x, means, scales):
    validate_x(x)
    z = [(v - m) / s for v, m, s in zip(x, means, scales, strict=True)]
    return [1.0, *z, *(z[i] * z[j] for i in range(6) for j in range(i, 6))]


def fit_ridge(rows, penalty):
    import numpy as np

    if not rows or penalty not in (1, 10, 100):
        raise ValueError("Invalid ridge fit")
    for row in rows:
        validate_x(row["x"])
        if not math.isfinite(row["delta"]) or not -1 <= row["delta"] <= 1:
            raise ValueError("Invalid treatment effect")
    raw = np.array([r["x"] for r in rows])
    means, scales = raw.mean(0), np.maximum(raw.std(0), 1e-6)
    matrix = np.array([expand(x, means, scales) for x in raw.tolist()])
    domains = [r["domain"] for r in rows]
    weights = np.array([len(rows) / (len(set(domains)) * domains.count(d)) for d in domains])
    target = np.array([r["delta"] for r in rows])
    regularizer = np.eye(matrix.shape[1]) * penalty
    regularizer[0, 0] = 0
    coefficients = np.linalg.solve(
        matrix.T @ (weights[:, None] * matrix) + regularizer, matrix.T @ (weights * target)
    )
    return dict(
        means=means.tolist(),
        scales=scales.tolist(),
        coefficients=coefficients.tolist(),
        penalty=penalty,
    )


def predict(model, x):
    values = expand(x, model["means"], model["scales"])
    value = sum(a * b for a, b in zip(values, model["coefficients"], strict=True))
    if not math.isfinite(value):
        raise ValueError("Nonfinite predicted benefit")
    return value


def decision(gate, features, encoded, view):
    if gate["kind"] == "benefit":
        if not math.isfinite(gate["threshold"]) or gate["threshold"] < 0:
            raise ValueError("Invalid benefit threshold")
        return predict(gate["model"], vector(features, encoded, view)) > gate["threshold"]
    if gate["kind"] == "random":
        probability(gate["fraction"])
        return (
            int(hashlib.sha256(("r19/" + view["id"]).encode()).hexdigest()[:16], 16) / 2**64
            < gate["fraction"]
        )
    return OLD["decision"](gate, features, view["id"])


def balanced(rows):
    domains = sorted({r["domain"] for r in rows})
    return sum(
        sum(r["quality"] for r in rows if r["domain"] == d) / sum(r["domain"] == d for r in rows)
        for d in domains
    ) / len(domains)


def select(fit, calibration):
    strengths = (2, 5)
    strength = min(
        strengths,
        key=lambda s: (
            -balanced([dict(domain=r["domain"], quality=r[f"dual_{s}"]) for r in calibration]),
            s,
        ),
    )
    candidates = [
        dict(
            gate={"kind": "never"},
            quality=balanced([dict(domain=r["domain"], quality=r["native"]) for r in calibration]),
            calls=0,
        )
    ]
    for penalty in (1, 10, 100):
        model = fit_ridge(
            [
                dict(x=r["x"], delta=r[f"dual_{strength}"] - r["native"], domain=r["domain"])
                for r in fit
            ],
            penalty,
        )
        predictions = [predict(model, r["x"]) for r in calibration]
        ordered = sorted(predictions)
        thresholds = {0.0} | {
            max(0.0, ordered[round(i / 20 * (len(ordered) - 1))]) for i in range(21)
        }
        for threshold in sorted(thresholds):
            calls = [v > threshold for v in predictions]
            if sum(calls) > len(calibration) / 2:
                continue
            quality = balanced(
                [
                    dict(domain=r["domain"], quality=r[f"dual_{strength}"] if call else r["native"])
                    for r, call in zip(calibration, calls, strict=True)
                ]
            )
            candidates.append(
                dict(
                    gate=dict(kind="benefit", model=model, threshold=threshold),
                    quality=quality,
                    calls=sum(calls),
                )
            )
    best = min(
        candidates, key=lambda c: (-c["quality"], c["calls"], json.dumps(c["gate"], sort_keys=True))
    )
    return dict(
        instruction_strength=strength,
        **best,
        fraction=best["calls"] / len(calibration),
        candidates=candidates,
    )
