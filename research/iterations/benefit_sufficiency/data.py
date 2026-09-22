"""Fresh three-way cohorts; original reference-free prompt and frozen R18 graders."""

import hashlib
import json
import random
import re
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OLD = runpy.run_path(str(HERE.parent / "boundary_attention/data.py"))
public_view, dump, sha, grade, domain, quality = (
    OLD[k] for k in ("public_view", "dump", "sha", "grade", "domain", "quality")
)
SEEDS = dict(fit=190922831, calibration=190922839, test=290922853)


def historical():
    rows = []
    for p in sorted((ROOT / "research/protocols").glob("*/*.json")):
        if p.parent.name == "benefit-sufficiency-v1":
            continue
        value = json.loads(p.read_text())
        if isinstance(value, list):
            rows.extend(c for c in value if isinstance(c, dict))
    return rows


def synthetic(split, count):
    function = runpy.run_path(str(HERE.parent / "selective_attention/data.py"))["synthetic"]
    previous = frozenset(re.findall(r"(?:parcel|crate|locker|task) ([a-z]{8})", str(historical())))
    function.__globals__["prior_names"] = lambda: previous
    function.__globals__["SEEDS"] = dict(development=SEEDS[split], test=SEEDS[split])
    rows = function("test" if split == "test" else "development", count)
    for row in rows:
        row["id"] = (
            row["id"].replace("r17/development/", f"r19/{split}/").replace("r17/test/", "r19/test/")
        )
        row["world_id"] = (
            row["world_id"]
            .replace("r17/development/", f"r19/{split}/")
            .replace("r17/test/", "r19/test/")
        )
        row["split"] = split
    return rows


def cohorts(tokenizer, hotpot, squad):
    R = runpy.run_path(str(HERE / "runtime.py"))
    previous = historical()
    excluded = {c["upstream_id"] for c in previous if "upstream_id" in c}
    excluded_articles = {c["article"] for c in previous if "article" in c}
    eligibility = []

    def eligible(c):
        try:
            n = len(R["encode"](tokenizer, public_view(c))["input_ids"])
        except ValueError as exc:
            if str(exc) != "Input context limit":
                raise
            n = 3073
        valid = 1 <= len(c["sources"]) <= 32 and n <= 3072
        eligibility.append(
            dict(id=c["id"], prompt_tokens=n, sources=len(c["sources"]), eligible=valid)
        )
        return valid

    result = {s: synthetic(s, n) for s, n in [("fit", 108), ("calibration", 72), ("test", 144)]}
    raw = sorted(json.loads(hotpot.read_text()), key=lambda r: r["id"])
    random.Random(190922857).shuffle(raw)
    selected = []
    for row in raw:
        if row["id"] in excluded:
            continue
        sources = [
            dict(id=f"D{i + 1:02}", text=title + ": " + "".join(sentences))
            for i, (title, sentences) in enumerate(
                zip(row["context"]["title"], row["context"]["sentences"], strict=True)
            )
        ]
        if len(sources) != 10:
            continue
        ident = "r19/hotpot/" + row["id"]
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
        )
        if eligible(c):
            selected.append(c)
        if len(selected) == 280:
            break
    if len(selected) != 280:
        raise ValueError("Insufficient fresh Hotpot inputs")
    for split, group in [
        ("fit", selected[:72]),
        ("calibration", selected[72:120]),
        ("test", selected[120:]),
    ]:
        result[split].extend(group)
    articles = sorted(
        [a for a in json.loads(squad.read_text())["data"] if a["title"] not in excluded_articles],
        key=lambda a: a["title"],
    )
    random.Random(190922859).shuffle(articles)
    article_split = {}
    for split, group, desired in [
        ("fit", articles[:30], 40),
        ("calibration", articles[30:60], 40),
        ("test", articles[60:], 80),
    ]:
        pool = []
        for article in group:
            article_split[article["title"]] = split
            for i, paragraph in enumerate(article["paragraphs"]):
                for q in paragraph["qas"]:
                    if q["id"] in excluded:
                        continue
                    ident = "r19/squad2/" + q["id"]
                    refs = sorted({a["text"] for a in q["answers"]})
                    pool.append(
                        dict(
                            id=ident,
                            world_id=ident,
                            cluster_id=article["title"],
                            upstream_id=q["id"],
                            paragraph_id=f"{article['title']}/{i}",
                            family="squad2",
                            article=article["title"],
                            question=q["question"],
                            sources=OLD["sentence_sources"](paragraph["context"]),
                            original_context_sha256=hashlib.sha256(
                                paragraph["context"].encode()
                            ).hexdigest(),
                            reference=refs[0] if refs else "",
                            references=refs,
                            missing=q["is_impossible"],
                            condition="original_passage",
                        )
                    )
        random.Random("r19-squad/" + split).shuffle(pool)
        seen, counts = set(), [0, 0]
        for c in pool:
            cls = int(c["missing"])
            if counts[cls] >= desired or c["paragraph_id"] in seen:
                continue
            if eligible(c):
                result[split].append(c)
                seen.add(c["paragraph_id"])
                counts[cls] += 1
            if counts == [desired, desired]:
                break
        if counts != [desired, desired]:
            raise ValueError("Insufficient fresh SQuAD paragraphs")
    for split, rows in result.items():
        for c in rows:
            c["split"] = split
    if [len(result[k]) for k in ("fit", "calibration", "test")] != [260, 200, 608]:
        raise ValueError("Cohort count mismatch")
    all_rows = sum(result.values(), [])
    if len({c["id"] for c in all_rows}) != len(all_rows):
        raise ValueError("Duplicate cases")
    aliases = [
        set(re.findall(r"(?:parcel|crate|locker|task) ([a-z]{8})", str(result[s]))) for s in result
    ]
    if any(a & b for i, a in enumerate(aliases) for b in aliases[i + 1 :]):
        raise ValueError("Cross-split alias overlap")
    return result, eligibility, article_split
