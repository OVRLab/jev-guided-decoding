"""New fictional rule worlds; deterministic labels checked by the independent oracle."""

import json
import random
import runpy
from pathlib import Path

DATA = runpy.run_path(str(Path(__file__).with_name("proofwriter_data.py")))


def make_cases(seed=20260921):
    rng = random.Random(seed)
    cases = []
    for depth in (2, 4, 6, 7):
        for motif in ("chain_cycle", "conjunction"):
            for label in DATA["LABELS"]:
                subject = f"Vela{rng.randrange(10000, 99999)}"
                properties = rng.sample(
                    [
                        "amber",
                        "blue",
                        "bronze",
                        "cold",
                        "copper",
                        "green",
                        "kind",
                        "nice",
                        "quiet",
                        "red",
                        "rough",
                        "round",
                        "silver",
                        "smart",
                        "warm",
                        "young",
                    ],
                    depth + 1,
                )

                def representation(value):
                    return "(" + " ".join(json.dumps(v) for v in value) + ")"

                def fact(prop, polarity="+", entity=subject):
                    value = (entity, "is", prop, polarity)
                    return {
                        "text": DATA["verbalize"](value) + ".",
                        "representation": representation(value),
                    }

                facts = (
                    [] if label == "UNKNOWN" and motif == "chain_cycle" else [fact(properties[0])]
                )
                if motif == "conjunction" and label != "UNKNOWN":
                    facts.append(fact("licensed"))
                rules = []
                for index in range(1, depth + 1):
                    body = [fact(properties[index - 1])]
                    if motif == "conjunction" and index == (depth + 1) // 2:
                        body.append(fact("licensed"))
                    head = fact(
                        properties[index],
                        "-" if index == depth and label == "CONTRADICTED" else "+",
                    )
                    rules.append(
                        {
                            "text": "If "
                            + " and ".join(f["text"].rstrip(".") for f in body)
                            + " then "
                            + head["text"],
                            "representation": "(("
                            + " ".join(f["representation"] for f in body)
                            + ") -> "
                            + head["representation"]
                            + ")",
                        }
                    )
                # An unseeded cycle cannot supply a missing first fact or licence.
                missing = properties[0] if motif == "chain_cycle" else "licensed"
                for start, end in ((missing, "registered"), ("registered", missing)):
                    a, b = fact(start), fact(end)
                    rules.append(
                        {
                            "text": f"If {a['text'][:-1]} then {b['text']}",
                            "representation": f"(({a['representation']}) -> {b['representation']})",
                        }
                    )
                for _ in range(6):
                    facts.append(
                        fact(rng.choice(properties), entity=f"Dexo{rng.randrange(10000, 99999)}")
                    )
                rng.shuffle(facts)
                rng.shuffle(rules)
                world = {
                    "id": f"stress-{len(cases):03d}",
                    "theory": " ".join(f["text"] for f in facts + rules),
                    "triples": {f"triple{i + 1}": f for i, f in enumerate(facts)},
                    "rules": {f"rule{i + 1}": r for i, r in enumerate(rules)},
                    "questions": {
                        "Q1": {
                            "question": fact(properties[-1])["text"],
                            "representation": fact(properties[-1])["representation"],
                            "answer": {
                                "ENTAILED": True,
                                "CONTRADICTED": False,
                                "UNKNOWN": "Unknown",
                            }[label],
                            "QDep": depth,
                        }
                    },
                }
                case = DATA["case_from"](world, "Q1")
                case.update(target_depth=depth, motif=motif)
                cases.append(case)
    rng.shuffle(cases)
    return cases
