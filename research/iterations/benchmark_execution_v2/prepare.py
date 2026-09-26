"""R27 private/public freezes; test references are never needed by inference."""

import argparse
import json
import random
import runpy
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
A = runpy.run_path(str(HERE.parent / "selective_benchmarks/admission.py"))
C, F = A["C"], A["F"]
K = runpy.run_path(str(HERE / "contract.py"))
OLD = ROOT / "research/protocols/selective-admission-v1"


def pilot_cases():
    cases = json.loads((OLD / "cases.json").read_text())
    refs = {r["id"]: r for r in json.loads((OLD / "references.json").read_text())}
    selected = []
    for task, count in [("arc", 4), ("gsm8k", 3), ("mmlu_pro", 5), ("musr", 3), ("ifbench", 3)]:
        group = [c for c in cases if c["task"] == task]
        if task == "musr":
            for family in sorted({c["family"] for c in group}):
                selected += sorted(
                    [c for c in group if c["family"] == family],
                    key=lambda c: C["digest"]("r27-pilot/" + c["id"]),
                )[:1]
        else:
            selected += sorted(group, key=lambda c: C["digest"]("r27-pilot/" + c["id"]))[:count]
    converted, references = [], []
    for case in selected:
        ref = refs[case["id"]]
        if case["split"] != "development" or ref["prompt_sha256"] != C["digest"](case["prompt"]):
            raise ValueError("Exposed pilot binding mismatch")
        body = case["prompt"]
        if case["format"] in K["SUFFIX"]:
            body, sep, _ = body.rpartition("\n\nSolve the problem. ")
            if not sep:
                raise ValueError("Unknown old task suffix")
        new = case | {"prompt": K["task_prompt"](body, case["format"])}
        converted.append(new)
        references.append(ref | {"prompt_sha256": C["digest"](new["prompt"])})
    return converted, references


def gpqa_case(row, index):
    options = [row[f"Incorrect Answer {i}"] for i in range(1, 4)] + [row["Correct Answer"]]
    if any(not isinstance(o, str) or not o.strip() for o in options) or len(set(options)) != 4:
        raise ValueError("Invalid GPQA options")
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


def source_hashes():
    files = [
        *HERE.glob("*.py"),
        ROOT / "research/benchmark-execution-v2-plan.md",
        ROOT / "research/evaluation/choice_readout_v2.py",
    ]
    return A["source_hashes"]() | {str(p.relative_to(ROOT)): C["sha"](p) for p in sorted(files)}


def freeze(folder, cases, refs, *, scope, max_seconds, reserve, prior_spend, upstream=None):
    if not cases or len({c["id"] for c in cases}) != len(cases):
        raise ValueError("Empty or duplicate case list")
    if len(cases) != len(refs):
        raise ValueError("Incomplete references")
    if not 0 < reserve <= 110 - prior_spend or not 0 < max_seconds <= 24 * 3600:
        raise ValueError("Invalid stage budget")
    for c, r in zip(cases, refs, strict=True):
        C["validate_case"](c)
        if c["id"] != r["id"] or C["digest"](c["prompt"]) != r["prompt_sha256"]:
            raise ValueError("Reference binding mismatch")
    folder.mkdir(parents=True, exist_ok=False)
    C["dump"](folder / "cases.json", cases)
    C["dump"](folder / "references.json", refs)
    previous = json.loads((OLD / "manifest.json").read_text())
    for item in previous["checkpoints"].values():
        shutil.copyfile(OLD / item["file"], folder / item["file"])
    manifest = dict(
        protocol="r27-benchmark-execution-v2",
        at=F["now"](),
        sources=source_hashes(),
        datasets={"cases.json": C["sha"](folder / "cases.json")},
        references_sha256=C["sha"](folder / "references.json"),
        checkpoints=previous["checkpoints"],
        models=A["MODELS"],
        seed=2701,
        batch_size=1,
        repair_limit=2048,
        input_limit=16384,
        layer=19,
        max_seconds=max_seconds,
        jev="jev-1.13.0",
        jev_cap=0.25,
        usd_per_million=0.042,
        prior_spend_usd=prior_spend,
        cumulative_cap_usd=110,
        stage_reserve_usd=reserve,
        scope=scope,
        upstream=upstream or {},
        output_contract="terminal-line-v2",
        source_revision=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        source_dirty=bool(
            subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()
        ),
    )
    A["verify_bindings"](folder, manifest)
    C["dump"](folder / "manifest.json", manifest)
    return manifest


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--pilot", type=Path, required=True)
    args = p.parse_args()
    cs, rs = pilot_cases()
    freeze(
        args.pilot,
        cs,
        rs,
        scope="exposed development engineering pilot",
        max_seconds=6300,
        reserve=5,
        prior_spend=46.17349123025742,
    )
