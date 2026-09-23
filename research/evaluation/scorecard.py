"""Compose comparable completed task scores; never label a partial suite a full win."""

import argparse
import json
import math
from pathlib import Path

BENCHMARKS = (
    "mmlu_pro",
    "gpqa_diamond",
    "aime_2026",
    "livecodebench",
    "ifbench",
    "musr",
    "longbench_v2",
    "simpleqa_verified",
    "bfcl_v4",
    "swe_bench_verified",
)


def compose(records, models):
    if len(models) != 2 or len(set(models)) != 2:
        raise ValueError("Specify exactly two distinct model/system identities")
    indexed, revisions = {}, {}
    for r in records:
        model, task = r["model"], r["benchmark"]
        pair = model, task
        if model not in models or task not in BENCHMARKS or pair in indexed:
            raise ValueError("Unexpected or duplicate score")
        if r["scope"] != "full" or r["status"] != "complete":
            raise ValueError("Only admitted complete full-task scores are eligible")
        score = r["score"]
        if type(score) not in (int, float) or not math.isfinite(score) or not 0 <= score <= 100:
            raise ValueError("Primary score must be finite on the 0–100 scale")
        for key in ("contract", "dataset_revision", "evaluator_revision", "model_revision"):
            if not isinstance(r[key], str) or not r[key].strip():
                raise ValueError("Missing provenance: " + key)
        if revisions.setdefault(model, r["model_revision"]) != r["model_revision"]:
            raise ValueError("A single system cannot switch its checkpoint across tasks")
        indexed[pair] = r
    for task in BENCHMARKS:
        pair = [indexed.get((m, task)) for m in models]
        if all(pair) and any(
            pair[0][k] != pair[1][k] for k in ("contract", "dataset_revision", "evaluator_revision")
        ):
            raise ValueError("Incomparable task contracts: " + task)
    result = {}
    for model in models:
        cells = {b: indexed.get((model, b), {}).get("score") for b in BENCHMARKS}

        def mean(tasks, cells=cells):
            return (
                sum(cells[b] for b in tasks) / len(tasks)
                if all(cells[b] is not None for b in tasks)
                else None
            )

        result[model] = {
            "scores": cells,
            "missing": [b for b in BENCHMARKS if cells[b] is None],
            "ten_task_mean": mean(BENCHMARKS),
            "direct_task_mean": mean(BENCHMARKS[:8]),
            "agent_task_mean": mean(BENCHMARKS[8:]),
        }
    values = [result[m]["ten_task_mean"] for m in models]
    return {
        "contract_version": "granite-jev-ten-v1",
        "models": result,
        "paired_mean_difference": values[1] - values[0]
        if all(v is not None for v in values)
        else None,
        "superiority_established": False,
        "inference_note": (
            "Descriptive aggregation only; paired clustered uncertainty, multiplicity "
            "and replication are separate requirements."
        ),
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--records", type=Path, required=True)
    p.add_argument("--models", nargs=2, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    result = compose(json.loads(a.records.read_text()), a.models)
    with a.output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
