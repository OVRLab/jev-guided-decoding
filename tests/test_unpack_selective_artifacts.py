import gzip
import hashlib
import json
import runpy
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "research/diagnostics/unpack_selective_artifacts.py"


def fixture(tmp_path):
    report = tmp_path / "report"
    (report / "artifacts").mkdir(parents=True)
    raw = b'{"example": "public evidence"}\n'
    stored = gzip.compress(raw, mtime=0)
    (report / "artifacts/outputs.jsonl.gz").write_bytes(stored)
    entry = dict(
        remote_result="selective-attention-v1/outputs.jsonl",
        public_file="artifacts/outputs.jsonl.gz",
        raw_sha256=hashlib.sha256(raw).hexdigest(),
        stored_sha256=hashlib.sha256(stored).hexdigest(),
        raw_bytes=len(raw),
        gzip=True,
    )
    (report / "raw-artifact-hashes.json").write_text(json.dumps([entry]))
    return report, raw, entry


def test_public_artifacts_reconstruct_original_names_and_bytes(tmp_path):
    report, raw, _ = fixture(tmp_path)
    m = runpy.run_path(str(SCRIPT))
    result = m["unpack"](report, tmp_path / "out")
    assert result["verified_files"] == 1
    assert (tmp_path / "out/selective-attention-v1/outputs.jsonl").read_bytes() == raw
    with pytest.raises(FileExistsError):
        m["unpack"](report, tmp_path / "out")


@pytest.mark.parametrize("tamper", ["stored", "raw", "traversal", "duplicate"])
def test_bad_public_artifact_manifest_leaves_no_partial_output(tmp_path, tamper):
    report, _, entry = fixture(tmp_path)
    if tamper == "stored":
        (report / entry["public_file"]).write_bytes(b"tampered")
    elif tamper == "raw":
        entry["raw_sha256"] = "0" * 64
    elif tamper == "traversal":
        entry["remote_result"] = "../escape.jsonl"
    entries = [entry, entry] if tamper == "duplicate" else [entry]
    (report / "raw-artifact-hashes.json").write_text(json.dumps(entries))
    m = runpy.run_path(str(SCRIPT))
    with pytest.raises(ValueError):
        m["unpack"](report, tmp_path / "out")
    assert not (tmp_path / "out").exists()
    assert not (tmp_path / "escape.jsonl").exists()
