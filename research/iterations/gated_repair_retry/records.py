"""Supplementary R25 v4 training-sequence, inference ordering and checkpoint audit.

No generation, training, selection or primary grading changes.
"""

import argparse
import json
import math
import random
from pathlib import Path


def audit_steps(cases, rows, settings, probabilities):
    train = [c["id"] for c in cases if c["split"] == "train"]
    expected = []
    for seed in settings["seeds"]:
        for mode in ("constant", "live"):
            updates = 0
            for epoch in range(1, settings["epochs"] + 1):
                indices = list(range(len(train)))
                random.Random(seed * 10 + epoch).shuffle(indices)
                for step, index in enumerate(indices):
                    if (step + 1) % settings["accumulate"] == 0:
                        updates += 1
                    ident = train[index]
                    gate = 0.5 if mode == "constant" else 1 - probabilities[ident]
                    expected.append(
                        dict(
                            mode=mode,
                            seed=seed,
                            epoch=epoch,
                            step=step,
                            id=ident,
                            gate=gate,
                            updates=updates,
                        )
                    )
    if len(rows) != len(expected):
        raise ValueError("Missing/extra training step")
    for row, want in zip(rows, expected, strict=True):
        if any(row[k] != v for k, v in want.items() if k != "gate") or not math.isclose(
            row["gate"], want["gate"], abs_tol=1e-12, rel_tol=0
        ):
            raise ValueError("Training data, order, gate or update mismatch")
        if (
            type(row["loss"]) not in (float, int)
            or not math.isfinite(row["loss"])
            or row["loss"] < 0
        ):
            raise ValueError("Invalid loss")
    return dict(
        passed=True,
        steps=len(rows),
        train_cases=len(train),
        test_cases_used=0,
        losses={
            f"{mode}/{seed}/{epoch}": sum(
                r["loss"] for r in rows if (r["mode"], r["seed"], r["epoch"]) == (mode, seed, epoch)
            )
            / len(train)
            for seed in settings["seeds"]
            for mode in ("constant", "live")
            for epoch in range(1, settings["epochs"] + 1)
        },
    )


def run(folder, output):
    import torch
    from safetensors.torch import load_file

    settings = json.loads((folder / "manifest.json").read_text())
    cases = json.loads((folder / "cases.json").read_text())

    def read(name):
        return [json.loads(x) for x in (output / name).read_text().splitlines()]

    requests = read("api-requests.jsonl") + read("new-requests.jsonl")
    responses = read("feedback-availability.jsonl")
    probabilities = {r["id"]: r["effective_probability_correct"] for r in responses}
    result = audit_steps(cases, read("training-steps.jsonl"), settings, probabilities)
    selection = json.loads((output / "selection.json").read_text())
    tests = {c["id"] for c in cases if c["split"] == "test"}
    if any(r["at"] < selection["at"] for r in requests if r["id"] in tests):
        raise ValueError("Test feedback predates selection")
    checkpoints = {}
    for seed in settings["seeds"]:
        starts = {
            mode: load_file(str(output / f"{mode}-{seed}-initial.safetensors"))
            for mode in ("constant", "live")
        }
        if not all(
            torch.equal(starts["constant"][k], starts["live"][k]) for k in starts["constant"]
        ):
            raise ValueError("Unmatched initial weights")
        if torch.count_nonzero(starts["live"]["up.weight"]):
            raise ValueError("Initial up matrix is nonzero")
        for mode in ("constant", "live"):
            for epoch in range(1, settings["epochs"] + 1):
                name = f"{mode}-{seed}-epoch{epoch}.safetensors"
                weights = load_file(str(output / name))
                if set(weights) != set(starts[mode]) or any(
                    not torch.isfinite(v).all()
                    or v.dtype != torch.float32
                    or v.shape != starts[mode][k].shape
                    for k, v in weights.items()
                ):
                    raise ValueError("Malformed checkpoint")
                change = (
                    sum(float((v - starts[mode][k]).square().sum()) for k, v in weights.items())
                    ** 0.5
                )
                if change == 0:
                    raise ValueError("Adapter never changed")
                checkpoints[name] = dict(
                    parameters=sum(v.numel() for v in weights.values()), l2_change=change
                )
    result.update(
        missing_feedback_ids=[
            r["id"] for r in responses if r["actual_probability_correct"] is None
        ],
        checkpoints=checkpoints,
        matched_initialization=True,
        selection_before_test_api=True,
    )
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--freeze", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--save", type=Path, required=True)
    a = p.parse_args()
    with a.save.open("x") as f:
        json.dump(run(a.freeze, a.output), f, indent=2, allow_nan=False)
        f.write("\n")
