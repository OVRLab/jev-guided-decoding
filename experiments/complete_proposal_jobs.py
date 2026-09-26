"""Run only never-started jobs after an interrupted fixed proposal evaluation."""

from __future__ import annotations

import argparse
import hashlib
import json
import signal
import subprocess
import sys
import time
import tomllib
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data/proposal-evaluation.jsonl"
MAX_SECONDS = 900


def remaining_jobs(metadata: dict, rows: list[dict], cases: list[dict]) -> list[tuple]:
    cases_by_id = {c["id"]: c for c in cases}
    planned = []
    modes = metadata["modes"]
    for case_index, case_id in enumerate(metadata["case_ids"]):
        for seed_index, seed in enumerate(metadata["seeds"]):
            offset = (case_index + seed_index) % len(modes)
            planned.extend((case_id, seed, mode) for mode in modes[offset:] + modes[:offset])
    observed = set()
    for row in rows:
        key = row["id"], row["seed"], row["result"]["mode"]
        if key not in planned or key in observed:
            raise ValueError("Unexpected or duplicate prior row")
        if any(
            row["request"].get(field) != cases_by_id[row["id"]][field]
            for field in ("question", "evidence")
        ):
            raise ValueError("Recorded problem differs from the fixed dataset")
        observed.add(key)  # Includes every failure/cancellation: none is replayed.
    return [key for key in planned if key not in observed]


def save(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--previous", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    metadata = json.loads((args.previous / "metadata.json").read_text())
    previous_bytes = (args.previous / "runs.jsonl").read_bytes()
    rows = [json.loads(line) for line in previous_bytes.decode().splitlines()]
    config = tomllib.loads(args.config.read_text())
    if config != metadata["config"]:
        raise ValueError("Continuation config differs from the frozen evaluation")
    if hashlib.sha256(DATASET.read_bytes()).hexdigest() != metadata["dataset_sha256"]:
        raise ValueError("Evaluation dataset changed")
    cases = [json.loads(line) for line in DATASET.read_text().splitlines()]
    jobs = remaining_jobs(metadata, rows, cases)
    cases_by_id = {c["id"]: c for c in cases}
    args.output.mkdir(parents=True, exist_ok=False)
    manifest = {
        "created_at": datetime.now(UTC).isoformat(),
        "previous": str(args.previous),
        "previous_results_sha256": hashlib.sha256(previous_bytes).hexdigest(),
        "config": config,
        "max_stage_seconds": MAX_SECONDS,
        "source_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "source_dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT)),
        "policy": "Only never-started jobs. Keep all failures. "
        "Stop on an early service/backend error. A scorer error coinciding with the "
        "request deadline is retained and does not block unrelated jobs.",
        "timing_caveat": "Each job reloads and warms the model in a separate process. "
        "Per-job metadata records loading; per-run elapsed excludes loading/warm-up.",
        "jobs": [
            {"id": cid, "seed": seed, "mode": mode, "status": "not_started"}
            for cid, seed, mode in jobs
        ],
    }
    manifest_path = args.output / "manifest.json"
    save(manifest_path, manifest)
    deadline = time.monotonic() + MAX_SECONDS
    status = 0
    for index, job in enumerate(manifest["jobs"]):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            status = 130
            break
        dataset = args.output / f"case-{index:02}.jsonl"
        dataset.write_text(json.dumps(cases_by_id[job["id"]]) + "\n")
        output = args.output / f"job-{index:02}"
        job.update(status="started", output=output.name)
        save(manifest_path, manifest)
        command = [
            sys.executable,
            "-c",
            "from jev_guided_decoding.cli import main; main()",
            "reason-benchmark",
            "--config",
            str(args.config),
            "--dataset",
            str(dataset),
            "--modes",
            job["mode"],
            "--seeds",
            str(job["seed"]),
            "--local-files-only",
            "--output",
            str(output),
        ]
        print(
            f"Never-started job {index + 1}/{len(jobs)}: {job['id']} {job['seed']} {job['mode']}",
            flush=True,
        )
        process = subprocess.Popen(command, cwd=ROOT)
        timed_out = False
        try:
            code = process.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            timed_out = True
            process.send_signal(signal.SIGINT)
            try:
                code = process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                code = process.wait()
        job.update(status="attempted", exit_code=code)
        trace_path = output / "runs.jsonl"
        result = None
        if trace_path.exists():
            records = [json.loads(line) for line in trace_path.read_text().splitlines()]
            if len(records) == 1:
                result = records[0]["result"]
                job.update(stop_reason=result["stop_reason"], usage_unknown=result["usage_unknown"])
        save(manifest_path, manifest)
        if timed_out or code == 130:
            status = 130
            break
        at_deadline = (
            result is not None
            and result["stop_reason"] == "scorer_error"
            and result["elapsed_seconds"] >= config["reasoning"]["max_seconds"] - 0.05
        )
        if code not in (0, 3) and not at_deadline:
            status = 2
            break
        if code != 0:
            status = 3
    manifest["exit_code"] = status
    save(manifest_path, manifest)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
