"""Strict derived recovery of R27 journals; never mutate an interrupted parent."""

import hashlib
import json
import math
import os
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def lines(path):
    if not path.exists():
        return []
    data = path.read_text()
    if data and not data.endswith("\n"):
        raise ValueError("Partial journal line; recovery refused")
    return [json.loads(line) for line in data.splitlines()]


def unique(rows, fields):
    result = {tuple(r[f] for f in fields): r for r in rows}
    if len(result) != len(rows):
        raise ValueError("Duplicate durable records")
    return result


def dump(path, row):
    with path.open("x") as stream:
        stream.write(json.dumps(row, indent=2, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def append(path, row):
    with path.open("a") as stream:
        stream.write(json.dumps(row, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def journal(parent):
    rows = lines(parent / "outputs.jsonl")
    by_key = unique(rows, ("model", "arm", "id"))
    by_batch = unique(rows, ("batch_id",))
    batches = unique(lines(parent / "batches.jsonl"), ("batch_id",))
    jobs = lines(parent / "jobs.jsonl")
    if any(j["event"] not in ("start", "finish") for j in jobs):
        raise ValueError("Unknown job event")
    starts = unique([j for j in jobs if j["event"] == "start"], ("batch_id",))
    ends = unique([j for j in jobs if j["event"] == "finish"], ("batch_id",))
    if not (set(by_batch) == set(batches) == set(ends) <= set(starts)):
        raise ValueError("Ambiguous partial completion; recovery refused")
    interrupted = set(starts) - set(ends)
    if len(interrupted) > 1 or (
        interrupted and (jobs[-1]["event"] != "start" or (jobs[-1]["batch_id"],) not in interrupted)
    ):
        raise ValueError("Nonserial interrupted jobs")
    for key, row in by_batch.items():
        a, z, b = starts[key], ends[key], batches[key]
        if (
            any(a[f] != z[f] or a[f] != b[f] or a[f] != row[f] for f in ("model", "arm"))
            or a["ids"] != z["ids"]
            or a["ids"] != [row["id"]]
            or a["at"] > z["at"]
        ):
            raise ValueError("Completed job binding mismatch")
    decisions = unique(lines(parent / "decisions.jsonl"), ("arm", "id"))
    return by_key, decisions, jobs, [starts[k] for k in interrupted]


class State:
    def __init__(self, output, rows, decisions, end):
        self.output, self.rows, self.decisions, self.end = output, rows, decisions, end

    def cached(self, model, arm, ident, prefix, gate):
        row = self.rows.get((model, arm, ident))
        if row is not None and (row["prompt_token_ids"] != prefix or row["gate"] != gate):
            raise ValueError("Reused prefix or gate changed")
        return row

    def decision(self, row):
        key = (row["arm"], row["id"])
        old = self.decisions.get(key)
        if old is not None:
            if {k: v for k, v in old.items() if k != "at"} != {
                k: v for k, v in row.items() if k != "at"
            }:
                raise ValueError("Reused decision changed")
            return
        append(self.output / "decisions.jsonl", row)
        self.decisions[key] = row

    def hardware(self, name, row):
        path = self.output / (name + "-hardware.json")
        if path.exists():
            old = json.loads(path.read_text())
            if {k: v for k, v in old.items() if k not in ("at", "load_seconds")} != {
                k: v for k, v in row.items() if k not in ("at", "load_seconds")
            }:
                raise ValueError("Reloaded hardware or weights changed")
            dump(self.output / ("recovery-" + name + "-hardware.json"), row)
        else:
            dump(path, row)


def prepare(parent, output, *, manifest_sha256, max_seconds, now=None):
    parent, output = Path(parent), Path(output)
    if output.exists():
        raise FileExistsError("Continuation output already exists")
    if output.resolve().is_relative_to(parent.resolve()):
        raise ValueError("Continuation cannot be inside parent")
    if (parent / "completion.json").exists() or (parent / "recovery.json").exists():
        raise ValueError("Already complete or previously recovered parent")
    if type(max_seconds) not in (int, float) or not math.isfinite(max_seconds) or max_seconds <= 0:
        raise ValueError("Invalid deadline")
    start = json.loads((parent / "start.json").read_text())
    current = now or datetime.now(UTC)
    end = datetime.fromisoformat(start["at"]) + timedelta(seconds=max_seconds)
    if (
        start["manifest_sha256"] != manifest_sha256
        or current >= end
        or current < datetime.fromisoformat(start["at"])
    ):
        raise ValueError("Changed manifest or expired deadline")
    rows, decisions, jobs, interrupted = journal(parent)
    files = list(parent.rglob("*"))
    if any(p.is_symlink() for p in files):
        raise ValueError("Symlink in parent")
    hashes = {str(p.relative_to(parent)): sha(p) for p in files if p.is_file()}
    shutil.copytree(parent, output)
    if any(sha(output / p) != value for p, value in hashes.items()):
        raise ValueError("Parent changed during recovery copy")
    lost = {j["batch_id"] for j in interrupted}
    (output / "jobs.jsonl").write_text(
        "".join(json.dumps(j) + "\n" for j in jobs if j["batch_id"] not in lost)
    )
    dump(
        output / "recovery.json",
        dict(
            version=1,
            at=current.isoformat(),
            parent_files=hashes,
            interrupted_jobs=interrupted,
            deadline=end.isoformat(),
            additional_jev_requests=0,
            timing="Interrupted run; reload, downtime and lost partial work separate",
        ),
    )
    return State(output, rows, decisions, end)


def verify_lineage(parent, output):
    """Verify derived inputs before applying the unchanged complete-run auditor."""
    record = json.loads((output / "recovery.json").read_text())
    actual = {str(p.relative_to(parent)): sha(p) for p in parent.rglob("*") if p.is_file()}
    if actual != record["parent_files"]:
        raise ValueError("Interrupted parent changed")
    _, _, jobs, interrupted = journal(parent)
    if interrupted != record["interrupted_jobs"] or record["additional_jev_requests"] != 0:
        raise ValueError("Interrupted job provenance changed")
    append_only = {"outputs.jsonl", "batches.jsonl", "decisions.jsonl"}
    for name, digest in actual.items():
        if name == "jobs.jsonl":
            continue
        if name in append_only:
            if not (output / name).read_bytes().startswith((parent / name).read_bytes()):
                raise ValueError("Completed records not preserved")
        elif sha(output / name) != digest:
            raise ValueError("Immutable parent file not preserved")
    lost = {j["batch_id"] for j in interrupted}
    kept = [j for j in jobs if j["batch_id"] not in lost]
    if lines(output / "jobs.jsonl")[: len(kept)] != kept:
        raise ValueError("Completed jobs not preserved")
    return dict(
        interrupted_jobs=len(interrupted),
        parent_files=len(actual),
        exact_parent_preserved=True,
        additional_jev_requests=0,
    )
