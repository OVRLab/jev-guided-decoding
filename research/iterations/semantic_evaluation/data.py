"""R20 fresh cohorts, excluding previous questions, articles and authored aliases."""

import hashlib
import json
import random
import re
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
D = runpy.run_path(str(HERE.parent / "benefit_sufficiency/data.py"))
R = runpy.run_path(str(HERE.parent / "benefit_sufficiency/runtime.py"))


def previous():
    rows = []
    for p in sorted((ROOT / "research/protocols").glob("*/*.json")):
        if p.parent.name.startswith("semantic-evaluation"):
            continue
        v = json.loads(p.read_text())
        if isinstance(v, list):
            rows.extend(c for c in v if isinstance(c, dict))
    return rows


def cohorts(tokenizer, hotpot, squad):
    old = previous()
    ids = {c["upstream_id"] for c in old if "upstream_id" in c}
    articles = {c["article"] for c in old if "article" in c}
    names = set(re.findall(r"(?:parcel|crate|locker|task) ([a-z]{8})", str(old)))
    f = runpy.run_path(str(HERE.parent / "selective_attention/data.py"))["synthetic"]
    f.__globals__["SEEDS"] = dict(development=203092311, test=203092313)
    f.__globals__["prior_names"] = lambda: frozenset(names)
    cases = f("test", 144)
    for c in cases:
        c["id"] = c["id"].replace("r17/", "r20/")
        c["world_id"] = c["world_id"].replace("r17/", "r20/")
        c["references"] = [] if c["missing"] else [c["reference"]]
    eligibility = []

    def eligible(c):
        try:
            n = len(R["encode"](tokenizer, D["public_view"](c))["input_ids"])
        except ValueError as exc:
            if str(exc) != "Input context limit":
                raise
            n = 3073
        ok = 1 <= len(c["sources"]) <= 32 and n <= 3072
        eligibility.append(dict(id=c["id"], tokens=n, sources=len(c["sources"]), eligible=ok))
        return ok

    for c in cases:
        if not eligible(c):
            raise ValueError("Authored input ineligible")
    raw = sorted(json.loads(hotpot.read_text()), key=lambda c: c["id"])
    random.Random(203092317).shuffle(raw)
    count = 0
    for row in raw:
        if row["id"] in ids:
            continue
        sources = [
            dict(id=f"D{i + 1:02}", text=t + ": " + "".join(ss))
            for i, (t, ss) in enumerate(
                zip(row["context"]["title"], row["context"]["sentences"], strict=True)
            )
        ]
        if len(sources) != 10:
            continue
        ident = "r20/hotpot/" + row["id"]
        c = dict(
            id=ident,
            world_id=ident,
            upstream_id=row["id"],
            family="hotpot",
            question=row["question"],
            sources=sources,
            reference=row["answer"],
            references=[row["answer"]],
            missing=False,
            condition="distractor",
            question_type=row["type"],
            split="test",
        )
        if eligible(c):
            cases.append(c)
            count += 1
        if count == 120:
            break
    if count != 120:
        raise ValueError("Insufficient fresh Hotpot cases")
    pool = []
    for article in json.loads(squad.read_text())["data"]:
        if article["title"] in articles:
            continue
        for i, p in enumerate(article["paragraphs"]):
            for q in p["qas"]:
                if q["id"] in ids:
                    continue
                ident = "r20/squad2/" + q["id"]
                refs = sorted({a["text"] for a in q["answers"]})
                pool.append(
                    dict(
                        id=ident,
                        world_id=ident,
                        upstream_id=q["id"],
                        family="squad2",
                        article=article["title"],
                        cluster_id=article["title"],
                        paragraph_id=f"{article['title']}/{i}",
                        question=q["question"],
                        sources=D["OLD"]["sentence_sources"](p["context"]),
                        reference=refs[0] if refs else "",
                        references=refs,
                        missing=q["is_impossible"],
                        original_context_sha256=hashlib.sha256(p["context"].encode()).hexdigest(),
                        split="test",
                        condition="original_passage",
                    )
                )
    random.Random(203092319).shuffle(pool)
    seen = set()
    counts = [0, 0]
    for c in pool:
        cls = int(c["missing"])
        if counts[cls] >= 60 or c["paragraph_id"] in seen:
            continue
        if eligible(c):
            cases.append(c)
            seen.add(c["paragraph_id"])
            counts[cls] += 1
        if counts == [60, 60]:
            break
    if counts != [60, 60] or len(cases) != 528:
        raise ValueError("Cohort count mismatch")
    if len({c["id"] for c in cases}) != len(cases):
        raise ValueError("Duplicate case")
    if ids & {c.get("upstream_id") for c in cases}:
        raise ValueError("Historical question overlap")
    if articles & {c.get("article") for c in cases}:
        raise ValueError("Historical article overlap")
    fresh = set(re.findall(r"(?:parcel|crate|locker|task) ([a-z]{8})", str(cases)))
    if names & fresh:
        raise ValueError("Historical authored alias overlap")
    return cases, eligibility
