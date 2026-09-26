"""Fresh R15 containment cohorts; preserve R14's visible test rendering."""

import hashlib
import random
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
D = runpy.run_path(str(ROOT / "research/experiments/evidence_data.py"))
SEEDS = {"development": 15092211, "test": 25092223, "challenge": 35092237}
context = D["context"]
model_view = D["model_view"]
lexical_scores = D["lexical_scores"]


def worlds(split, count, used):
    if split not in SEEDS or type(count) is not int or count < 6 or count % 6:
        raise ValueError("Balanced known cohort required")
    rng = random.Random(SEEDS[split])
    depths = (4, 5, 6) if split == "challenge" else (1, 2, 3)

    def alias(kind):
        while True:
            value = "".join(rng.choice("bcdfgklmnprstv") + rng.choice("aeiou") for _ in range(3))
            if value not in used:
                used.add(value)
                return kind + " " + value

    result = []
    for index in range(count):
        depth, missing = depths[index % 3], index % 6 >= 3
        target = alias("parcel")
        room = rng.choice(D["LABELS"][:-1])
        chain = (
            [target]
            + [alias("crate" if i % 2 == 0 else "locker") for i in range(depth - 1)]
            + ["room " + room]
        )
        relevant = list(zip(chain[:-1], chain[1:], strict=True))
        if missing:
            relevant.pop()
        noise = []
        for _ in range(6):
            path = [
                alias("parcel"),
                alias("crate"),
                alias("locker"),
                "room " + rng.choice(D["LABELS"][:-1]),
            ]
            noise.extend(zip(path[:-1], path[1:], strict=True))
        reference = "UNKNOWN" if missing else room
        if D["grade"](target, relevant + noise) != reference:
            raise ValueError("Construction and graph disagree")
        ident = hashlib.sha256(f"r15/{split}/{index}/{target}".encode()).hexdigest()[:16]
        result.append(
            dict(
                id=f"evidence-v2/{split}/{ident}",
                index=index,
                split="test",
                cohort=split,
                depth=depth,
                missing=missing,
                target=target,
                relevant=relevant,
                noise=noise,
                reference=reference,
                ordering_seed=rng.randrange(2**31),
            )
        )
    return result


def exposed_aliases():
    used = set()
    for split in ("profile", "calibration", "test"):
        import json

        for world in json.loads(
            (ROOT / f"research/protocols/evidence-attention-v1/{split}.json").read_text()
        ):
            used.add(world["target"].split(" ", 1)[1])
            for edge in world["relevant"] + world["noise"]:
                for node in edge:
                    if not node.startswith("room "):
                        used.add(node.split(" ", 1)[1])
    return used
