"""Authored synthetic rule worlds and strict independent full-claim semantics.

No generated text is executed. Noncanonical or compound prose is unassessed.
The oracle certifies entailment of an atomic assertion, not an implicit proof.
"""

from __future__ import annotations

import hashlib
import json
import random
import re

PROPERTIES = ("blue", "calm", "ready", "striped", "quiet", "warm", "small", "bright")
MOTIFS = ("forward", "conjunction", "missing", "reverse", "negative", "distractor")


def closure(case):
    known = set(case["facts"])
    while True:
        extra = {
            conclusion for premises, conclusion in case["rules"] if set(premises) <= known
        } - known
        if not extra:
            return known
        known.update(extra)


def grade_claim(case, text):
    normalized = re.sub(r"\s+", " ", text.strip()).rstrip(".").casefold()
    known = {x.casefold().rstrip(".") for x in closure(case)}
    given = {x.casefold().rstrip(".") for x in case["facts"]}
    for entity in case["entities"]:
        for prop in case["properties"]:
            for negated in (False, True):
                atom = f"{entity} is {'not ' if negated else ''}{prop}".casefold()
                if normalized == atom:
                    return {
                        "correct": atom in known,
                        "novel": atom not in given,
                        "kind": "negative" if negated else "positive",
                        "atom": atom,
                    }
                if normalized == "it is not established that " + atom:
                    return {
                        "correct": atom not in known,
                        "novel": True,
                        "kind": "not_established",
                        "atom": atom,
                    }
    return None


def worlds(split, count):
    if split not in ("development", "gate", "test") or not 1 <= count <= 1000:
        raise ValueError("Invalid world split/count")
    rng = random.Random({"development": 30109, "gate": 40927, "test": 58711}[split])
    result = []
    for i in range(count):
        names = []
        while len(names) < 3:
            name = "".join(
                rng.choice("bcdfghjklmnprstv") + rng.choice("aeiou") for _ in range(3)
            ).capitalize()
            if name not in names:
                names.append(name)
        a, b, c = names
        p, q, r, s, t, u, v, w = rng.sample(PROPERTIES, len(PROPERTIES))
        motif = MOTIFS[i % len(MOTIFS)]
        facts = [f"{a} is {p}.", f"{b} is {s}.", f"{c} is {u}."]
        rules = []
        target = f"{a} is {r}."
        if motif == "forward":
            rules = [[[f"{a} is {p}."], f"{a} is {q}."], [[f"{a} is {q}."], target]]
            if split != "development":
                rules[1][1] = f"{a} is {t}."
                rules.append([[f"{a} is {t}."], target])
        elif motif in ("conjunction", "missing"):
            facts.append(f"{a if motif == 'conjunction' else b} is {q}.")
            rules = [[[f"{a} is {p}.", f"{a} is {q}."], target]]
        elif motif == "reverse":
            facts.append(target)
            rules = [[[f"{a} is {q}."], target]]
            target = f"{a} is {q}."
        elif motif == "negative":
            target = f"{a} is not {r}."
            rules = [[[f"{a} is {p}."], target]]
        else:
            rules = [[[f"{a} is {p}."], f"{a} is {q}."], [[f"{b} is {s}."], f"{b} is {r}."]]
        # Different renderer templates across splits; logical motifs deliberately overlap.
        rng.shuffle(facts)
        rng.shuffle(rules)
        if split == "development":
            rendered = [
                "If " + " and ".join(x.rstrip(".") for x in pre) + ", then " + end
                for pre, end in rules
            ]
        else:
            rendered = [
                "Whenever " + " and ".join(x.rstrip(".") for x in pre) + ", it follows that " + end
                for pre, end in rules
            ]
        evidence = " ".join(facts + rendered)
        record = {
            "split": split,
            "index": i,
            "motif": motif,
            "entities": names,
            "properties": list(PROPERTIES),
            "facts": facts,
            "rules": rules,
            "target": target,
            "template": split + "-rules-v1",
            "evidence": evidence,
        }
        digest = hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest()
        record["id"] = f"local-claims/{split}/{digest[:16]}"
        result.append(record)
    return result


def request_question(case):
    return (
        f"We want to establish whether: {case['target']} "
        "Write one intermediate claim useful for considering that target. "
        "Write only one complete sentence in one of these forms, replacing X and P "
        "with an entity and property from the evidence: 'X is P.', 'X is not P.', "
        "or 'It is not established that X is P.'. Do not give the final TRUE/FALSE/UNKNOWN "
        "answer or an explanation. Close the supplied step frame."
    )


CLAIM_SYSTEM = """Use only the supplied evidence and forward implications. Every condition
of a rule is required. A missing fact is not an explicit negative fact. Produce one
short, complete intermediate assertion in the requested sentence format. The opening
<step> tag is already supplied. Continue its body and close with </step>. Do not open
a new frame, repeat instructions or output any other text. The target is a question,
not a given fact. Do not assume it is true."""
