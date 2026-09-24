"""Export aggregate full-task results without private examples or double-counted cost."""

import math

SYSTEMS = (
    "original",
    "guided",
    "self_refine",
    "blind",
    "constant",
    "live_constant",
    "inverted",
    "shuffled",
    "granite_4_2_3b",
    "qwen3_4b_instruct",
)
COUNTS = {"gpqa_diamond": (198, 196), "ifbench": (300, 288), "aime2026": (30, 30)}


def number(value, low, high):
    if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError("Invalid aggregate number")
    return value


def count(value, maximum):
    if type(value) is not int or not 0 <= value <= maximum:
        raise ValueError("Invalid aggregate count")
    return value


def interval(value, low, high):
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError("Invalid interval")
    result = [number(v, low - 1e-12, high + 1e-12) for v in value]
    if result[0] > result[1]:
        raise ValueError("Reversed interval")
    return result


def quality_export(audit, *, tasks):
    if not all(audit.get(k) is True for k in ("admitted", "audited_records", "tokenizers_checked")):
        raise ValueError("Independent audit required")
    if not tasks or len(set(tasks)) != len(tasks) or set(tasks) - COUNTS.keys():
        raise ValueError("Unsupported task scope")

    def extract(quality, index):
        if not quality or set(quality["summaries"]) != set(SYSTEMS):
            raise ValueError("Incomplete compared systems")
        summaries = {}
        for system, values in quality["summaries"].items():
            if set(values) != set(tasks):
                raise ValueError("Task coverage mismatch")
            summaries[system] = {}
            for task, row in values.items():
                n = COUNTS[task][index]
                if row["total"] != n or type(row["total"]) is not int:
                    raise ValueError("Incomplete task denominator")
                correct = count(row["correct"], n)
                accuracy = number(row["accuracy"], 0, 1)
                if not math.isclose(accuracy, correct / n, rel_tol=0, abs_tol=1e-12):
                    raise ValueError("Score/count mismatch")
                clean = dict(
                    total=n,
                    correct=correct,
                    accuracy=accuracy,
                    wilson_95=interval(row["wilson_95"], 0, 1),
                    **{
                        k: count(row[k], n)
                        for k in ("unparseable", "length_stops", "unfinished_thinking")
                    },
                )
                if task == "ifbench":
                    clean["loose_correct"] = count(row["loose_correct"], n)
                summaries[system][task] = clean
        allowed_pairs = {f"{a}-{b}" for a in SYSTEMS for b in SYSTEMS if a != b}
        paired = {}
        for name, values in quality["paired_differences"].items():
            if name not in allowed_pairs or set(values) != set(tasks):
                raise ValueError("Invalid paired comparison")
            paired[name] = {}
            for task, row in values.items():
                n = COUNTS[task][index]
                if row["pairs"] != n or row["confirmatory_superiority"] is not False:
                    raise ValueError("Invalid comparison scope/claim")
                wins, losses = count(row["wins"], n), count(row["losses"], n)
                difference = number(row["difference"], -1, 1)
                clusters = count(row["clusters"], n)
                if (
                    wins + losses > n
                    or clusters == 0
                    or not math.isclose(difference, (wins - losses) / n, abs_tol=1e-12)
                ):
                    raise ValueError("Invalid paired counts")
                paired[name][task] = dict(
                    pairs=n,
                    clusters=clusters,
                    wins=wins,
                    losses=losses,
                    difference=difference,
                    descriptive_paired_95=interval(row["descriptive_paired_95"], -1, 1),
                    confirmatory_superiority=False,
                )
        return dict(summaries=summaries, paired_differences=paired)

    untouched = audit["untouched_quality"]
    if untouched is None and all(COUNTS[t][0] == COUNTS[t][1] for t in tasks):
        untouched = audit["quality"]
    return dict(
        full=extract(audit["quality"], 0),
        untouched=extract(untouched, 1),
        ten_task_mean=None,
        superiority_established=False,
    )


def reconcile_cost(prior, stages, *, cap):
    number(cap, 0, math.inf)
    number(prior, 0, cap)
    names, costs = set(), []
    for stage in stages:
        name = stage["name"]
        if not isinstance(name, str) or not name or name in names:
            raise ValueError("Invalid or duplicate stage")
        names.add(name)
        if stage["deleted"] is not True:
            raise ValueError("Verified cleanup required")
        seconds = number(stage["resource_seconds"], 0, math.inf)
        rate = number(stage["rate_usd_hour"], 0, math.inf)
        jev = number(stage["jev_usd"], 0, math.inf)
        costs.append(dict(name=name, cloud_usd=seconds / 3600 * rate, jev_usd=jev))
    total = prior + sum(s["cloud_usd"] + s["jev_usd"] for s in costs)
    if total > cap:
        raise ValueError("Cumulative cap exceeded")
    return dict(
        prior_usd=prior,
        stages=costs,
        cumulative_usd=total,
        remaining_usd=cap - total,
        cap_usd=cap,
        estimate_before_tax_and_separate_network=True,
    )
