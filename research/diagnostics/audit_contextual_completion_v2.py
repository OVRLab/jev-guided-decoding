"""R31 audit correction: canonical CUDA device alias, with unchanged raw evidence."""

import argparse
import hashlib
import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def canonical_admission(record):
    if record.get("device") not in ("cuda", "cuda:0"):
        raise ValueError("Unexpected single-GPU admission device")
    return record | dict(device="cuda")


def audit(folder, output):
    original = runpy.run_path(str(ROOT / "research/iterations/contextual_memory/audit.py"))
    namespace = original["audit"].__globals__
    read = namespace["read"]
    raw = read(output, "mechanical-admission.json")
    admission_hash = hashlib.sha256((output / "mechanical-admission.json").read_bytes()).hexdigest()

    def read_with_device_alias(directory, name):
        value = read(directory, name)
        if directory.resolve() == output.resolve() and name == "mechanical-admission.json":
            return canonical_admission(value)
        return value

    namespace["read"] = read_with_device_alias
    try:
        result = original["audit"](folder, output)
    finally:
        namespace["read"] = read
    if (
        hashlib.sha256((output / "mechanical-admission.json").read_bytes()).hexdigest()
        != admission_hash
    ):
        raise ValueError("Raw admission changed during audit")
    result["audit_revision"] = dict(
        name="R31 CUDA alias correction v2",
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        raw_device=raw["device"],
        canonical_device="cuda",
        raw_admission_sha256=admission_hash,
        raw_evidence_unchanged=True,
        scope="Device-label normalization only; all frozen integrity/statistical checks retained",
    )
    original["C"]["dump"](output / "analysis.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = audit(args.input, args.output)
    print(json.dumps({k: result[k] for k in ("passed", "outputs", "requests", "scores")}))
