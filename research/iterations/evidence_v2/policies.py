"""Finite policies and development selection, with no model or provider imports."""

import copy
import math

ARMS = (
    "native",
    "r14",
    "r15",
    "shuffled",
    "lexical",
    "prompt",
    "oracle",
    "zero",
    "mapping_only",
    "heads_only",
    "strength_only",
    "scope_only",
)
DEPENDENT = {
    "r14",
    "r15",
    "shuffled",
    "prompt",
    "mapping_only",
    "heads_only",
    "strength_only",
    "scope_only",
}


def map_scores(scores, mapping):
    if not scores or any(
        type(r) not in (int, float) or not math.isfinite(r) or not 0 <= r <= 1 for r in scores
    ):
        raise ValueError("Invalid relevance probabilities")
    if mapping == "soft":
        return list(scores)
    if mapping in ("hard50", "hard80"):
        threshold = 0.5 if mapping == "hard50" else 0.8
        return [int(r > threshold) for r in scores]
    raise ValueError("Unknown relevance mapping")


def grid(ranking):
    result = []
    for count in (1, 2, 4, 8, 12):
        for factor in (4, 8, 16):
            for mapping in ("soft", "hard50", "hard80"):
                for scope in ("question", "answer"):
                    result.append(
                        dict(
                            id=f"h{count:02}-ln{factor}-{mapping}-{scope}",
                            count=count,
                            strength=math.log(factor),
                            mapping=mapping,
                            scope=scope,
                            heads=[list(r["head"]) for r in ranking[:count]],
                        )
                    )
    return result


def r14(ranking):
    return next(p for p in grid(ranking) if p["id"] == "h08-ln8-soft-question")


def arms(previous, selected):
    result = {
        name: copy.deepcopy(selected) for name in ("r15", "shuffled", "lexical", "oracle", "zero")
    }
    result["r14"] = copy.deepcopy(previous)
    result["zero"]["strength"] = 0.0
    result["zero"]["id"] = "zero"
    result["native"] = result["prompt"] = None
    for name, fields in [
        ("mapping_only", ["mapping"]),
        ("heads_only", ["heads", "count"]),
        ("strength_only", ["strength"]),
        ("scope_only", ["scope"]),
    ]:
        result[name] = copy.deepcopy(previous)
        for field in fields:
            result[name][field] = copy.deepcopy(selected[field])
        result[name]["id"] = name
    return result


def select(outcomes, previous_id):
    previous = next(row for row in outcomes if row["policy"]["id"] == previous_id)
    candidates = []
    for row in outcomes:
        harms = [
            name
            for name in ("answerable", "missing", "clean")
            if row[name] < previous[name] - 0.03 - 1e-12
        ]
        candidates.append({**row, "eligible": not harms, "floor_failures": harms})
    eligible = [row for row in candidates if row["eligible"]]
    selected = min(
        eligible,
        key=lambda row: (
            -row["accuracy"],
            -row["mean_logprob"],
            row["policy"]["count"],
            row["policy"]["strength"],
            row["policy"]["mapping"],
            row["policy"]["scope"],
        ),
    )
    return {"selected": selected, "previous": previous, "candidates": candidates}
