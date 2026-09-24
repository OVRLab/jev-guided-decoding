"""Private preparation for full short tasks, with explicit development exposure."""

import ast
import re
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P = runpy.run_path(str(ROOT / "research/iterations/benchmark_execution_v2/prepare.py"))
C, K = P["C"], P["K"]


def pair(ident, task, family, body, kind, reference, *, cluster=None, exposed=False):
    prompt = K["task_prompt"](body, kind)
    case = dict(
        id=ident,
        task=task,
        family=family,
        prompt=prompt,
        format=kind,
        origin_id=ident.split("/", 1)[1],
        cluster=cluster or ident,
        split="development" if exposed else "test",
    )
    C["validate_case"](case)
    return case, dict(id=ident, prompt_sha256=C["digest"](prompt), **reference)


def ifbench_case(row, exposed_ids):
    ident = f"ifbench/{row['key']}"
    return pair(
        ident,
        "ifbench",
        "instruction_following",
        row["prompt"],
        "instruction",
        {"kind": "ifbench", **{k: row[k] for k in ("key", "instruction_id_list", "kwargs")}},
        exposed=ident in exposed_ids,
    )


def story_clusters(rows, family):
    """Conservative related-story grouping from narrative only, never reference labels.

    Same normalized first 150 characters joins shared settings even when their
    evidence differs. >=0.65 five-word-shingle Jaccard also joins near duplicates.
    This is a documented heuristic, not proof of semantic independence.
    """
    normalized = [" ".join(r["narrative"].casefold().split()) for r in rows]
    starts = [s[:150] for s in normalized]
    shingles = []
    for text in normalized:
        words = re.findall(r"\w+", text)
        shingles.append({tuple(words[i : i + 5]) for i in range(max(0, len(words) - 4))})
    parent = list(range(len(rows)))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(rows)):
        for j in range(i):
            a, b = shingles[i], shingles[j]
            same = normalized[i] == normalized[j] or (
                len(starts[i]) == 150 and starts[i] == starts[j]
            )
            similar = bool(a and b) and len(a & b) / len(a | b) >= 0.65
            if same or similar:
                x, y = root(i), root(j)
                parent[max(x, y)] = min(x, y)
    return [f"musr/{family}/story-{root(i)}" for i in range(len(rows))]


def musr_case(row, family, index, cluster, exposed_clusters):
    if family not in {"murder_mystery", "object_placements", "team_allocation"}:
        raise ValueError("Unknown MuSR family")
    options = ast.literal_eval(row["choices"])
    answer = int(row["answer_index"])
    if (
        not isinstance(options, list)
        or not 2 <= len(options) <= 26
        or any(not isinstance(o, str) or not o.strip() for o in options)
        or not 0 <= answer < len(options)
        or row["answer_choice"] != options[answer]
    ):
        raise ValueError("MuSR answer/options mismatch")
    body = (
        row["narrative"]
        + "\n\n"
        + row["question"]
        + "\n\n"
        + "\n".join(f"{chr(65 + i)}. {o}" for i, o in enumerate(options))
    )
    return pair(
        f"musr/{family}/{index}",
        "musr",
        family,
        body,
        "choice",
        dict(kind="choice", options=options, answer=chr(65 + answer)),
        cluster=cluster,
        exposed=cluster in exposed_clusters,
    )


def aime_case(row):
    answer = row["answer"]
    if type(answer) is not int or not 0 <= answer <= 999:
        raise ValueError("Invalid AIME answer")
    return pair(
        f"aime2026/{row['id']}",
        "aime2026",
        "competition_math",
        row["problem"],
        "number",
        dict(kind="number", answer=str(answer)),
    )
