"""Conditional R32a freeze: completed lineage, exact checkpoints, exposed inputs."""

import hashlib
import json
import math
import re
import runpy
import shutil
import subprocess
import tarfile
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
C = runpy.run_path(str(HERE.parent / "contextual_memory/contract.py"))
DATA = runpy.run_path(str(HERE / "data.py"))
S = runpy.run_path(str(HERE / "single.py"))
COMP = runpy.run_path(str(HERE / "comparator.py"))
sha, dump = C["sha"], C["dump"]
REPORT = ROOT / "reports/2026-09-26-contextual-memory"
NATIVE = ROOT / "research/diagnostics/musr-single-interface-20260926/native-readability-v1.tar.gz"


def fixed():
    return dict(
        study="R32a",
        source_dirty=False,
        model=C["fixed"]()["model"],
        backbone_digest="efa5edd16939c3996fe63734e8cc88146091d066ceed023837d7833f6225e27c",
        revision=C["fixed"]()["revision"],
        layer=19,
        rank=32,
        specs=[
            [name, seed]
            for name in ("contextual-scalar", "embedding-scalar")
            for seed in (3101, 3102)
        ],
        readout_version=S["READOUT_VERSION"],
        native_limit=1024,
        repair_limit=1024,
        context_limit=4096,
        max_seconds=5400,
        api_cap_usd=0.05,
        usd_per_million=0.05,
        api_delay_seconds=0.25,
        planned_cases=12,
        planned_outputs=192,
        planned_requests=12,
        larger_model=COMP["MODEL"],
        larger_revision=COMP["REVISION"],
        larger_dtype="torch.bfloat16",
        larger_profiles=["nonthinking", "thinking"],
        stage_reserve_usd=5.25,
        cumulative_cap_usd=175,
    )


def budget_ok(previous):
    value = previous.get("prior_conservative_usd")
    if (
        type(value) not in (int, float)
        or not math.isfinite(value)
        or value < 0
        or previous.get("cumulative_cap_usd") != 175
        or value + fixed()["stage_reserve_usd"] > 175
    ):
        raise ValueError("Insufficient or invalid cumulative budget")


def upstream(report=REPORT):
    analysis, cost, provenance = (
        json.loads((report / n).read_text())
        for n in ("analysis.json", "cost-and-cleanup.json", "provenance.json")
    )
    if (
        any(
            analysis.get(k) != v
            for k, v in dict(
                passed=True,
                outputs=11840,
                requests=832,
                training_steps=12288,
                optimizer_updates=1536,
                test_cases=256,
            ).items()
        )
        or not all(
            cost.get(k) is True
            for k in (
                "instance_terminated",
                "owned_disk_deleted",
                "owned_security_group_deleted",
                "owned_subnet_deleted",
            )
        )
        or cost.get("cumulative_cap_usd") != 175
    ):
        raise ValueError("R31 completion or cleanup is not admitted")
    previous = dict(
        prior_conservative_usd=cost["cumulative_conservative_usd"], cumulative_cap_usd=175
    )
    budget_ok(previous)
    archives = {}
    for name in ("recorded-run.tar.gz", "adapters.tar.gz"):
        path = report / "artifacts" / name
        if path.is_symlink() or sha(path) != provenance["public_archives"][name]:
            raise ValueError("Changed R31 archive")
        archives[name] = path

    def member(archive, name):
        with tarfile.open(archives[archive]) as stream:
            matches = [m for m in stream if m.name == name]
            if len(matches) != 1 or not matches[0].isfile():
                raise ValueError("Missing or ambiguous R31 archive member")
            body = stream.extractfile(matches[0]).read()
        if hashlib.sha256(body).hexdigest() != provenance["original_backup_inventory"][name]:
            raise ValueError("R31 member changed from verified backup")
        return body

    choices = json.loads(member("recorded-run.tar.gz", "selection.json"))["models"]
    selection, binaries = {}, {}
    for name, seed in fixed()["specs"]:
        key = f"{name}/{seed}"
        row = choices[key]
        scores = row["scores"]
        if (
            not isinstance(scores, list)
            or len(scores) != 2
            or any(
                type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 1
                for v in scores
            )
        ):
            raise ValueError("Invalid development selection scores")
        epoch = max(range(2), key=lambda i: scores[i]) + 1
        file = f"{name}-{seed}-epoch{epoch}.safetensors"
        if (
            row["epoch"] != epoch
            or row["file"] != file
            or row["memory"] != name.split("-")[0]
            or row["feedback"] != "scalar"
        ):
            raise ValueError("Checkpoint is not the development-selected scalar condition")
        binary = member("adapters.tar.gz", file)
        if hashlib.sha256(binary).hexdigest() != row["sha256"]:
            raise ValueError("Checkpoint selection digest mismatch")
        selection[key], binaries[file] = row, binary
    previous["files"] = {
        name: sha(report / name)
        for name in (
            "analysis.json",
            "cost-and-cleanup.json",
            "provenance.json",
            "artifacts/recorded-run.tar.gz",
            "artifacts/adapters.tar.gz",
        )
    }
    return dict(lineage=previous, selection=selection, checkpoint_bytes=binaries)


