import gzip
import hashlib
import json
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def archive(tmp_path):
    report = tmp_path / "report"
    report.mkdir()
    raw = b"a binary checkpoint\x00\xff"
    packed = gzip.compress(raw, mtime=0)
    (report / "sample.gz").write_bytes(packed)
    entry = dict(
        original_path="gated-repair-retry-v4/sample.safetensors",
        original_sha256=hashlib.sha256(raw).hexdigest(),
        original_bytes=len(raw),
        archive_sha256=hashlib.sha256(packed).hexdigest(),
        archive_bytes=len(packed),
    )
    return report, raw, entry


def test_public_extraction_verifies_binary_bytes_and_rejects_corruption(tmp_path):
    extract = runpy.run_path(str(ROOT / "research/diagnostics/replay_gated_repair.py"))["extract"]
    report, raw, entry = archive(tmp_path)
    (report / "raw-artifact-hashes.json").write_text(json.dumps({"sample.gz": entry}))
    output = tmp_path / "verified"
    assert extract(report, output) == 1
    assert (output / entry["original_path"]).read_bytes() == raw
    with pytest.raises(FileExistsError):
        extract(report, output)
    entry["original_sha256"] = "0" * 64
    (report / "raw-artifact-hashes.json").write_text(json.dumps({"sample.gz": entry}))
    with pytest.raises(ValueError, match="Original bytes"):
        extract(report, tmp_path / "corrupt")


@pytest.mark.parametrize("field", ["archive", "original", "duplicate"])
def test_public_extraction_rejects_path_escape_and_duplicate_targets(tmp_path, field):
    extract = runpy.run_path(str(ROOT / "research/diagnostics/replay_gated_repair.py"))["extract"]
    report, _, entry = archive(tmp_path)
    index = {"sample.gz": entry}
    if field == "archive":
        index = {"../sample.gz": entry}
    elif field == "original":
        entry["original_path"] = "../escape"
    else:
        index["duplicate.gz"] = entry
    (report / "raw-artifact-hashes.json").write_text(json.dumps(index))
    with pytest.raises(ValueError):
        extract(report, tmp_path / "extract")
    assert not (tmp_path / "escape").exists()
