"""Download pinned public development sources and freeze R23 before inference.

Run with pyarrow==21.0.0 in an isolated preparation environment.
"""

import argparse
import ast
import csv
import hashlib
import io
import json
import runpy
import subprocess
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
C = runpy.run_path(str(HERE / "common.py"))
UPSTREAM = {
    "mmlu": (
        "TIGER-Lab/MMLU-Pro",
        "b189ec765aa7ed75c8acfea42df31fdae71f97be",
        "data/validation-00000-of-00001.parquet",
    ),
    "gsm": (
        "openai/gsm8k",
        "740312add88f781978c0658806c59bc2815b9866",
        "main/train-00000-of-00001.parquet",
    ),
    **{
        family: ("TAUR-Lab/MuSR", "7c365b439a222150f317764d4f16ae6c96d7d94a", family + ".csv")
        for family in ("murder_mystery", "object_placements", "team_allocation")
    },
}
IF_REV = "1c40f0c10d9b5c5c2f10a175a28007ebb64f7f4d"
MODELS = {
    "granite_4_0_1b": {
        "id": "ibm-granite/granite-4.0-1b",
        "revision": "6a7381ba1f54d684ff508d991aeb7dc580157103",
        "thinking": False,
        "do_sample": False,
        "max_new_tokens": 2048,
    },
    "granite_4_2_3b": {
        "id": "ibm-granite/granite-4.2-3b",
        "revision": "e459acceac81e5fe67c07d9cfc72329a332e7eb1",
        "thinking": True,
        "do_sample": True,
        "temperature": 1.0,
        "top_p": 0.95,
        "top_k": 0,
        "max_new_tokens": 8192,
    },
}


def sources():
    files = [
        *HERE.glob("*.py"),
        ROOT / "research/benchmark-baseline-plan.md",
        ROOT / "uv.lock",
        ROOT / "pyproject.toml",
    ]
    return {str(p.relative_to(ROOT)): C["sha"](p) for p in sorted(files)}


def prepare(folder):
    import pyarrow.parquet as pq

    folder.mkdir(parents=True, exist_ok=False)
    origins, data = {}, {}
    for name, (repo, revision, path) in UPSTREAM.items():
        url = f"https://huggingface.co/datasets/{repo}/resolve/{revision}/{path}"
        blob = urllib.request.urlopen(url, timeout=60).read()
        origins[name] = {
            "url": url,
            "sha256": hashlib.sha256(blob).hexdigest(),
            "digest_encoding": "sha256 of original bytes",
        }
        data[name] = (
            pq.read_table(io.BytesIO(blob)).to_pylist()
            if path.endswith(".parquet")
            else list(csv.DictReader(io.StringIO(blob.decode())))
        )
    url = f"https://raw.githubusercontent.com/allenai/IFBench/{IF_REV}/data/IFBench_test.jsonl"
    blob = urllib.request.urlopen(url, timeout=60).read()
    origins["ifbench"] = {
        "url": url,
        "sha256": hashlib.sha256(blob).hexdigest(),
        "digest_encoding": "sha256 of original bytes",
    }
    data["ifbench"] = [json.loads(line) for line in blob.decode().splitlines()]
    candidates = []

    def add(task, family, ident, prompt, ref):
        c = {
            "id": f"{task}/{ident}",
            "task": task,
            "family": family,
            "origin_id": str(ident),
            "prompt": prompt,
        }
        C["validate_case"](c)
        candidates.append((c, {"id": c["id"], "prompt_sha256": C["digest_text"](prompt), **ref}))

    def choice_prompt(question, options):
        return (
            question
            + "\n\n"
            + "\n".join(f"{chr(65 + i)}. {o}" for i, o in enumerate(options))
            + "\n\nReason through the problem and finish with a separate line: Final: <letter>."
        )

    for r in data["mmlu"]:
        add(
            "mmlu_pro",
            r["category"],
            r["question_id"],
            choice_prompt(r["question"], r["options"]),
            {"kind": "choice", "answer": r["answer"], "choices": len(r["options"])},
        )
    for i, r in enumerate(data["gsm"]):
        add(
            "gsm8k_train",
            "arithmetic",
            i,
            r["question"]
            + (
                "\n\nReason through the problem and finish with a separate line: "
                "#### <numeric answer>."
            ),
            {"kind": "number", "answer": r["answer"].rsplit("####", 1)[1].strip().replace(",", "")},
        )
    for family in ("murder_mystery", "object_placements", "team_allocation"):
        for i, r in enumerate(data[family]):
            options = ast.literal_eval(r["choices"])
            add(
                "musr",
                family,
                f"{family}/{i}",
                choice_prompt(r["narrative"] + "\n\n" + r["question"], options),
                {
                    "kind": "choice",
                    "answer": chr(65 + int(r["answer_index"])),
                    "choices": len(options),
                },
            )
    for r in data["ifbench"]:
        add(
            "ifbench",
            "instruction_following",
            r["key"],
            r["prompt"],
            {
                "kind": "ifbench",
                "key": r["key"],
                "instruction_id_list": r["instruction_id_list"],
                "kwargs": r["kwargs"],
            },
        )
    selected = []
    for task, family in sorted({(c["task"], c["family"]) for c, _ in candidates}):
        n = {"mmlu_pro": 2, "gsm8k_train": 24, "musr": 4, "ifbench": 12}[task]
        group = [(c, r) for c, r in candidates if (c["task"], c["family"]) == (task, family)]
        selected.extend(sorted(group, key=lambda cr: C["digest_text"]("r23/" + cr[0]["id"]))[:n])
    assert len(selected) == 76
    C["dump"](folder / "cases.json", [c for c, _ in selected])
    C["dump"](folder / "references.json", [r for _, r in selected])
    C["dump"](
        folder / "manifest.json",
        {
            "protocol": "r23-public-baseline-v1",
            "at": datetime.now(UTC).isoformat(),
            "sources": sources(),
            "upstream": origins,
            "models": MODELS,
            "datasets": {n: C["sha"](folder / n) for n in ("cases.json", "references.json")},
            "source_revision": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "source_dirty": bool(
                subprocess.check_output(
                    ["git", "status", "--porcelain"], cwd=ROOT, text=True
                ).strip()
            ),
            "seed": 2301,
            "dtype": "bfloat16",
            "attention": "sdpa",
            "max_input_tokens": 16384,
            "max_seconds": 10800,
            "ifbench_revision": IF_REV,
            "prior_spend_usd": 33.76145561903811,
            "cumulative_cap_usd": 50,
            "stage_cap_usd": 7.10,
            "use": (
                "development only; selected MuSR and IFBench IDs excluded "
                "from future untouched holdout"
            ),
        },
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("folder", type=Path)
    prepare(p.parse_args().folder)
