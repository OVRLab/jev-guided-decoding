"""Label-side readout and paired scenario bootstrap, never inference inputs."""

import math
import random
import runpy
from pathlib import Path

S = runpy.run_path(str(Path(__file__).with_name("single.py")))


def grade(text, choices, reference, *, thinking=False):
    S["valid_choices"](choices)
    if type(reference) is not int or not 0 <= reference < len(choices):
        raise ValueError("Invalid reference index")
    readout = S["parse_choice"](text, choices, thinking=thinking)
    selected = readout["index"]
    normalized = [S["normalized"](c) for c in choices]
    return dict(
        correct=selected == reference,
        equivalent_choice=selected is not None and normalized[selected] == normalized[reference],
        ambiguous_options=len(set(normalized)) != len(choices),
        parsed_index=selected,
        unreadable=selected is None,
        format=readout["format"],
    )


def effect(cases, groups, differences, *, draws=10000, seed=3200, comparisons=4):
    ids = {c["id"] for c in cases}
    if (
        not cases
        or len(ids) != len(cases)
        or set(groups) != ids
        or set(differences) != ids
        or any(
            type(v) not in (int, float) or not math.isfinite(v) or abs(v) > 1
            for v in differences.values()
        )
        or any(not isinstance(g, str) or not g for g in groups.values())
        or type(draws) is not int
        or not 100 <= draws <= 100000
        or type(seed) is not int
        or not 0 <= seed < 2**63
        or type(comparisons) is not int
        or not 1 <= comparisons <= 20
    ):
        raise ValueError("Invalid grouped paired contrast")
    group_families = {}
    for case in cases:
        group_families.setdefault(groups[case["id"]], set()).add(case["task"])
    if any(len(families) != 1 for families in group_families.values()):
        raise ValueError("One scenario cannot cross task families")
    families = sorted({c["task"] for c in cases})
    populations, weights, observed = [], [], {}
    for family in families:
        members = [c["id"] for c in cases if c["task"] == family]
        grouped = []
        for group in sorted({groups[i] for i in members}):
            values = [differences[i] for i in members if groups[i] == group]
            grouped.append((sum(values), len(values)))
        populations.append(grouped)
        weights.append(len(members) / len(cases))
        observed[family] = 100 * sum(differences[i] for i in members) / len(members)
    rng = random.Random(seed)
    micro, macro = [], []
    for _ in range(draws):
        means = []
        for population in populations:
            selected = rng.choices(population, k=len(population))
            means.append(sum(value for value, _ in selected) / sum(size for _, size in selected))
        micro.append(100 * sum(w * value for w, value in zip(weights, means, strict=True)))
        macro.append(100 * sum(means) / len(means))
    micro.sort()
    macro.sort()

    def interval(values, alpha):
        return [
            values[int(alpha / 2 * draws)],
            values[min(draws - 1, int((1 - alpha / 2) * draws))],
        ]

    return dict(
        n=len(cases),
        groups=len(group_families),
        by_task_delta_pp=observed,
        delta_pp=100 * sum(differences.values()) / len(cases),
        ci95_pp=interval(micro, 0.05),
        family_ci_pp=interval(micro, 0.05 / comparisons),
        family_confidence=1 - 0.05 / comparisons,
        comparisons=comparisons,
        macro_delta_pp=sum(observed.values()) / len(observed),
        macro_ci95_pp=interval(macro, 0.05),
        draws=draws,
        seed=seed,
        method=(
            "Paired scenario bootstrap within task; fixed original task weights "
            "for question-weighted effect"
        ),
    )
