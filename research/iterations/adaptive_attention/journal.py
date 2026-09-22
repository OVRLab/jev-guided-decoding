"""Exclusive, append-only experiment journal. Started jobs are never silently replayed."""

import json
import os
from datetime import UTC, datetime
from pathlib import Path


def append(path, row):
    with Path(path).open("a") as stream:
        stream.write(json.dumps(row, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def rows(path):
    return (
        [json.loads(line) for line in Path(path).read_text().splitlines()]
        if Path(path).exists()
        else []
    )


def now():
    return datetime.now(UTC).isoformat()


class Journal:
    def __init__(self, folder, freeze):
        self.folder, self.freeze = Path(folder), freeze
        self.starts, self.outputs = {}, {}

    def __enter__(self):
        self.folder.mkdir(parents=True, exist_ok=True)
        self.lock = self.folder / "run.lock"
        with self.lock.open("x") as stream:
            stream.write(str(os.getpid()))
        try:
            path = self.folder / "freeze.json"
            if path.exists():
                if json.loads(path.read_text()) != json.loads(json.dumps(self.freeze)):
                    raise ValueError("Study freeze mismatch")
            else:
                with path.open("x") as stream:
                    json.dump(self.freeze, stream, indent=2)
            for row in rows(self.folder / "starts.jsonl"):
                if row["job"] in self.starts:
                    raise ValueError("Duplicate job start")
                self.starts[row["job"]] = row
            for row in rows(self.folder / "outputs.jsonl"):
                if row["job"] in self.outputs or row["job"] not in self.starts:
                    raise ValueError("Invalid completed job")
                self.outputs[row["job"]] = row
            for job, row in self.starts.items():
                if job not in self.outputs:
                    self.finish(
                        job,
                        {
                            "status": "interrupted",
                            "seconds": 0,
                            "reason": "started without completion; not replayed",
                            "work_unknown": True,
                            **row["metadata"],
                        },
                    )
            return self
        except BaseException:
            self.lock.unlink()
            raise

    def __exit__(self, *args):
        self.lock.unlink()

    def start(self, job, metadata):
        if job in self.starts:
            if self.starts[job]["metadata"] != metadata:
                raise ValueError("Job identity mismatch")
            return False
        row = {"job": job, "metadata": metadata, "at": now()}
        append(self.folder / "starts.jsonl", row)
        self.starts[job] = row
        return True

    def finish(self, job, result):
        if job not in self.starts or job in self.outputs:
            raise ValueError("Job must start exactly once before completion")
        row = {**result, "job": job, "at": now()}
        append(self.folder / "outputs.jsonl", row)
        self.outputs[job] = row
