"""Append-only recovery ancestry with an independently checked global budget."""

import json
import math
import runpy
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path

V1 = runpy.run_path(str(Path(__file__).resolve().parent.parent / "benchmark_recovery_v1/state.py"))
sha, lines, dump, append, journal = (V1[k] for k in ("sha", "lines", "dump", "append", "journal"))
LEDGER = "recovery-chain.jsonl"
SOURCES = "recovery-chain-sources.jsonl"


def budget(admission, manifest_sha256, now):
    a = admission
    for key in ("cap_usd", "prior_closed_usd", "settled_jev_usd", "rate_usd_hour"):
        if type(a[key]) not in (int, float) or not math.isfinite(a[key]) or a[key] <= 0:
            raise ValueError("Invalid budget input")
    if (
        a["cap_usd"] != 110
        or a["prior_closed_usd"] < 47.39595151031136
        or a["settled_jev_usd"] < 0.017775408
        or a["rate_usd_hour"] < 1.8245808219178083
    ):
        raise ValueError("Authorized budget terms changed")
    if manifest_sha256 not in a["manifests"] or len(a["stream_created_at"]) != 2:
        raise ValueError("Manifest or two-stream budget binding mismatch")
    end = datetime.fromisoformat(a["worker_deadline"])
    stop = datetime.fromisoformat(a["cloud_deadline"])
    starts = [datetime.fromisoformat(s) for s in a["stream_created_at"]]
    if any(t.utcoffset() is None for t in [end, stop, now, *starts]):
        raise ValueError("Timezone-aware deadlines required")
    if end <= now or stop < end + timedelta(minutes=30) or any(t > now for t in starts):
        raise ValueError("Expired or inconsistent deadline")
    estimate = (
        a["prior_closed_usd"]
        + a["settled_jev_usd"]
        + sum((stop - t).total_seconds() / 3600 * a["rate_usd_hour"] for t in starts)
    )
    if estimate > a["cap_usd"]:
        raise ValueError("Global budget exceeded")
    return end, estimate


class State(V1["State"]):
    def __init__(self, output, rows, decisions, end, hop):
        super().__init__(output, rows, decisions, end)
        self.hop = hop

    def hardware(self, name, row):
        path = self.output / (name + "-hardware.json")
        if path.exists():
            old = json.loads(path.read_text())
            if {k: v for k, v in old.items() if k not in ("at", "load_seconds")} != {
                k: v for k, v in row.items() if k not in ("at", "load_seconds")
            }:
                raise ValueError("Reloaded hardware or weights changed")
            dump(self.output / f"recovery-chain-{self.hop}-{name}-hardware.json", row)
        else:
            dump(path, row)


def prepare(parent, output, *, manifest_sha256, admission, now=None):
    parent, output = Path(parent), Path(output)
    current = now or datetime.now(UTC)
    end, estimate = budget(admission, manifest_sha256, current)
    if output.exists():
        raise FileExistsError("Continuation already exists")
    if output.resolve().is_relative_to(parent.resolve()):
        raise ValueError("Continuation inside parent")
    if (parent / "completion.json").exists():
        raise ValueError("Parent already complete")
    if not (parent / "recovery.json").exists():
        raise ValueError("An initial v1 recovery is required")
    if json.loads((parent / "start.json").read_text())["manifest_sha256"] != manifest_sha256:
        raise ValueError("Manifest mismatch")
    rows, decisions, jobs, lost = journal(parent)
    files = list(parent.rglob("*"))
    if any(p.is_symlink() for p in files):
        raise ValueError("Symlink in parent")
    hashes = {str(p.relative_to(parent)): sha(p) for p in files if p.is_file()}
    chain = lines(parent / LEDGER)
    hop = len(chain) + 2
    shutil.copytree(parent, output)
    if any(sha(output / name) != h for name, h in hashes.items()):
        raise ValueError("Parent changed during copy")
    lost_ids = {j["batch_id"] for j in lost}
    (output / "jobs.jsonl").write_text(
        "".join(json.dumps(j) + "\n" for j in jobs if j["batch_id"] not in lost_ids)
    )
    append(
        output / LEDGER,
        dict(
            version=2,
            hop=hop,
            at=current.isoformat(),
            parent_files=hashes,
            interrupted_jobs=lost,
            deadline=end.isoformat(),
            admission=admission,
            conservative_cumulative_bound_usd=estimate,
            additional_jev_requests=0,
        ),
    )
    return State(output, rows, decisions, end, hop)


def verify_pair(parent, output):
    chain, old_chain = lines(output / LEDGER), lines(parent / LEDGER)
    if len(chain) != len(old_chain) + 1 or chain[:-1] != old_chain:
        raise ValueError("Recovery ancestry was overwritten")
    record = chain[-1]
    actual = {str(p.relative_to(parent)): sha(p) for p in parent.rglob("*") if p.is_file()}
    if actual != record["parent_files"]:
        raise ValueError("Recovery parent changed")
    _, _, jobs, lost = journal(parent)
    if lost != record["interrupted_jobs"] or record["additional_jev_requests"] != 0:
        raise ValueError("Interrupted work changed")
    end, estimate = budget(
        record["admission"],
        json.loads((parent / "start.json").read_text())["manifest_sha256"],
        datetime.fromisoformat(record["at"]),
    )
    if (
        record["deadline"] != end.isoformat()
        or record["conservative_cumulative_bound_usd"] != estimate
    ):
        raise ValueError("Recovery admission changed")
    append_only = {"outputs.jsonl", "batches.jsonl", "decisions.jsonl", LEDGER, SOURCES}
    for name, h in actual.items():
        if name == "jobs.jsonl":
            continue
        if name in append_only:
            if not (output / name).read_bytes().startswith((parent / name).read_bytes()):
                raise ValueError("Completed records not preserved")
        elif sha(output / name) != h:
            raise ValueError("Immutable ancestor record changed")
    lost_ids = {j["batch_id"] for j in lost}
    kept = [j for j in jobs if j["batch_id"] not in lost_ids]
    if lines(output / "jobs.jsonl")[: len(kept)] != kept:
        raise ValueError("Completed jobs not preserved")
    return len(lost)


def verify_chain(folders):
    folders = [Path(f) for f in folders]
    if len(folders) < 2 or len({f.resolve() for f in folders}) != len(folders):
        raise ValueError("Incomplete or cyclic ancestry")
    first = V1["verify_lineage"](folders[0], folders[1])
    interrupted = first["interrupted_jobs"]
    for parent, output in zip(folders[1:-1], folders[2:], strict=True):
        interrupted += verify_pair(parent, output)
    return dict(
        continuations=len(folders) - 1,
        interrupted_jobs=interrupted,
        exact_parent_preserved=True,
        additional_jev_requests=0,
    )
