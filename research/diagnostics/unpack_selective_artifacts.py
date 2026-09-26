"""Verify and reconstruct published R17 artifacts without inference or API access."""

import argparse
import gzip
import hashlib
import io
import json
import tempfile
from pathlib import Path, PurePosixPath


def relative(name):
    if (
        not isinstance(name, str)
        or not name
        or "\\" in name
        or PurePosixPath(name).is_absolute()
        or any(part in ("", ".", "..") for part in name.split("/"))
    ):
        raise ValueError("Unsafe artifact path")
    return Path(name)


def unpack(report, output):
    report = report.resolve()
    if output.exists() or output.is_symlink():
        raise FileExistsError("Use a new output directory")
    entries = json.loads((report / "raw-artifact-hashes.json").read_text())
    if not isinstance(entries, list) or not entries:
        raise ValueError("Empty/invalid artifact manifest")
    targets, sources = set(), set()
    validated = []
    for row in entries:
        source, target = relative(row["public_file"]), relative(row["remote_result"])
        if target in targets or source in sources:
            raise ValueError("Duplicate artifact path")
        targets.add(target)
        sources.add(source)
        path = (report / source).resolve()
        if not path.is_relative_to(report) or not path.is_file():
            raise ValueError("Artifact outside report or missing")
        size = row["raw_bytes"]
        if type(size) is not int or not 0 <= size <= 1_000_000_000 or type(row["gzip"]) is not bool:
            raise ValueError("Invalid artifact size/encoding")
        stored = path.read_bytes()
        if hashlib.sha256(stored).hexdigest() != row["stored_sha256"]:
            raise ValueError("Stored artifact hash mismatch")
        try:
            data = (
                gzip.GzipFile(fileobj=io.BytesIO(stored)).read(size + 1) if row["gzip"] else stored
            )
        except (OSError, EOFError) as exc:
            raise ValueError("Invalid compressed artifact") from exc
        if len(data) != size or hashlib.sha256(data).hexdigest() != row["raw_sha256"]:
            raise ValueError("Raw artifact hash/size mismatch")
        validated.append((target, data))
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="r17-verified-", dir=output.parent) as temporary:
        staging = Path(temporary) / "results"
        staging.mkdir()
        for target, data in validated:
            path = staging / target
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        if output.exists() or output.is_symlink():
            raise FileExistsError("Output appeared during verification")
        staging.rename(output)
    return dict(verified_files=len(validated), raw_bytes=sum(len(v) for _, v in validated))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--report", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    print(json.dumps(unpack(args.report, args.output)))


if __name__ == "__main__":
    main()
