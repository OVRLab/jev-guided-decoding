"""R13 authored rule worlds; no labels or oracle internals enter model_view."""

import hashlib
import json
import random
import runpy
from pathlib import Path

OLD = runpy.run_path(str(Path(__file__).with_name("claim_worlds.py")))
closure, grade_claim = OLD["closure"], OLD["grade_claim"]
MOTIFS = ("forward", "conjunction", "negative", "negative_conjunction", "missing", "reverse")


def truth(case):
    known = closure(case)
    target = case["target"]
    opposite = (
        target.replace(" is not ", " is ", 1)
        if " is not " in target
        else target.replace(" is ", " is not ", 1)
    )
    if target in known and opposite in known:
        raise ValueError("Inconsistent world")
    return "TRUE" if target in known else "FALSE" if opposite in known else "UNKNOWN"


def model_view(case):
    return {key: case[key] for key in ("id", "evidence", "target", "entities", "properties")}


def worlds(split, count):
    if split not in {"development", "test"} or not 1 <= count <= 1000:
        raise ValueError("Invalid split/count")
    rng = random.Random({"development": 928917, "test": 1049123}[split])
    result = []
    for index in range(count):
        names = []
        while len(names) < 3:
            name = "".join(
                rng.choice("bcdfghjklmnprstv") + rng.choice("aeiou") for _ in range(3)
            ).capitalize()
            if name not in names:
                names.append(name)
        a, b, c = names
        props = rng.sample(OLD["PROPERTIES"], 8)
        depth = (2 if split == "development" else 3) + 2 * ((index // 6) % 2)
        motif = MOTIFS[index % 6]

        def atom(entity, p):
            return f"{entity} is {p}."

        chain = [atom(a, p) for p in props[: depth + 1]]
        facts = [chain[0], atom(b, props[1]), atom(c, props[7])]
        rules = [[[chain[i]], chain[i + 1]] for i in range(depth)]
        target = chain[-1]
        if motif in {"conjunction", "negative_conjunction", "missing"}:
            rules[0][0].append(atom(a, props[7]))
            if motif != "missing":
                facts.append(atom(a, props[7]))
        if motif in {"negative", "negative_conjunction"}:
            rules[-1][1] = target.replace(" is ", " is not ", 1)
        if motif == "reverse":
            facts.remove(chain[0])
            facts.append(chain[-1])
            target = chain[0]
        rules.append([[atom(b, props[1])], atom(b, props[6])])
        rng.shuffle(facts)
        rng.shuffle(rules)
        rendered = [
            ("If " if split == "development" else "Whenever ")
            + " and ".join(x.rstrip(".") for x in pre)
            + (", then " if split == "development" else ", it follows that ")
            + end
            for pre, end in rules
        ]
        case = dict(
            split=split,
            index=index,
            motif=motif,
            depth=depth,
            entities=names,
            properties=list(OLD["PROPERTIES"]),
            facts=facts,
            rules=rules,
            target=target,
            evidence=" ".join(facts + rendered),
        )
        case["reference_label"] = truth(case)
        digest = hashlib.sha256(json.dumps(case, sort_keys=True).encode()).hexdigest()
        case["id"] = f"structured/{split}/{digest[:16]}"
        result.append(case)
    return result
