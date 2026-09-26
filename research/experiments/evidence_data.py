"""Authored containment worlds and an independent graph-based answer grader."""

import hashlib
import random
import re

LABELS = ("red", "blue", "green", "white", "black", "yellow", "UNKNOWN")
SEEDS = {"profile": 14092117, "calibration": 24092129, "test": 34092143}


def grade(target, edges):
    graph = {}
    for source, destination in edges:
        graph.setdefault(source, set()).add(destination)
    visited, pending, rooms = set(), [target], set()
    while pending:
        node = pending.pop()
        if node in visited:
            continue
        visited.add(node)
        if node.startswith("room "):
            rooms.add(node.removeprefix("room "))
        pending.extend(graph.get(node, ()))
    if len(rooms) > 1 or not rooms.issubset(LABELS[:-1]):
        raise ValueError("Ambiguous or invalid reference room")
    return next(iter(rooms), "UNKNOWN")


def worlds(split, count):
    if split not in SEEDS or count < 1 or count % 6:
        raise ValueError("Known split and balanced six-cell count required")
    rng = random.Random(SEEDS[split])
    results = []
    used = set()

    def alias(kind):
        while True:
            name = "".join(rng.choice("bcdfgklmnprstv") + rng.choice("aeiou") for _ in range(3))
            if name not in used:
                used.add(name)
                return f"{kind} {name}"

    for index in range(count):
        depth = index % 3 + 1
        missing = index % 6 >= 3
        target = alias("parcel")
        intermediates = [alias(kind) for kind in ("crate", "locker")[: depth - 1]]
        room = rng.choice(LABELS[:-1])
        chain = [target, *intermediates, "room " + room]
        relevant = list(zip(chain[:-1], chain[1:], strict=True))
        if missing:
            relevant.pop()
        noise = []
        for _ in range(6):
            nodes = [
                alias("parcel"),
                alias("crate"),
                alias("locker"),
                "room " + rng.choice(LABELS[:-1]),
            ]
            noise.extend(zip(nodes[:-1], nodes[1:], strict=True))
        expected = "UNKNOWN" if missing else room
        if grade(target, relevant + noise) != expected:
            raise ValueError("Construction expectation disagrees with graph grader")
        ident = hashlib.sha256(f"r14/{split}/{index}/{target}".encode()).hexdigest()[:16]
        results.append(
            dict(
                id=f"evidence/{split}/{ident}",
                index=index,
                split=split,
                depth=depth,
                missing=missing,
                target=target,
                relevant=relevant,
                noise=noise,
                reference=expected,
                ordering_seed=rng.randrange(2**31),
            )
        )
    return results


def context(world, condition):
    if condition not in ("clean", "distracted"):
        raise ValueError("Unknown context condition")
    # The light condition still includes one unrelated complete three-edge chain.
    noise = world["noise"][:3] if condition == "clean" else world["noise"]
    tagged = [(tuple(e), 1) for e in world["relevant"]] + [(tuple(e), 0) for e in noise]
    random.Random(world["ordering_seed"]).shuffle(tagged)
    sources, oracle, edges = [], [], []
    for i, (edge, relevance) in enumerate(tagged):
        source, destination = edge
        text = (
            f"The {source} is inside the {destination}."
            if world["split"] != "test"
            else f"The {destination} contains the {source}."
        )
        sources.append({"id": f"E{i + 1:02}", "text": text})
        edges.append(edge)
        oracle.append(relevance)
    return dict(
        id=world["id"] + "/" + condition,
        world_id=world["id"],
        condition=condition,
        depth=world["depth"],
        missing=world["missing"],
        target=world["target"],
        question=f"Which room contains the {world['target']}?",
        sources=sources,
        edges=edges,
        oracle_scores=oracle,
        reference=grade(world["target"], edges),
    )


def model_view(case):
    return {k: case[k] for k in ("id", "question", "sources")} | {"labels": list(LABELS)}


def lexical_scores(view):
    stop = {
        "the",
        "a",
        "is",
        "in",
        "inside",
        "which",
        "room",
        "contains",
        "parcel",
        "crate",
        "locker",
    }

    def words(text):
        return set(re.findall(r"[a-z]+", text.lower())) - stop

    query = words(view["question"])
    return [len(query & words(s["text"])) / max(1, len(query)) for s in view["sources"]]
