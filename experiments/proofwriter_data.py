"""Offline ProofWriter selection and finite forward-rule oracle (no model grading)."""

import hashlib
import json
import random
import re
import zipfile
from collections import Counter

from jev_guided_decoding.types import Request

ARCHIVE_SHA256 = "bbc5694901e8306d0bd659aa1ad53ccfd02c201864f4b320ffa3777827d1fc26"
ARCHIVE_URL = "https://aristo-data-public.s3-us-west-2.amazonaws.com/proofwriter/proofwriter-dataset-V2020.12.3.zip"
ATOM = re.compile(r'\("([^"\\]+)" "([^"\\]+)" "([^"\\]+)" "([+~-])"\)')
VARIABLES = {"something", "someone"}
LABELS = ("ENTAILED", "CONTRADICTED", "UNKNOWN")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def atom(text):
    match = ATOM.fullmatch(text)
    if match is None:
        raise ValueError("Unsupported atom representation")
    values = match.groups()
    return (*values[:3], "-" if values[3] == "~" else values[3])


def rule(text):
    pieces = text.split(" -> ")
    if len(pieces) != 2 or not pieces[0].startswith("((") or not pieces[0].endswith(")"):
        raise ValueError("Unsupported rule representation")
    body = pieces[0][2:-1]
    matches = list(ATOM.finditer(body))
    if not matches or " ".join(m.group() for m in matches) != body:
        raise ValueError("Unsupported rule body")
    if not pieces[1].endswith(")"):
        raise ValueError("Unsupported rule head")
    return tuple(atom(m.group()) for m in matches), atom(pieces[1][:-1])


def opposite(value):
    return (*value[:3], "-" if value[3] == "+" else "+")


def derive(world):
    """Return minimal forward proof depths; negative atoms require explicit support."""
    depths = {atom(v["representation"]): 0 for v in world["triples"].values()}
    rules = [rule(v["representation"]) for v in world["rules"].values()]
    all_atoms = [*depths, *(a for body, head in rules for a in (*body, head))]
    entities = {a[0] for a in all_atoms} | {a[2] for a in all_atoms if a[1] != "is"}
    entities -= VARIABLES
    grounded = []
    for body, head in rules:
        variables = {v for a in (*body, head) for v in (a[0], a[2]) if v in VARIABLES}
        if len(variables) > 1:
            raise ValueError("Only one variable per ProofWriter rule is supported")
        for entity in sorted(entities) if variables else [None]:

            def ground(a, entity=entity, variables=variables):
                return tuple(entity if v in variables else v for v in a)

            grounded.append((tuple(map(ground, body)), ground(head)))
    changed = True
    while changed:
        changed = False
        for body, head in grounded:
            if all(a in depths for a in body):
                depth = 1 + max(depths[a] for a in body)
                if depth < depths.get(head, float("inf")):
                    depths[head] = depth
                    changed = True
    if any(opposite(a) in depths for a in depths):
        raise ValueError("Inconsistent theory cannot use three-way verdicts")
    return depths


def label_for(query, closure):
    return (
        "ENTAILED"
        if query in closure
        else "CONTRADICTED"
        if opposite(query) in closure
        else "UNKNOWN"
    )


def case_from(world, question_id, closure=None):
    closure = derive(world) if closure is None else closure
    q = world["questions"][question_id]
    query = atom(q["representation"])
    label = label_for(query, closure)
    expected = {"True": "ENTAILED", "False": "CONTRADICTED", "Unknown": "UNKNOWN"}[str(q["answer"])]
    if label != expected:
        raise ValueError(f"Source label mismatch: {world['id']}/{question_id}")
    depth = closure.get(query, closure.get(opposite(query)))
    if depth is not None and depth != q["QDep"]:
        raise ValueError(f"Source depth mismatch: {world['id']}/{question_id}")
    return {
        "id": f"{world['id']}/{question_id}",
        "theory_id": world["id"],
        "question_id": question_id,
        "claim": q["question"],
        "evidence": world["theory"],
        "label": label,
        "depth": depth,
        "source_question_depth": q["QDep"],
        "world_sha256": digest(world),
        "world": world,
    }


def request_for(case):
    return Request(
        f"Classify the claim: {case['claim']}\n"
        "Use only the supplied facts and forward rules. Require every condition. "
        "Missing facts are not false. Choose ENTAILED if the claim follows, "
        "CONTRADICTED if its explicit negation follows, or UNKNOWN if neither follows. "
        "Put only that exact label inside the final frame.",
        case["evidence"],
    )


