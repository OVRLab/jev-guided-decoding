"""Prospective freeze requires completed upstream evidence and a final protocol."""

import json
import math
import re
import runpy
import subprocess
import tarfile
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = runpy.run_path(str(HERE / "data.py"))
C = DATA["P"]["R29"]
N = runpy.run_path(str(HERE / "common.py"))
ROOT, dump, sha = C["ROOT"], C["dump"], C["sha"]


def fixed():
    return dict(
        study="R31",
        source_dirty=False,
        model=C["MODEL"],
        revision=C["REVISION"],
        informative="both",
        specs=[list(s) for s in N["specifications"]("both")],
        layer=19,
        rank=32,
        seeds=[3101, 3102],
        epochs=2,
        lr=0.001,
        accumulate=8,
        limit=128,
        max_seconds=16200,
        api_cap_usd=0.35,
        usd_per_million=0.05,
        api_delay_seconds=0.25,
        planned_cases=832,
        planned_test_cases=256,
        planned_outputs=11840,
        planned_training_steps=12288,
        planned_optimizer_updates=1536,
        data_seed=31001,
        sizes=[512, 64, 256],
        stage_reserve_usd=16,
        cumulative_cap_usd=175,
    )


def lineage():
    report = ROOT / "reports/2026-09-26-feedback-pairing"
    a = json.loads((report / "analysis.json").read_text())
    cost = json.loads((report / "cost-and-cleanup.json").read_text())
    if (
        a.get("passed") is not True
        or a.get("outputs") != 7680
        or a.get("requests") != 384
        or not all(
            cost[k]
            for k in (
                "instance_terminated",
                "owned_disk_deleted",
                "owned_security_group_deleted",
                "owned_subnet_deleted",
            )
        )
        or cost["cumulative_cap_usd"] != 175
    ):
        raise ValueError("Upstream completion, cleanup or budget not admitted")
    return dict(
        prior_conservative_usd=cost["cumulative_conservative_usd"],
        cumulative_cap_usd=175,
        files={
            str((report / name).relative_to(ROOT)): sha(report / name)
            for name in ("analysis.json", "cost-and-cleanup.json", "provenance.json")
        },
    )


def sources():
    files = C["source_hashes"]()
    paths = [
        *HERE.glob("*.py"),
        HERE.parent / "feedback_pairing/common.py",
        HERE.parent / "feedback_pairing/audit.py",
        ROOT / "research/contextual-memory-plan-v1.md",
        ROOT / "reports/2026-09-26-structured-correction/provenance.json",
    ]
    files.update({str(p.relative_to(ROOT)): sha(p) for p in sorted(paths)})
    return files


def admission_input():
    report = ROOT / "reports/2026-09-26-structured-correction"
    prov = json.loads((report / "provenance.json").read_text())
    archive = report / "artifacts/recorded-run.tar.gz"
    if sha(archive) != prov["public_archives"][archive.name]:
        raise ValueError("Changed historical admission archive")
    with tarfile.open(archive) as tar:
        content = tar.extractfile("outputs.jsonl").read()
    import hashlib

    if hashlib.sha256(content).hexdigest() != prov["original_backup_inventory"]["outputs.jsonl"]:
        raise ValueError("Unverified historical admission draft")
    case = C["make_data"]()[0][0]
    rows = [json.loads(s) for s in content.splitlines()]
    native = [r for r in rows if r["id"] == case["id"] and r["arm"] == "native"]
    if len(native) != 1 or case["split"] != "train":
        raise ValueError("Invalid historical admission case")
    return dict(case=case, native=native[0])


def budget_ok(previous):
    value = previous.get("prior_conservative_usd")
    if (
        type(value) not in (float, int)
        or not math.isfinite(value)
        or value < 0
        or previous.get("cumulative_cap_usd") != 175
        or value + fixed()["stage_reserve_usd"] > 175
    ):
        raise ValueError("Insufficient or invalid cumulative budget")


def prepare(folder):
    previous = lineage()
    budget_ok(previous)
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip():
        raise ValueError("Freeze requires committed source")
    bound_sources = sources()
    cases, refs = DATA["make_data"]()
    replay = runpy.run_path(str(HERE.parent / "structured_correction/audit.py"))["replay_reference"]
    if any(replay(c) != refs[c["id"]] for c in cases):
        raise ValueError("Independent reference replay failed")
    admission = admission_input()
    folder.mkdir(parents=True, exist_ok=False)
    for name, value in (
        ("cases.json", cases),
        ("references.json", refs),
        ("admission-input.json", admission),
    ):
        dump(folder / name, value)
    m = fixed() | dict(
        at=datetime.now(UTC).isoformat(),
        lineage=previous,
        git_revision=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        sources=bound_sources,
        files={p.name: sha(p) for p in folder.iterdir()},
    )
    dump(folder / "manifest.json", m)
    return m


def verify(folder):
    m = json.loads((folder / "manifest.json").read_text())
    if any(m.get(k) != v for k, v in fixed().items()) or not re.fullmatch(
        r"[0-9a-f]{40}", m.get("git_revision", "")
    ):
        raise ValueError("Frozen protocol contract mismatch")
    if m["sources"] != sources():
        raise ValueError("Frozen source mismatch")
    files = {
        str(p.relative_to(folder)): sha(p)
        for p in folder.rglob("*")
        if p.is_file() and p != folder / "manifest.json"
    }
    if (
        files != m["files"]
        or set(files) != {"cases.json", "references.json", "admission-input.json"}
        or any(p.is_symlink() for p in folder.rglob("*"))
    ):
        raise ValueError("Frozen input inventory mismatch")
    cases, refs = DATA["make_data"](m["sizes"], m["data_seed"])
    if (
        json.loads((folder / "cases.json").read_text()) != cases
        or json.loads((folder / "references.json").read_text()) != refs
        or json.loads((folder / "admission-input.json").read_text()) != admission_input()
    ):
        raise ValueError("Frozen data contract mismatch")
    if m["lineage"] != lineage():
        raise ValueError("Upstream evidence contract mismatch")
    budget_ok(m["lineage"])
    return m
