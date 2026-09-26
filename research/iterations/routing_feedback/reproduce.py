"""Acquire pinned R28 inputs or replay public numerical grades without paid calls."""

import argparse
import gzip
import json
import re
import runpy
import shutil
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
C = runpy.run_path(str(HERE / "common.py"))
ROOT = C["ROOT"]


def build_inputs(rows, *, excluded):
    keys = [r["key"] for r in rows]
    if len(set(keys)) != len(keys) or any(type(i) is not int or i < 0 for i in keys):
        raise ValueError("Invalid or duplicate source IDs")
    cases, refs = [], []
    for row in rows:
        if row["key"] in excluded:
            continue
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
    return cases, refs


def public_grade(row):
    if (
        set(row) != {"id", "arm", "strict", "loose", "instruction_strict", "instruction_loose"}
        or not isinstance(row["id"], str)
        or not re.fullmatch(r"ifeval/\d+", row["id"])
        or row["arm"] not in {"native", "constant", "live", "shuffled"}
        or any(type(row[k]) is not bool for k in ["strict", "loose"])
        or any(
            not isinstance(row[k], list) or not row[k] or any(type(x) is not bool for x in row[k])
            for k in ["instruction_strict", "instruction_loose"]
        )
    ):
        raise ValueError("Invalid or text-bearing public grade")
    return dict(row)


def acquire(destination, protocol):
    m = json.loads((protocol / "manifest.json").read_text())
    commit = m["upstream_commit"]
    if not re.fullmatch("[a-f0-9]{40}", commit):
        raise ValueError("Unpinned source")
    for name, sha in m["sources"].items():
        if Path(name).is_absolute() or ".." in Path(name).parts or C["sha"](ROOT / name) != sha:
            raise ValueError("Frozen source mismatch")
    destination.mkdir(parents=True, exist_ok=False)
    grading = destination.parent / (destination.name + "-grading")
    grading.mkdir(mode=0o700, exist_ok=False)
    upstream = grading / "instruction_following_eval"
    for name, want in m["evaluator"].items():
        if Path(name).is_absolute() or ".." in Path(name).parts:
            raise ValueError("Invalid upstream path")
        url = f"https://raw.githubusercontent.com/google-research/google-research/{commit}/instruction_following_eval/{name}"
        data = urllib.request.urlopen(url, timeout=60).read()
        path = upstream / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        if C["sha"](path) != want:
            raise ValueError("Upstream file hash mismatch: " + name)
    rows = [json.loads(s) for s in (upstream / "data/input_data.jsonl").read_text().splitlines()]
    cases, refs = build_inputs(rows, excluded={1122, 1129, *m["overlap"]["exact_keys"]})
    if len(cases) != m["eligible_cases"]:
        raise ValueError("Eligible cohort mismatch")
    C["dump"](destination / "cases.json", cases)
    C["dump"](grading / "references.json", refs)
    if (
        C["sha"](destination / "cases.json") != m["datasets"]["cases.json"]
        or C["sha"](grading / "references.json") != m["references_sha256"]
    ):
        raise ValueError("Reconstructed dataset binding mismatch")
    checkpoint = m["checkpoints"]["live"]
    name = checkpoint["file"]
    if Path(name).name != name:
        raise ValueError("Invalid checkpoint path")
    archive = (
        ROOT / "reports/2026-09-23-gated-repair/artifacts/gated-repair-retry-v4" / (name + ".gz")
    )
    (destination / name).write_bytes(gzip.decompress(archive.read_bytes()))
    if C["sha"](destination / name) != checkpoint["sha256"]:
        raise ValueError("Checkpoint archive mismatch")
    shutil.copyfile(protocol / "manifest.json", destination / "manifest.json")
    return dict(
        cases=len(cases),
        paid_calls=0,
        model_inference=False,
        manifest_sha256=C["sha"](destination / "manifest.json"),
    )


def export(private, selection, analysis, destination):
    result = json.loads(analysis.read_text())
    if C["sha"](selection) != result["integrity"]["artifact_hashes"]["selection.json"]:
        raise ValueError("Selection changed after admitted analysis")
    rows = [public_grade(r) for r in json.loads(private.read_text())]
    plan = json.loads(selection.read_text())["plan"]
    C["select_outputs"](plan, rows)
    destination.mkdir(parents=True, exist_ok=False)
    C["dump"](destination / "grades.json", rows)
    C["dump"](destination / "selection.json", plan)
    shutil.copyfile(analysis, destination / "analysis.json")
    C["dump"](
        destination / "hashes.json",
        dict(
            files={p.name: C["sha"](p) for p in destination.iterdir() if p.is_file()},
            private_grade_source_sha256=C["sha"](private),
            scope=(
                "Numerical outcome/policy replay only; no questions, answer text, "
                "tokens or API payloads"
            ),
        ),
    )
    return replay(destination)


def replay(folder):
    hashes = json.loads((folder / "hashes.json").read_text())
    for name, sha in hashes["files"].items():
        if Path(name).name != name or C["sha"](folder / name) != sha:
            raise ValueError("Public replay hash mismatch")
    rows = [public_grade(r) for r in json.loads((folder / "grades.json").read_text())]
    plan = json.loads((folder / "selection.json").read_text())
    result = json.loads((folder / "analysis.json").read_text())
    policies = C["select_outputs"](plan, rows)
    blocks = {i: b["index"] for b in plan["blocks"] for i in b["ids"]}
    ids = sorted(blocks)
    vectors = {
        p: [{r["id"]: r["strict"] for r in rs}[i] for i in ids] for p, rs in policies.items()
    }
    for name, rs in policies.items():
        for key in ["strict", "loose"]:
            if sum(r[key] for r in rs) != result["scores"][name][key]:
                raise ValueError("Public score mismatch")
    for label, expected in result["contrasts"].items():
        a, b = label.split("__")
        actual = C["paired"](vectors[a], vectors[b], [blocks[i] for i in ids])
        if any(actual[k] != expected[k] for k in actual):
            raise ValueError("Paired contrast replay mismatch")
    return dict(
        passed=True,
        cases=len(ids),
        potential_outcomes=len(rows),
        policies=len(policies),
        contrasts=len(result["contrasts"]),
        paid_calls=0,
        model_inference=False,
        raw_token_audit=False,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    modes = p.add_subparsers(dest="mode", required=True)
    a = modes.add_parser("acquire")
    a.add_argument("--destination", type=Path, required=True)
    a.add_argument("--protocol", type=Path, default=ROOT / "research/protocols/routing-feedback-v1")
    e = modes.add_parser("export")
    for flag in ("private", "selection", "analysis", "destination"):
        e.add_argument("--" + flag, type=Path, required=True)
    r = modes.add_parser("replay")
    r.add_argument("--folder", type=Path, required=True)
    args = vars(p.parse_args())
    mode = args.pop("mode")
    print(json.dumps(globals()[mode](**args)))
