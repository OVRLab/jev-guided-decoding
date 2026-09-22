"""Fresh authored graphs, independent visible-text grading and Hotpot answer metrics."""

import copy
import hashlib
import json
import random
import re
import string
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
COLORS = ("red", "blue", "green", "white", "black", "yellow")
SEEDS = {"development": 160922173, "test": 260922181}


def public_view(case):
    return {k: case[k] for k in ("id", "question", "sources", "family")}


def synthetic(split, count):
    if split not in SEEDS or count < 12 or count % 12:
        raise ValueError("Need a balanced twelve-cell cohort")
    rng = random.Random(SEEDS[split])
    used = set()
    for folder in ("evidence-attention-v1", "evidence-attention-v2"):
        for path in (ROOT / "research/protocols" / folder).glob("*.json"):
            used.update(re.findall(r"(?:parcel|crate|locker) ([a-z]+)", path.read_text()))

    def alias(kind):
        while True:
            name = "".join(rng.choice("bcdfgklmnprstv") + rng.choice("aeiou") for _ in range(4))
            if name not in used:
                used.add(name)
                return f"{kind} {name}"

    cases = []
    for index in range(count):
        depth, missing = index % 6 + 1, index % 12 >= 6
        target = alias("parcel")
        path = [target] + [alias("crate") for _ in range(depth - 1)]
        path.append("room " + rng.choice(COLORS))
        relevant = list(zip(path[:-1], path[1:], strict=True))
        if missing:
            relevant.pop()
        noise = []
        for _ in range(6):
            nodes = [alias("parcel"), alias("crate"), alias("locker"), "room " + rng.choice(COLORS)]
            noise.extend(zip(nodes[:-1], nodes[1:], strict=True))
        ident = f"r16/{split}/{index:04}/{target.split()[1]}"
        for condition in ("heavy",) if split == "development" else ("light", "heavy"):
            tagged = [(e, 1) for e in relevant] + [
                (e, 0) for e in (noise[:3] if condition == "light" else noise)
            ]
            random.Random(f"{SEEDS[split]}/{index}/{condition}").shuffle(tagged)
            case = dict(
                id=f"{ident}/{condition}",
                world_id=ident,
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
                reference="UNKNOWN" if missing else path[-1].split()[1],
                oracle_scores=[v for _, v in tagged],
            )
            if visible_reference(case) != case["reference"]:
                raise ValueError("Construction/visible reference disagreement")
            cases.append(case)
    return cases


def visible_edges(case):
    edges = []
    for source in case["sources"]:
        text = source["text"]
        if case["family"] == "original":
            m = re.fullmatch(r"The (.+) contains the (.+)\.", text)
            edge = (m[2], m[1]) if m else None
        elif case["family"] == "paraphrase":
            m = re.fullmatch(r"The (.+) is located inside the (.+)\.", text)
            edge = (m[1], m[2]) if m else None
        elif case["family"] == "dependency":
            m = re.fullmatch(r"The (.+) depends on the (.+)\.", text)
            edge = (m[1], m[2]) if m else None
        else:
            raise ValueError("Unknown synthetic family")
        if edge is None:
            raise ValueError("Unparseable source")
        edges.append(edge)
    return edges


def visible_reference(case):
    graph = {}
    for a, b in visible_edges(case):
        if a in graph and graph[a] != b:
            raise ValueError("Conflicting graph")
        graph[a] = b
    node, visited = case["target"], set()
    terminal = "terminal " if case["family"] == "dependency" else "room "
    while node in graph and node not in visited:
        visited.add(node)
        node = graph[node]
    return node[len(terminal) :] if node.startswith(terminal) else "UNKNOWN"


def variant(case, family):
    if family == "original":
        return copy.deepcopy(case)
    if case["family"] != "original" or family not in ("paraphrase", "dependency"):
        raise ValueError("Invalid transfer rendering")
    result = copy.deepcopy(case)
    edges = visible_edges(case)
    if family == "paraphrase":
        texts = [f"The {a} is located inside the {b}." for a, b in edges]
        result["question"] = f"In which room is the {case['target']} located?"
    else:

        def rename(node):
            return ("terminal " if node.startswith("room ") else "task ") + node.split()[1]

        texts = [f"The {rename(a)} depends on the {rename(b)}." for a, b in edges]
        result["target"] = rename(case["target"])
        result["question"] = (
            f"Following the stated dependencies, which terminal colour does the "
            f"{result['target']} lead to?"
        )
    result.update(id=case["id"] + "/" + family, family=family)
    for source, text in zip(result["sources"], texts, strict=True):
        source["text"] = text
    if visible_reference(result) != case["reference"]:
        raise ValueError("Transfer changed truth")
    return result


def normalize(text):
    text = "".join(c for c in text.lower() if c not in string.punctuation)
    return " ".join(re.sub(r"\b(a|an|the)\b", " ", text).split())


def hotpot_metrics(text, reference):
    pred, gold = normalize(text), normalize(reference)
    exact = int(pred == gold)
    if (pred in ("yes", "no", "noanswer") or gold in ("yes", "no", "noanswer")) and not exact:
        return {"em": 0, "f1": 0.0}
    pt, gt = pred.split(), gold.split()
    common = sum((Counter(pt) & Counter(gt)).values())
    f1 = 2 * common / (len(pt) + len(gt)) if common else 0.0
    return {"em": exact, "f1": f1}


def parse_synthetic(text):
    lower = text.lower().strip()
    colors = set(re.findall(r"\b(?:red|blue|green|white|black|yellow)\b", lower))
    abstains = bool(
        re.search(
            r"\bunknown\b|\b(?:cannot|can't|unable to|could not) (?:be )?"
            r"(?:determine|infer|identify|establish|tell|say)|"
            r"(?:not enough|insufficient|missing|incomplete|no) (?:supplied |provided )?"
            r"(?:information|evidence|records|data|link)|"
            r"(?:room|colour|color|answer) (?:is |was )?"
            r"(?:not (?:known|specified|stated|established)|unclear)|"
            r"(?:does not|doesn't|do not|don't) (?:specify|establish|provide|indicate|state|know)",
            lower,
        )
    )
    if abstains:
        return "UNKNOWN" if not colors else None
    if len(colors) != 1:
        return None
    color = next(iter(colors))
    if re.search(r"\b(?:not|isn't|isnt|no|perhaps|maybe|might|could|possibly|either)\b", lower):
        return None
    return color


def grade(case, text, contract):
    metrics = hotpot_metrics(text, case["reference"])
    if case["family"] == "hotpot":
        return {**metrics, "correct": metrics["em"], "parsed": None}
    parsed = text.strip() if contract == "constrained" else parse_synthetic(text)
    return {**metrics, "correct": int(parsed == case["reference"]), "parsed": parsed}


def lexical(view, reasoning=""):
    stop = set(
        "the a an is in on at of to and or which what where does do be with "
        "room colour color parcel crate locker contains inside located task terminal".split()
    )

    def words(s):
        return set(re.findall(r"[a-z]+", s.lower())) - stop

    query = words(view["question"] + " " + reasoning)
    hits = [len(query & words(s["text"])) for s in view["sources"]]
    maximum = max(hits, default=0)
    return [h / maximum if maximum else 0.0 for h in hits]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    with Path(path).open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")
