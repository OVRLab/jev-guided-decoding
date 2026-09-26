"""Independent recorded-memory reconstruction; this does not rerun the backbone."""

import hashlib
import math
import random
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
M = runpy.run_path(str(HERE / "memory.py"))
D = runpy.run_path(str(HERE / "provenance.py"))
C = M["C"]


def check_training(
    cases,
    refs,
    natives,
    rows,
    steps,
    targets,
    epochs,
    selection,
    memories,
    receipts,
    output,
    tok,
    manifest,
    *,
    eos,
    width=2048,
):
    import torch
    from safetensors.torch import load_file

    runtime = runpy.run_path(str(HERE.parent / "structured_correction/runtime.py"))
    specs, seeds = manifest["specs"], manifest["seeds"]
    train = [c for c in cases if c["split"] == "train"]
    dev = [c for c in cases if c["split"] == "development"]
    table = {(r["id"], r["arm"]): r for r in rows}
    expected_targets = {}
    for case in train:
        ident = case["id"]
        native = natives[ident]
        correct = C["grade"](native["text"], refs[ident])["correct"]
        expected_targets[ident] = dict(
            target_ids=C["target_ids"](
                "train",
                correct,
                native["generated_token_ids"],
                tok.encode(C["target"](refs[ident]), add_special_tokens=False),
                eos,
            ),
            preserve_native=correct,
        )
    if targets != expected_targets:
        raise ValueError("Incorrect training targets or coverage")
    expected_steps = []
    for seed in seeds:
        for name, memory, feedback in specs:
            for epoch in range(1, manifest["epochs"] + 1):
                order = list(train)
                random.Random(seed + epoch).shuffle(order)
                expected_steps.extend(
                    dict(
                        condition=name,
                        memory=memory,
                        feedback=feedback,
                        seed=seed,
                        epoch=epoch,
                        step=i,
                        id=c["id"],
                        probabilities=C["signal"](feedback, receipts[c["id"]]["probabilities"]),
                        memory_digest=memories[c["id"]][memory],
                        optimizer_update=(i + 1) % manifest["accumulate"] == 0,
                    )
                    for i, c in enumerate(order)
                )
    if len(steps) != len(expected_steps) or any(
        any(actual.get(k) != v for k, v in expected.items())
        or type(actual["loss"]) not in (int, float)
        or not math.isfinite(actual["loss"])
        or actual["loss"] < 0
        or actual["at"] < receipts[actual["id"]].get("at", natives[actual["id"]]["at"])
        or actual["at"] >= selection["at"]
        for actual, expected in zip(steps, expected_steps, strict=True)
    ):
        raise ValueError("Incorrect training order, memory, feedback, loss or timing")
    if any(a["at"] > b["at"] for a, b in zip(steps, steps[1:], strict=False)):
        raise ValueError("Nonmonotonic training order")
    expected_models = {f"{name}/{seed}" for name, _, _ in specs for seed in seeds}
    if (
        set(selection["models"]) != expected_models
        or selection["seeds"] != seeds
        or selection["specs"] != [list(s) for s in specs]
    ):
        raise ValueError("Incorrect checkpoint selection coverage")
    epoch_table = {(r["condition"], r["seed"], r["epoch"]): r for r in epochs}
    expected_epochs = {
        (name, seed, epoch)
        for name, _, _ in specs
        for seed in seeds
        for epoch in range(1, manifest["epochs"] + 1)
    }
    if len(epoch_table) != len(epochs) or set(epoch_table) != expected_epochs:
        raise ValueError("Incomplete checkpoint epoch coverage")
    digests, chosen_digests, expected_files = {}, {}, set()

    def weights(name):
        path = output / name
        if path.is_symlink() or not path.is_file():
            raise ValueError("Invalid checkpoint path")
        tensors = load_file(str(path))
        adapter = runtime["B"]["Repair"](width, manifest["rank"])
        adapter.load_state_dict(tensors, strict=True)
        if any(not torch.isfinite(t).all() for t in tensors.values()):
            raise ValueError("Nonfinite checkpoint weights")
        expected_files.add(name)
        return tensors, runtime["weight_digest"](adapter)

    for seed in seeds:
        initial = None
        for name, memory, feedback in specs:
            tensors, _ = weights(f"{name}-{seed}-initial.safetensors")
            if torch.count_nonzero(tensors["up.weight"]) or (
                initial is not None
                and any(not torch.equal(tensors[k], initial[k]) for k in initial)
            ):
                raise ValueError("Unmatched or nonzero initial checkpoint")
            initial = tensors
            scores = []
            for epoch in range(1, manifest["epochs"] + 1):
                file = f"{name}-{seed}-epoch{epoch}.safetensors"
                _, digest = weights(file)
                digests[name, seed, epoch] = digest
                dev_rows = [table[c["id"], f"development/{name}/{seed}/{epoch}"] for c in dev]
                score = sum(
                    C["grade"](r["text"], refs[r["id"]])["correct"] for r in dev_rows
                ) / len(dev)
                scores.append(score)
                record = epoch_table[name, seed, epoch]
                cohort = [
                    s
                    for s in steps
                    if (s["condition"], s["seed"], s["epoch"]) == (name, seed, epoch)
                ]
                if (
                    record["accuracy"] != score
                    or record["sha256"] != C["sha"](output / file)
                    or max(r["at"] for r in dev_rows) > record["at"]
                    or min(r["at"] for r in dev_rows) < max(s["at"] for s in cohort)
                    or record["at"] >= selection["at"]
                ):
                    raise ValueError("Changed checkpoint epoch, development score or timing")
            best = max(range(len(scores)), key=lambda i: scores[i]) + 1
            file = f"{name}-{seed}-epoch{best}.safetensors"
            expected = dict(
                epoch=best,
                scores=scores,
                file=file,
                sha256=C["sha"](output / file),
                memory=memory,
                feedback=feedback,
            )
            if selection["models"][f"{name}/{seed}"] != expected:
                raise ValueError("Incorrect development checkpoint selection")
            chosen_digests[name, seed] = digests[name, seed, best]
    if {p.name for p in output.glob("*.safetensors")} != expected_files:
        raise ValueError("Unexpected checkpoint file coverage")
    return dict(
        examples=len(steps),
        updates=sum(r["optimizer_update"] for r in steps),
        epoch_digests=digests,
        selected_digests=chosen_digests,
    )