def load_split(archive, split):
    if split not in ("test", "dev"):
        raise ValueError("Only evaluation and development splits are supported")
    with archive.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != ARCHIVE_SHA256:
            raise ValueError("Archive checksum mismatch")
    member = f"proofwriter-dataset-V2020.12.3/OWA/depth-5/meta-{split}.jsonl"
    with zipfile.ZipFile(archive) as z:
        return [json.loads(line) for line in z.read(member).splitlines()]


def select_cases(worlds, quotas, seed=20260920):
    """Sample strata in declared order; never use the same theory or text twice."""
    rng = random.Random(seed)
    buckets = {}
    ids = set()
    for world in worlds:
        if world["id"] in ids:
            raise ValueError("Duplicate theory ID")
        ids.add(world["id"])
        closure = derive(world)
        for qid in world["questions"]:
            case = case_from(world, qid, closure)
            buckets.setdefault((case["label"], case["depth"]), []).append(case)
    selected, used_ids, used_text = [], set(), set()
    for key, count in quotas.items():
        pool = sorted(buckets.get(key, []), key=lambda c: c["id"])
        rng.shuffle(pool)
        taken = 0
        for case in pool:
            if case["theory_id"] in used_ids or case["evidence"] in used_text:
                continue
            if taken == count:
                break
            selected.append(case)
            used_ids.add(case["theory_id"])
            used_text.add(case["evidence"])
            taken += 1
        if taken != count:
            raise ValueError(f"Not enough distinct theories in stratum {key}")
    rng.shuffle(selected)
    return selected


def main_quotas():
    return {
        **{
            (label, depth): 12 if depth == 5 else 11
            for depth in reversed(range(6))
            for label in LABELS[:2]
        },
        ("UNKNOWN", None): 66,
    }


def counts(cases):
    return dict(Counter(f"{c['label']}/depth={c['depth']}" for c in cases))


def verbalize(value):
    subject, verb, obj, polarity = value
    if verb == "is":
        return f"{subject} is {'not ' if polarity == '-' else ''}{obj}"
    if polarity == "+":
        return f"{subject} {verb} {obj}"
    base = {
        "chases": "chase",
        "sees": "see",
        "likes": "like",
        "visits": "visit",
        "eats": "eat",
        "needs": "need",
    }.get(verb)
    if base is None:
        raise ValueError("Unknown relation")
    return f"{subject} does not {base} {obj}"


def normalize(text):
    return re.sub(r"\bthe\s+", "", text.lower()).strip(" .")


def audit_steps(world, steps):
    """Audit only an exactly recognized leading atomic claim, never a whole proof."""
    closure = derive(world)
    premises = {atom(v["representation"]) for v in world["triples"].values()}
    atoms = set(closure) | {atom(q["representation"]) for q in world["questions"].values()}
    for body, head in map(lambda r: rule(r["representation"]), world["rules"].values()):
        atoms.update(a for a in (*body, head) if not VARIABLES.intersection(a))
    # Ground all observed predicates for observed entities, including unsupported facts.
    entities = {a[0] for a in atoms} | {a[2] for a in atoms if a[1] != "is"}
    attributes = {a[2] for a in atoms if a[1] == "is"}
    relations = {a[1] for a in atoms if a[1] != "is"}
    atoms |= {(e, "is", p, s) for e in entities for p in attributes for s in ("+", "-")}
    atoms |= {
        (e, r, o, s) for e in entities for r in relations for o in entities for s in ("+", "-")
    }
    mapping = {normalize(verbalize(a)): a for a in atoms}
    seen, rows = set(premises), []
    for step in steps:
        leading = re.sub(r"^therefore,?\s*", "", step.strip(), flags=re.I)
        leading = re.split(r":|\bbecause\b|\bsince\b|\bas\b", leading, maxsplit=1, flags=re.I)[0]
        value = mapping.get(normalize(leading))
        status = "unparsed"
        if value is not None:
            status = (
                "unsupported"
                if value not in closure
                else "premise"
                if value in premises
                else "repeated"
                if value in seen
                else "supported_new"
            )
            seen.add(value)
        rows.append(
            {
                "text": step,
                "leading_claim": leading.strip(),
                "atom": value,
                "status": status,
                "full_inference_verified": False,
            }
        )
    return rows
