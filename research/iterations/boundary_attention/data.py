"""Fresh R18 authored worlds and disclosed natural-answer SQuAD adaptation."""

import re
import runpy
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OLD = runpy.run_path(str(Path(__file__).resolve().parents[1] / "selective_attention/data.py"))
public_view, dump, sha = (OLD[k] for k in ("public_view", "dump", "sha"))
normalize = OLD["OLD"]["normalize"]


def prior_names():
    used = set(OLD["prior_names"]())
    for p in (ROOT / "research/protocols/selective-attention-v1").glob("*.json"):
        used.update(re.findall(r"(?:parcel|crate|locker|task) ([a-z]{8})", p.read_text()))
    return frozenset(used)


def synthetic(split, count):
    # Instantiate the immutable R17 generator in a private namespace with fresh seeds.
    function = runpy.run_path(
        str(Path(__file__).resolve().parents[1] / "selective_attention/data.py")
    )["synthetic"]
    function.__globals__["SEEDS"] = {"development": 180922711, "test": 280922713}
    function.__globals__["prior_names"] = prior_names
    result = function(split, count)
    for row in result:
        row["id"] = row["id"].replace("r17/", "r18/", 1)
        row["world_id"] = row["world_id"].replace("r17/", "r18/", 1)
    return result


def sentence_sources(paragraph):
    units = re.split(r"(?<=[.!?])(?=\s+)", paragraph)
    return [{"id": f"S{i + 1:02}", "text": text} for i, text in enumerate(units) if text.strip()]


def abstention(text):
    value = text.lower().strip()
    if not value or len(value) > 350:
        return False
    prefix = (
        r"the (?:provided |supplied )?(?:evidence|context|passage|text|information) "
        r"(?:does not|doesn\x27t) "
        r"(?:state|establish|provide|indicate|mention|specify|contain|say|give)"
        r"|(?:there is |there\x27s )?(?:not enough|insufficient|no) (?:information|evidence)"
        r"|(?:it )?(?:cannot|can\x27t) be determined"
        r"|(?:i |we )?(?:cannot|can\x27t|could not|am unable to|are unable to) "
        r"(?:determine|infer|establish|answer|tell)"
        r"|the answer is (?:unknown|not (?:stated|provided|specified|established))"
        r"|not (?:stated|specified|provided) in the (?:context|passage|text|evidence)"
    )
    return value in ("unknown", "unknown.") or bool(
        re.fullmatch(r"(?:" + prefix + r")[^.!?]*[.]?", value)
    )


def span_metrics(prediction, reference):
    pred, gold = normalize(prediction), normalize(reference)
    exact = int(pred == gold)
    p, g = pred.split(), gold.split()
    if not p or not g:
        return dict(em=exact, f1=float(exact))
    common = sum((Counter(p) & Counter(g)).values())
    return dict(em=exact, f1=2 * common / (len(p) + len(g)))


def grade(case, text):
    if case["family"] != "squad2":
        return OLD["grade"](case, text, "open_explicit")
    refs = case["references"] or [""]
    raw = [span_metrics(text, ref) for ref in refs]
    abstained = abstention(text)
    mapped = "" if abstained else text
    metrics = [span_metrics(mapped, ref) for ref in refs]
    em = max(x["em"] for x in metrics) if text.strip() else 0
    f1 = max(x["f1"] for x in metrics) if text.strip() else 0.0
    return dict(
        correct=em,
        em=em,
        f1=f1,
        raw_em=max(x["em"] for x in raw),
        raw_f1=max(x["f1"] for x in raw),
        abstained=abstained,
        parsed=None,
    )


def domain(case):
    return case["family"] if case["family"] in ("hotpot", "squad2") else "synthetic"


def quality(case, scored):
    return scored["correct"] if domain(case) == "synthetic" else scored["f1"]
