"""Fresh, balanced R17 worlds and unchanged conservative R16 scoring contracts."""

import random
import re
import runpy
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OLD = runpy.run_path(str(Path(__file__).resolve().parents[1] / "adaptive_attention/data.py"))
public_view, grade, dump, sha = (OLD[k] for k in ("public_view", "grade", "dump", "sha"))
SEEDS = {"development": 170922317, "test": 270922319}


@lru_cache
def prior_names():
    used = set()
    for folder in ("evidence-attention-v1", "evidence-attention-v2", "adaptive-attention-fp32"):
        for p in (ROOT / "research/protocols" / folder).glob("*.json"):
            used.update(re.findall(r"(?:parcel|crate|locker|task) ([a-z]{8})", p.read_text()))
    return frozenset(used)


def synthetic(split, count):
    if split not in SEEDS or count < 36 or count % 36:
        raise ValueError("Balanced 36-cell relation/depth/missing cohort required")
    rng, used = random.Random(SEEDS[split]), set(prior_names())
    if split == "test":
        for c in synthetic("development", 108):
            used.update(re.findall(r"\b[a-z]{8}\b", str(c["sources"])))

    def alias(kind):
        while True:
            word = "".join(rng.choice("bcdfgklmnprstv") + rng.choice("aeiou") for _ in range(4))
            if word not in used:
                used.add(word)
                return kind + " " + word

    result = []
    for index in range(count):
        depth, missing = index % 6 + 1, index % 12 >= 6
        family = ("original", "paraphrase", "dependency")[(index // 12) % 3]
        target = alias("parcel")
        nodes = (
            [target]
            + [alias("crate") for _ in range(depth - 1)]
            + ["room " + rng.choice(OLD["COLORS"])]
        )
        relevant = list(zip(nodes[:-1], nodes[1:], strict=True))
        if missing:
            relevant.pop()
        noise = []
        for _ in range(6):
            distractor = [
                alias("parcel"),
                alias("crate"),
                alias("locker"),
                "room " + rng.choice(OLD["COLORS"]),
            ]
            noise.extend(zip(distractor[:-1], distractor[1:], strict=True))
        world = f"r17/{split}/{index:04}/{target.split()[1]}"
        for condition in ("heavy",) if split == "development" else ("light", "heavy"):
            tagged = [(e, 1) for e in relevant] + [
                (e, 0) for e in (noise[:3] if condition == "light" else noise)
            ]
            random.Random(f"r17/{SEEDS[split]}/{index}/{condition}").shuffle(tagged)
            c = dict(
                id=f"{world}/{condition}",
                world_id=world,
                split=split,
                index=index,
                condition=condition,
                depth=depth,
                missing=missing,
                family="original",
                target=target,
                question=f"Which room contains the {target}?",
                sources=[
                    {"id": f"E{i + 1:02}", "text": f"The {b} contains the {a}."}
                    for i, ((a, b), _) in enumerate(tagged)
                ],
                reference="UNKNOWN" if missing else nodes[-1].split()[1],
                oracle_scores=[v for _, v in tagged],
            )
            c = OLD["variant"](c, family)
            if OLD["visible_reference"](c) != c["reference"]:
                raise ValueError("Visible truth mismatch")
            result.append(c)
    return result


def domain(case):
    return "hotpot" if case["family"] == "hotpot" else "synthetic"


def quality(case, grade):
    return grade["f1"] if case["family"] == "hotpot" else grade["correct"]
