"""Finite memory/feedback comparison and paired case-level statistics."""

import math
import random


def specifications(informative):
    if informative not in ("structured", "scalar", "both"):
        raise ValueError("Unknown informative feedback form")
    feedbacks = (
        ("structured", "scalar", "constant") if informative == "both" else (informative, "constant")
    )
    return [
        (f"{memory}-{feedback}", memory, feedback)
        for memory in ("embedding", "contextual")
        for feedback in feedbacks
    ]


def test_arms(manifest):
    specs = specifications(manifest["informative"])
    arms = ["native", "blind"]
    for seed in manifest["seeds"]:
        arms.extend(f"{name}/{seed}" for name, _, _ in specs)
        arms.extend(
            f"{control}/{name}/{seed}"
            for name, _, feedback in specs
            if feedback != "constant"
            for control in ("same_constant", "donor", "oracle")
        )
    return arms


def expected_outputs(cases, manifest):
    specs = specifications(manifest["informative"])
    expected = {(c["id"], "native") for c in cases}
    for case in cases:
        if case["split"] == "development":
            expected.update(
                (case["id"], f"development/{name}/{seed}/{epoch}")
                for name, _, _ in specs
                for seed in manifest["seeds"]
                for epoch in range(1, manifest["epochs"] + 1)
            )
        elif case["split"] == "test":
            expected.update((case["id"], arm) for arm in test_arms(manifest))
        elif case["split"] != "train":
            raise ValueError("Invalid split in output coverage")
    return expected


def coverage(cases, rows, manifest):
    actual = {(r["id"], r["arm"]) for r in rows}
    if (
        len({c["id"] for c in cases}) != len(cases)
        or len(actual) != len(rows)
        or actual != expected_outputs(cases, manifest)
    ):
        raise ValueError("Incomplete, duplicate or unexpected output coverage")


def effect(cases, differences, draws=10000):
    ids = [c["id"] for c in cases]
    if (
        not ids
        or len(set(ids)) != len(ids)
        or set(ids) != set(differences)
        or type(draws) is not int
        or draws < 100
        or any(not math.isfinite(v) or abs(v) > 2 for v in differences.values())
    ):
        raise ValueError("Invalid paired case differences")
    groups = [
        [differences[c["id"]] for c in cases if c["task"] == task]
        for task in sorted({c["task"] for c in cases})
    ]
    rng = random.Random(3100)
    samples = sorted(
        100 * sum(sum(rng.choices(g, k=len(g))) for g in groups) / len(ids) for _ in range(draws)
    )

    def interval(alpha):
        return [
            samples[int(alpha / 2 * draws)],
            samples[min(draws - 1, int((1 - alpha / 2) * draws))],
        ]

    return dict(
        n=len(ids),
        delta_pp=100 * sum(differences.values()) / len(ids),
        ci95_pp=interval(0.05),
        family_ci_pp=interval(0.05 / 4),
        family_confidence=0.9875,
    )
