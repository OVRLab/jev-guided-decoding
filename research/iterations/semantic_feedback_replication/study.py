"""R21B changes only the cohort and manifest verifier of the frozen R21A runtime."""

import argparse
import asyncio
import json
import runpy
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
S = runpy.run_path(str(HERE.parent / "semantic_feedback/study.py"))
D = runpy.run_path(str(HERE / "data.py"))


def source_hashes():
    sources = S["source_hashes"]()
    for p in [*HERE.glob("*.py"), ROOT / "research/semantic-feedback-replication.md"]:
        sources[str(p.relative_to(ROOT))] = S["sha"](p)
    return dict(sorted(sources.items()))


def verify(folder):
    m = json.loads((folder / "manifest.json").read_text())
    if m["sources"] != source_hashes() or any(
        S["sha"](folder / n) != h for n, h in m["datasets"].items()
    ):
        raise ValueError("Replication source/data freeze mismatch")
    return m


def prepare(folder):
    folder.mkdir(parents=True, exist_ok=False)
    prior = ROOT / "research/protocols/semantic-feedback-v1"
    old = json.loads((prior / "cases.json").read_text())
    excluded = {n for c in old for n in [*c["people"], c["parcel"].removeprefix("Parcel-")]}
    cases = D["worlds"](384, excluded=excluded)
    m = json.loads((prior / "manifest.json").read_text())
    S["dump"](folder / "cases.json", cases)
    m.update(
        protocol="r21b-semantic-feedback-replication-v1",
        at=S["J"]["now"](),
        source_revision=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        dirty=bool(
            subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()
        ),
        sources=source_hashes(),
        datasets={"cases.json": S["sha"](folder / "cases.json")},
        cases=len(cases),
        prior_spend_usd=32.56217300454077,
        predecessor_manifest_sha256=S["sha"](prior / "manifest.json"),
    )
    S["dump"](folder / "manifest.json", m)
    return m


async def execute(folder, output, device, key_file=None):
    # runpy creates an isolated namespace; no original module/file is mutated.
    # Preserve all generation/scoring/budget behavior and bind only this new freeze.
    S["execute"].__globals__["verify"] = verify
    await S["execute"](folder, output, device, key_file)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=("prepare", "run"))
    p.add_argument("--freeze", type=Path, required=True)
    p.add_argument("--output", type=Path)
    p.add_argument("--device", choices=("mps", "cuda", "cpu"), default="mps")
    a = p.parse_args()
    if a.command == "prepare":
        print(json.dumps(prepare(a.freeze), indent=2))
    elif a.output is None:
        p.error("--output required")
    else:
        asyncio.run(execute(a.freeze, a.output, a.device))


if __name__ == "__main__":
    main()
