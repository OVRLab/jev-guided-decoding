"""Download immutable public datasets and separate adaptation from fresh evaluation."""

import argparse
import io
import json
import re
import runpy
import subprocess
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
C = runpy.run_path(str(HERE / "common.py"))
ROOT = C["ROOT"]
PINS = {
    "gsm8k": ("openai/gsm8k", "740312add88f781978c0658806c59bc2815b9866", "main"),
    "arc": ("allenai/ai2_arc", "210d026faf9955653af8916fad021475a3f00453", "ARC-Challenge"),
}


def select(candidates, exposed):
    seen = set(exposed)
    result, excluded = [], []
    for task in ("gsm8k", "arc"):
        for split, n in [("train", 192), ("development", 32), ("test", 96)]:
            group = sorted(
                [x for x in candidates if x[0]["task"] == task and x[0]["split"] == split],
                key=lambda x: C["digest"]("r25/" + x[0]["id"]),
            )
            selected = []
            for case, ref, target, question in group:
                norm = C["normalize"](question)
                if norm in seen:
                    excluded.append(
                        dict(id=case["id"], reason="normalized question duplicate or exposed")
                    )
                    continue
                seen.add(norm)
                selected.append((case, ref, target))
                if len(selected) == n:
                    break
            if len(selected) != n:
                raise ValueError("Insufficient disjoint cases")
            result.extend(selected)
    return result, excluded


def prepare(folder, upstream):
    import pyarrow.parquet as pq

    folder.mkdir(parents=True, exist_ok=False)
    upstream.mkdir(parents=True, exist_ok=True)
    candidates, origins = [], {}
    for task, (repo, rev, config) in PINS.items():
        for split in ("train", "test") if task == "gsm8k" else ("train", "validation", "test"):
            url = f"https://huggingface.co/datasets/{repo}/resolve/{rev}/{config}/{split}-00000-of-00001.parquet"
            blob = urllib.request.urlopen(url, timeout=60).read()
            path = upstream / f"{task}-{split}.parquet"
            path.write_bytes(blob)
            origins[f"{task}/{split}"] = dict(url=url, sha256=C["sha"](path))
            for i, r in enumerate(pq.read_table(io.BytesIO(blob)).to_pylist()):
                question = r["question"]
                if task == "gsm8k":
                    ident = f"gsm8k/{split}/{i}"
                    prompt = (
                        question
                        + "\n\nReason through the problem and finish with a separate line: "
                        "#### <numeric answer>."
                    )
                    ref = dict(
                        kind="number",
                        answer=r["answer"].rsplit("####", 1)[1].strip().replace(",", ""),
                    )
                    target = re.sub(r"<<.*?>>", "", r["answer"])
                    parts = ("train", "development") if split == "train" else ("test",)
                else:
                    ident = f"arc/{split}/{r['id']}"
                    choices = r["choices"]
                    texts = list(choices["text"])
                    labels = list(choices["label"])
                    answer = chr(65 + labels.index(r["answerKey"]))
                    prompt = (
                        question
                        + "\n\n"
                        + "\n".join(f"{chr(65 + j)}. {v}" for j, v in enumerate(texts))
                        + "\n\nReason through the problem and finish with a separate line: "
                        "Final: <letter>."
                    )
                    ref = dict(kind="choice", answer=answer, choices=len(texts))
                    target = "Final: " + answer
                    parts = (
                        {"train": "train", "validation": "development", "test": "test"}[split],
                    )
                for part in parts:
                    case = dict(
                        id=ident, task=task, split=part, prompt=prompt, origin=f"{split}/{i}"
                    )
                    C["validate_case"](case)
                    candidates.append(
                        (
                            case,
                            dict(id=ident, prompt_sha256=C["digest"](prompt), **ref),
                            target,
                            question,
                        )
                    )
    old = json.loads((ROOT / "research/protocols/public-baseline-v1/cases.json").read_text())
    exposed = {
        C["normalize"](c["prompt"].split("\n\nReason through the problem")[0])
        for c in old
        if c["task"] == "gsm8k_train"
    }
    chosen, excluded = select(candidates, exposed)
    if len({x[0]["id"] for x in chosen}) != len(chosen):
        raise ValueError("Split ID overlap")
    cases = [c for c, _, _ in chosen]
    C["dump"](folder / "cases.json", cases)
    for part in ("train", "development", "test"):
        C["dump"](
            folder / f"{part}-references.json", [r for c, r, _ in chosen if c["split"] == part]
        )
    C["dump"](
        folder / "training-targets.json",
        [dict(id=c["id"], target=t) for c, _, t in chosen if c["split"] == "train"],
    )
    C["dump"](folder / "exclusions.json", excluded)
    C["dump"](
        folder / "manifest.json",
        dict(
            protocol="r25-gated-repair-v1",
            at=datetime.now(UTC).isoformat(),
            sources=C["sources"](),
            datasets={p.name: C["sha"](p) for p in folder.glob("*.json")},
            upstream=origins,
            source_revision=subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            model="ibm-granite/granite-4.0-1b",
            revision="6a7381ba1f54d684ff508d991aeb7dc580157103",
            jev="jev-1.13.0",
            seeds=list(C["SEEDS"]),
            rank=64,
            layer=19,
            epochs=2,
            lr=0.001,
            accumulate=8,
            clip=1.0,
            draft_limit=1024,
            repair_limit=512,
            input_limit=8192,
            target_limit=768,
            max_seconds=7 * 3600,
            jev_cap=0.25,
            usd_per_million=0.042,
            cumulative_cap=75,
            prior_estimate=36.773534922020566,
            reservation=14.40,
        ),
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--freeze", type=Path, required=True)
    p.add_argument("--upstream", type=Path, required=True)
    a = p.parse_args()
    prepare(a.freeze, a.upstream)