def check_bindings(rows, bindings, expected):
    table = {(r["id"], r["arm"]): r for r in rows}
    bound = {(r["id"], r["arm"]): r for r in bindings}
    if (
        len(table) != len(rows)
        or len(bound) != len(bindings)
        or set(table) != set(bound)
        or set(table) != set(expected)
    ):
        raise ValueError("Incomplete or duplicate generation binding coverage")
    for key, row in table.items():
        binding = bound[key]
        if (
            any(
                binding[field] != expected[key][field]
                for field in ("memory_digest", "adapter_digest", "probabilities")
            )
            or binding["probabilities"] != row["probabilities"]
            or type(binding["seconds"]) not in (int, float)
            or not math.isfinite(binding["seconds"])
            or binding["seconds"] < 0
            or binding["at"] > row["at"]
        ):
            raise ValueError("Substituted memory, weights, feedback or work binding")
    return sum(r["seconds"] for r in bindings)


def check_memories(cases, natives, records, output, tok, *, eos, width=2048, layer=19):
    import torch
    from safetensors.torch import load_file

    ids = {c["id"] for c in cases}
    table = {r["id"]: r for r in records}
    if (
        len(ids) != len(cases)
        or set(natives) != ids
        or set(table) != ids
        or len(table) != len(records)
    ):
        raise ValueError("Incomplete or duplicate memory coverage")
    result, paths = {}, set()
    for case in cases:
        ident = case["id"]
        row = table[ident]
        aligned = M["positions_for"](tok, case, natives[ident], eos=eos)
        if row["input_token_ids"] != aligned["ids"] or row["positions"] != aligned["slots"]:
            raise ValueError("Memory token/position provenance mismatch")
        name = "memories/" + hashlib.sha256(ident.encode()).hexdigest() + ".safetensors"
        path = output / name
        if (
            row["file"] != name
            or path.is_symlink()
            or not path.is_file()
            or hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]
        ):
            raise ValueError("Changed or unbound memory file")
        if (
            row["shape"] != [3, width]
            or row["layer"] != layer
            or type(row["processed_tokens"]) is not int
            or row["processed_tokens"] != len(aligned["ids"])
            or type(row["seconds"]) not in (int, float)
            or not math.isfinite(row["seconds"])
            or row["seconds"] < 0
            or row["at"] < natives[ident]["at"]
        ):
            raise ValueError("Invalid extraction work or boundary")
        values = load_file(str(path))
        if set(values) != {"embedding", "contextual"} or any(
            tensor.shape != (3, width)
            or tensor.dtype != torch.float32
            or not torch.isfinite(tensor).all()
            for tensor in values.values()
        ):
            raise ValueError("Invalid memory tensors")
        result[ident] = {kind: D["tensor_digest"](v) for kind, v in values.items()}
        paths.add(name)
    actual = {str(p.relative_to(output)) for p in (output / "memories").rglob("*") if p.is_file()}
    if actual != paths:
        raise ValueError("Unexpected memory file coverage")
    return dict(
        count=len(records),
        processed_tokens=sum(r["processed_tokens"] for r in records),
        seconds=sum(r["seconds"] for r in records),
        digests=result,
    )
