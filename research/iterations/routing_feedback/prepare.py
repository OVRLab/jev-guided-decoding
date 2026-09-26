"""Freeze IFEval data and sources; inference export contains no grading metadata."""

import argparse
import json
import re
import runpy
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
C = runpy.run_path(str(HERE / "common.py"))
F = runpy.run_path(str(HERE / "feedback.py"))
ROOT = C["ROOT"]
A = runpy.run_path(str(HERE.parent / "selective_benchmarks/admission.py"))


def normalize(text):
    return " ".join(text.casefold().split())


def overlap(rows, prior_paths):
    previous = set()
    for path in prior_paths:
        value = json.loads(path.read_text())
        if isinstance(value, list):
            previous.update(
                normalize(c["prompt"])
                for c in value
                if isinstance(c, dict) and isinstance(c.get("prompt"), str)
            )

    def shingles(text):
        words = re.findall(r"\w+", text)
        return {tuple(words[i : i + 5]) for i in range(max(0, len(words) - 4))}

    old_shingles = [shingles(p) for p in previous]
    exact, near = [], []
    for row in rows:
        text = normalize(row["prompt"])
        if text in previous:
            exact.append(row["key"])
        s = shingles(text)
        if s and any(t and len(s & t) / len(s | t) >= 0.65 for t in old_shingles):
            near.append(row["key"])
    return dict(
        unique_prior_prompts=len(previous),
        exact_keys=sorted(exact),
        near_keys=sorted(near),
        near_rule="five-word shingle Jaccard >= 0.65",
    )


def freeze(upstream, prior_paths, checkpoint_folder, output):
    C["admit_cost"](103.82976781335556, 18.5, 125)
    rows = [json.loads(s) for s in (upstream / "data/input_data.jsonl").read_text().splitlines()]
    if len(rows) != 541 or len({r["key"] for r in rows}) != 541:
        raise ValueError("Unexpected upstream coverage")
    overlaps = overlap(rows, prior_paths)
    selected = [
        r for r in rows if r["key"] not in overlaps["exact_keys"] and r["key"] not in {1122, 1129}
    ]
    cases, refs = [], []
    for row in selected:
        ident = f"ifeval/{row['key']}"
        case = dict(
            id=ident,
            task="ifeval",
            family="instruction_following",
            prompt=row["prompt"],
            format="instruction",
            origin_id=str(row["key"]),
            cluster=ident,
            split="test",
        )
        C["validate_case"](case)
        cases.append(case)
        refs.append(dict(id=ident, prompt_sha256=C["digest"](row["prompt"]), **row))
    output.mkdir(parents=True, exist_ok=False)
    private = output.parent / (output.name + "-grading")
    private.mkdir(mode=0o700, exist_ok=False)
    C["dump"](private / "references.json", refs)
    shutil.copytree(upstream, private / "instruction_following_eval")
    C["dump"](output / "cases.json", cases)
    previous = json.loads((checkpoint_folder / "manifest.json").read_text())
    ckpt = previous["checkpoints"]["live"]
    shutil.copyfile(checkpoint_folder / ckpt["file"], output / ckpt["file"])
    source_paths = sorted(
        set(
            [
                *list((ROOT / "research").rglob("*.py")),
                *list((ROOT / "src").rglob("*.py")),
                ROOT / "research/routing-feedback-plan-v1.md",
                ROOT / "uv.lock",
                ROOT / "pyproject.toml",
            ]
        )
    )
    evaluator = {
        str(p.relative_to(private / "instruction_following_eval")): C["sha"](p)
        for p in (private / "instruction_following_eval").rglob("*")
        if p.is_file()
    }
    manifest = dict(
        protocol="r28-routing-feedback-v1",
        at=F["now"](),
        sources={str(p.relative_to(ROOT)): C["sha"](p) for p in source_paths},
        datasets={"cases.json": C["sha"](output / "cases.json")},
        references_sha256=C["sha"](private / "references.json"),
        evaluator=evaluator,
        checkpoints={"live": ckpt},
        model=A["MODELS"]["granite_4_0_1b"],
        upstream_commit="e6890f85757dd84e27ca6df2dd30651dafad28e0",
        overlap=overlaps,
        eligible_cases=len(cases),
        layer=19,
        seed=2801,
        limit=2048,
        max_seconds=11 * 3600,
        jev="jev-1.13.0",
        jev_cap=0.25,
        usd_per_million=0.042,
        cumulative_cap_usd=125,
        prior_conservative_usd=103.82976781335556,
        reserve_usd=18.5,
        source_revision=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        source_dirty=bool(
            subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()
        ),
    )
    A["verify_bindings"](output, manifest)
    C["dump"](output / "manifest.json", manifest)
    return dict(
        eligible=len(cases), overlap=overlaps, manifest_sha256=C["sha"](output / "manifest.json")
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--upstream", type=Path, required=True)
    p.add_argument("--prior", type=Path, action="append", default=[])
    p.add_argument("--checkpoints", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    print(json.dumps(freeze(args.upstream, args.prior, args.checkpoints, args.output)))