def sources():
    files = C["sources"]()
    paths = [
        *HERE.glob("*.py"),
        ROOT / "research/musr-live-admission-v1.md",
        ROOT / "research/musr-readout-v2.md",
        DATA["ADMISSION"],
        ROOT / "research/diagnostics/musr_groups.py",
        NATIVE,
        NATIVE.with_name("native-readability-provenance.json"),
        NATIVE.with_name("larger-tokenizer-admission.json"),
    ]
    files.update({str(p.relative_to(ROOT)): sha(p) for p in sorted(paths)})
    return files


def inventory(folder):
    paths = list(folder.rglob("*"))
    if any(p.is_symlink() for p in paths):
        raise ValueError("Input inventory contains a symlink")
    return {
        str(p.relative_to(folder)): sha(p)
        for p in paths
        if p.is_file() and p != folder / "manifest.json"
    }


def expected_data(folder):
    data = DATA["load"](folder)
    cases = sorted((c for c in data["cases"] if c["split"] == "development"), key=lambda c: c["id"])
    if len(cases) != 12:
        raise ValueError("Admission must use exactly twelve exposed questions")
    ids = {c["id"] for c in cases}
    with tarfile.open(NATIVE) as stream:
        old_cases = json.load(stream.extractfile("cases.json"))
        old_rows = [json.loads(s) for s in stream.extractfile("outputs.jsonl").read().splitlines()]
    if cases != old_cases:
        raise ValueError("Exposed-case admission lineage changed")
    native = [r for r in old_rows if r["id"] == cases[0]["id"]]
    if len(native) != 1:
        raise ValueError("Invalid first exposed native draft")
    return dict(
        cases=cases,
        references={i: data["references"][i] for i in sorted(ids)},
        groups={i: data["case_groups"][i] for i in sorted(ids)},
        admission=dict(case=cases[0], native=native[0]),
        sources=data["sources"],
    )


def prepare(folder, dataset):
    prior = upstream()
    data = expected_data(dataset)
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip():
        raise ValueError("Freeze requires committed source")
    folder.mkdir(parents=True, exist_ok=False)
    (folder / "source").mkdir()
    (folder / "adapters").mkdir()
    for name in data["sources"]:
        shutil.copyfile(dataset / name, folder / "source" / name)
    for name, binary in prior["checkpoint_bytes"].items():
        (folder / "adapters" / name).write_bytes(binary)
    for name, value in (
        ("cases", data["cases"]),
        ("references", data["references"]),
        ("groups", data["groups"]),
        ("admission-input", data["admission"]),
        ("selection", prior["selection"]),
    ):
        dump(folder / f"{name}.json", value)
    manifest = fixed() | dict(
        at=datetime.now(UTC).isoformat(),
        lineage=prior["lineage"],
        git_revision=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        sources=sources(),
        files=inventory(folder),
    )
    dump(folder / "manifest.json", manifest)
    verify(folder)
    return manifest


def verify(folder):
    manifest = json.loads((folder / "manifest.json").read_text())
    if any(manifest.get(k) != v for k, v in fixed().items()) or not re.fullmatch(
        r"[a-f0-9]{40}", manifest.get("git_revision", "")
    ):
        raise ValueError("Changed R32a protocol contract")
    if manifest["sources"] != sources() or manifest["files"] != inventory(folder):
        raise ValueError("Changed R32a frozen source/input inventory")
    prior, data = upstream(), expected_data(folder / "source")
    if manifest["lineage"] != prior["lineage"]:
        raise ValueError("Changed R31 evidence lineage")
    expected = {"source/" + n for n in data["sources"]} | {
        "adapters/" + n for n in prior["checkpoint_bytes"]
    }
    for name, value in (
        ("cases", data["cases"]),
        ("references", data["references"]),
        ("groups", data["groups"]),
        ("admission-input", data["admission"]),
        ("selection", prior["selection"]),
    ):
        expected.add(name + ".json")
        if json.loads((folder / f"{name}.json").read_text()) != value:
            raise ValueError("Changed exposed input or checkpoint selection")
    if set(manifest["files"]) != expected or any(
        (folder / "adapters" / name).read_bytes() != body
        for name, body in prior["checkpoint_bytes"].items()
    ):
        raise ValueError("Unexpected files or changed checkpoint weights")
    budget_ok(manifest["lineage"])
    return manifest
