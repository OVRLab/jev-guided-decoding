"""R30 frozen worlds, feedback interventions and paired case statistics."""

import json
import math
import random
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
R29 = runpy.run_path(str(HERE.parent / "structured_correction/common.py"))
ROOT, sha, dump = R29["ROOT"], R29["sha"], R29["dump"]
ROOMS = ("kitchen", "office", "garage", "bedroom", "attic", "cellar", "hall", "lounge")
MODES = (
    "live",
    "rotate_left",
    "rotate_right",
    "mean",
    "donor",
    "constant",
    "type_only",
    "oracle",
    "scalar_trained",
)
SEEDS = (2901, 2902)


def worlds(size=384, seed=30001):
    if type(size) is not int or size < 4 or size % 2 or type(seed) is not int:
        raise ValueError("Need an even paired-family cohort of at least four worlds")
    cases, refs, rng = [], {}, random.Random(seed)
    objects = ["key", "coin", "book", "cup", "lamp", "ball", "ring", "pen", "map", "hat"]
    boxes = ["red crate", "blue crate", "green crate", "yellow crate"]
    for index in range(size):
        task = "temporal" if index % 2 == 0 else "compositional"
        items, places = rng.sample(objects, 6), rng.sample(list(ROOMS), 6)
        locations = {item: rng.choice(places if task == "temporal" else boxes) for item in items}
        box_rooms = {box: rng.choice(places) for box in boxes}
        lines = ["Use only this record. Events are listed from earliest to latest."]
        if task == "compositional":
            lines.append("Objects travel with their crate unless explicitly transferred.")
            lines.extend(
                f"Initially, the {box} is in the {room}." for box, room in box_rooms.items()
            )
        lines.extend(
            f"Initially, the {item} is in the {place}." for item, place in locations.items()
        )
        for event in range(8):
            if task == "compositional" and event % 2 == 0:
                box, room = rng.choice(boxes), rng.choice(places)
                lines.append(f"Event {event + 1}: the {box} is moved to the {room}.")
                box_rooms[box] = room
            else:
                item = rng.choice(items)
                place = rng.choice(places if task == "temporal" else boxes)
                lines.append(f"Event {event + 1}: the {item} is moved to the {place}.")
                locations[item] = place
        selected = rng.sample(items, 3)
        questions = [f"Which room contains the {item} after the final event?" for item in selected]
        prompt = (
            "\n".join(lines)
            + "\n\n"
            + "\n".join(f"{i + 1}. {q}" for i, q in enumerate(questions))
            + "\nReturn exactly three numbered lines, 1., 2., and 3., "
            "with only the requested room name on each line. Do not add explanations."
        )
        ident = f"r30/test/{task}/{index:03d}"
        cases.append(dict(id=ident, task=task, split="test", prompt=prompt, questions=questions))
        refs[ident] = [
            locations[item] if task == "temporal" else box_rooms[locations[item]]
            for item in selected
        ]
    if len({c["prompt"] for c in cases}) != size:
        raise ValueError("Duplicate generated world")
    return cases, refs


def signal(mode, values, *, donor=None, truth=None, draft=""):
    p = R29["probabilities"](values)
    if mode == "live":
        return p
    if mode == "rotate_left":
        return p[1:] + p[:1]
    if mode == "rotate_right":
        return p[-1:] + p[:-1]
    if mode in ("mean", "scalar_trained"):
        return [sum(p) / 3] * 3
    if mode == "constant":
        return [0.5] * 3
    if mode == "donor":
        if donor is None:
            raise ValueError("Missing donor feedback")
        return R29["probabilities"](donor)
    if mode == "oracle":
        if truth is None or len(truth) != 3 or any(type(v) is not bool for v in truth):
            raise ValueError("Oracle requires explicit Boolean reference flags")
        return [float(v) for v in truth]
    if mode == "type_only":
        fields = R29["fields"](draft)
        return [
            float(" ".join(fields.get(i, "").strip().rstrip(".!?").casefold().split()) in ROOMS)
            for i in (1, 2, 3)
        ]
    raise ValueError("Unknown pairing condition")


def donors(cases):
    if len({c["id"] for c in cases}) != len(cases):
        raise ValueError("Duplicate cases")
    result = {}
    for task in sorted({c["task"] for c in cases}):
        ids = sorted(c["id"] for c in cases if c["task"] == task)
        if len(ids) < 2:
            raise ValueError("Insufficient same-family donors")
        result.update({ident: ids[(i + 1) % len(ids)] for i, ident in enumerate(ids)})
    return result


def arms(seeds=SEEDS):
    return ["native", "blind"] + [f"{mode}/{seed}" for seed in seeds for mode in MODES]


def coverage(cases, rows, seeds=SEEDS):
    expected = {(c["id"], arm) for c in cases for arm in arms(seeds)}
    actual = {(r["id"], r["arm"]) for r in rows}
    if (
        len({c["id"] for c in cases}) != len(cases)
        or len(actual) != len(rows)
        or actual != expected
    ):
        raise ValueError("Incomplete, duplicate or unexpected output coverage")


def selected_checkpoints(upstream, provenance):
    inventory = provenance["original_backup_inventory"]
    if sha(upstream / "selection.json") != inventory["selection.json"]:
        raise ValueError("R29 checkpoint selection changed")
    selected = json.loads((upstream / "selection.json").read_text())["models"]
    result = {}
    for mode in ("structured", "scalar"):
        for seed in SEEDS:
            key = f"{mode}/{seed}"
            row = selected[key]
            name = row["file"]
            if (
                Path(name).name != name
                or row["sha256"] != inventory.get(name)
                or sha(upstream / name) != row["sha256"]
            ):
                raise ValueError("Unverified R29 checkpoint")
            result[key] = dict(row)
    return result


def sources():
    result = R29["source_hashes"]()
    paths = [
        *HERE.glob("*.py"),
        ROOT / "research/feedback-pairing-plan-v1.md",
        ROOT / "reports/2026-09-26-structured-correction/provenance.json",
    ]
    result.update({str(p.relative_to(ROOT)): sha(p) for p in sorted(paths)})
    return result


def effect(cases, treatment, baseline, draws=10000):
    ids = [c["id"] for c in cases]
    if (
        not ids
        or len(set(ids)) != len(ids)
        or set(ids) != set(treatment)
        or set(ids) != set(baseline)
    ):
        raise ValueError("Incomplete paired denominator")
    if (
        type(draws) is not int
        or draws < 100
        or any(
            not math.isfinite(v) or not 0 <= v <= 1
            for x in (treatment, baseline)
            for v in x.values()
        )
    ):
        raise ValueError("Invalid paired scores or draws")
    diff = {i: treatment[i] - baseline[i] for i in ids}
    groups = [
        [diff[c["id"]] for c in cases if c["task"] == task]
        for task in sorted({c["task"] for c in cases})
    ]
    rng = random.Random(3000)
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
        delta_pp=100 * sum(diff.values()) / len(ids),
        ci95_pp=interval(0.05),
        family_ci_pp=interval(0.05 / 3),
        family_confidence=1 - 0.05 / 3,
        fixed=sum(max(v, 0) for v in diff.values()),
        damaged=sum(max(-v, 0) for v in diff.values()),
    )
