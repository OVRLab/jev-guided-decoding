"""Source-preserving full GPQA inputs; no examples or references bundled here."""

import random
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P = runpy.run_path(str(ROOT / "research/iterations/benchmark_execution_v2/prepare.py"))
C, K = P["C"], P["K"]


def gpqa_case(row, index):
    options = [row[f"Incorrect Answer {i}"] for i in range(1, 4)] + [row["Correct Answer"]]
    if any(not isinstance(o, str) or not o.strip() for o in options):
        raise ValueError("Invalid blank GPQA options")
    if options.count(row["Correct Answer"]) != 1:
        raise ValueError("GPQA has an ambiguous correct option")
    # The pinned source has two repeated distractors; retain all four positions,
    # as the official loader does. Neither is a duplicate of its correct answer.
    ident = f"gpqa_diamond/{index}"
    random.Random(K["case_seed"](ident + "/shuffle", 2701)).shuffle(options)
    body = (
        row["Question"] + "\n\n" + "\n".join(f"{chr(65 + i)}. {o}" for i, o in enumerate(options))
    )
    prompt = K["task_prompt"](body, "choice")
    case = dict(
        id=ident,
        task="gpqa_diamond",
        family=row.get("Subdomain") or "science",
        prompt=prompt,
        format="choice",
        origin_id=str(index),
        cluster=ident,
        split="test",
    )
    C["validate_case"](case)
    reference = dict(
        id=ident,
        prompt_sha256=C["digest"](prompt),
        kind="choice",
        options=options,
        answer=chr(65 + options.index(row["Correct Answer"])),
    )
    return case, reference
