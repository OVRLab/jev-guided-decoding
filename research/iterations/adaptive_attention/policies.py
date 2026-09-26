"""Bounded head-specific policies; development selection has no hidden harm gate."""

import copy
import hashlib
import json
import math

HEADS = [
    (34, 4),
    (38, 11),
    (37, 14),
    (30, 4),
    (23, 8),
    (19, 6),
    (21, 13),
    (19, 11),
    (19, 15),
    (21, 14),
    (29, 10),
    (20, 11),
]
LEVELS = (0.0, math.log(4), math.log(16), 4.0, 5.0)


def identified(policy):
    p = copy.deepcopy(policy)
    p.pop("id", None)
    p["id"] = hashlib.sha256(json.dumps(p, sort_keys=True).encode()).hexdigest()[:16]
    return p


def r15():
    return identified(
        {
            "heads": [list(h) for h in HEADS],
            "weights": [math.log(16)] * 12,
            "mapping": "threshold",
            "threshold": 0.5,
        }
    )


def validate(policy):
    if set(policy) != {"id", "heads", "weights", "mapping", "threshold"}:
        raise ValueError("Invalid policy fields")
    if not policy["heads"] or len(policy["heads"]) != len(policy["weights"]):
        raise ValueError("One weight per head required")
    if len({tuple(h) for h in policy["heads"]}) != len(policy["heads"]):
        raise ValueError("Duplicate heads")
    if any(
        type(w) not in (int, float) or not math.isfinite(w) or not 0 <= w <= 5
        for w in policy["weights"]
    ):
        raise ValueError("Invalid head weight")
    if policy["mapping"] not in ("threshold", "soft"):
        raise ValueError("Invalid mapping")
    if not 0 <= policy["threshold"] <= 1:
        raise ValueError("Invalid threshold")


def token_maps(policy, spans, scores):
    validate(policy)
    if (
        len(spans) != len(scores)
        or not scores
        or any(
            type(s) not in (int, float) or not math.isfinite(s) or not 0 <= s <= 1 for s in scores
        )
    ):
        raise ValueError("Invalid relevance scores")
    mapped = (
        [float(s > policy["threshold"]) for s in scores]
        if policy["mapping"] == "threshold"
        else [max(0.0, 2 * s - 1) for s in scores]
    )
    if max(mapped) == min(mapped):
        return {}
    result = {}
    for head, weight in zip(policy["heads"], policy["weights"], strict=True):
        if not weight:
            continue
        keys = {}
        for span, score in zip(spans, mapped, strict=True):
            for token in span:
                if type(token) is not int or token < 0 or token in keys:
                    raise ValueError("Invalid source tokens")
                keys[token] = weight * score
        result[tuple(head)] = {k: v for k, v in keys.items() if v}
    return {h: b for h, b in result.items() if b}


def changed(policy, **kwargs):
    return identified({**policy, **kwargs})


def diagnostic_policies():
    base = r15()
    result = [base]
    for index in range(12):
        weights = list(base["weights"])
        weights[index] = 0.0
        result.append(changed(base, weights=weights))
    for layer in sorted({h[0] for h in HEADS}):
        weights = [0.0 if h[0] == layer else w for h, w in zip(HEADS, base["weights"], strict=True)]
        result.append(changed(base, weights=weights))
    for strength in (math.log(4), 4.0, 5.0):
        result.append(changed(base, weights=[strength] * 12))
    return list({p["id"]: p for p in result}.values())


def choose(rows):
    if not rows:
        raise ValueError("No development candidates")
    return min(
        rows,
        key=lambda r: (
            -r["accuracy"],
            -r["mean_logprob"],
            sum(r["policy"]["weights"]),
            r["policy"]["id"],
        ),
    )
