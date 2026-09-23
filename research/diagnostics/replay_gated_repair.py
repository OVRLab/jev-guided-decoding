"""Reproduce the R25 v4 audits from the distributed, byte-verified raw archive.

No training, generation, provider calls, checkpoint selection or metric changes.
Requires the inference extras for tokenizer and checkpoint verification.
"""

import argparse
import gzip
import hashlib
import json
import runpy
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def contained(root, name):
    relative = PurePosixPath(name)
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise ValueError("Unsafe archive path")
    path = (root / str(relative)).resolve()
    if not path.is_relative_to(root.resolve()) or path == root.resolve():
        raise ValueError("Archive path escapes root")
    return path


def extract(report, destination):
    entries = json.loads((report / "raw-artifact-hashes.json").read_text())
    if not entries:
        raise ValueError("Empty archive index")
    targets = set()
    for name, entry in entries.items():
        contained(report, name)
        target = contained(destination, entry["original_path"])
        if target in targets:
            raise ValueError("Duplicate extraction target")
        targets.add(target)
    destination.mkdir(exist_ok=False)
    for name, entry in entries.items():
        packed = contained(report, name).read_bytes()
        if (
            len(packed) != entry["archive_bytes"]
            or hashlib.sha256(packed).hexdigest() != entry["archive_sha256"]
        ):
            raise ValueError("Archive bytes do not match index")
        raw = gzip.decompress(packed)
        if (
            len(raw) != entry["original_bytes"]
            or hashlib.sha256(raw).hexdigest() != entry["original_sha256"]
        ):
            raise ValueError("Original bytes do not match index")
        target = contained(destination, entry["original_path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(raw)
    return len(entries)


def run(report, destination):
    count = extract(report, destination)
    from transformers import AutoTokenizer

    folder = ROOT / "research/protocols/gated-repair-retry-v4"
    source = ROOT / "research/iterations/gated_repair_retry"
    manifest = json.loads((folder / "manifest.json").read_text())
    tokenizer = AutoTokenizer.from_pretrained(
        manifest["model"], revision=manifest["revision"], trust_remote_code=False
    )
    output = destination / "gated-repair-retry-v4"
    primary_path = report / "analysis.json"
    checks = {}

    def compare(name, value):
        if value != json.loads((report / name).read_text()):
            raise ValueError("Public audit differs: " + name)
        checks[name] = dict(matched=True, sha256=sha(report / name))
        print(name + ": exact JSON-object match", flush=True)

    analyzer = runpy.run_path(str(source / "analyze.py"))
    compare("analysis.json", analyzer["analyze"](folder, output, tokenizer))
    records = runpy.run_path(str(source / "records.py"))
    compare("training-audit.json", records["run"](folder, output))
    # Use the already matched public serialization for supplement hash binding.
    retention = runpy.run_path(str(source / "retention.py"))
    compare(
        "retention.json",
        retention["run"](
            folder,
            output,
            primary_path,
            ROOT / "research/protocols/gated-repair-retention-retry-v4.json",
        ),
    )
    details = runpy.run_path(str(source / "details.py"))
    compare("details.json", details["run"](folder, output, primary_path))
    return dict(
        passed=True,
        raw_files=count,
        checkpoints=len(list(output.glob("*.safetensors"))),
        archive_index_sha256=sha(report / "raw-artifact-hashes.json"),
        replay_source_sha256=sha(Path(__file__)),
        inference_repeated=False,
        checks=checks,
        note=(
            "Hashes and exact audit replay establish reproducibility, not independent replication."
        ),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--extract", type=Path, required=True)
    parser.add_argument("--save", type=Path, required=True)
    args = parser.parse_args()
    if args.save.exists():
        raise FileExistsError(args.save)
    result = run(args.report, args.extract)
    with args.save.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
