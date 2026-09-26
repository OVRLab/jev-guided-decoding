"""Matched memory/feedback training utility; a separate protocol admits live use."""

import math
import random
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
C = runpy.run_path(str(HERE.parent / "structured_correction/common.py"))
F = runpy.run_path(str(HERE.parent / "structured_correction/feedback.py"))
D = runpy.run_path(str(HERE / "provenance.py"))


def train(
    runner,
    train_cases,
    dev_cases,
    refs,
    *,
    specs,
    seeds,
    epochs=2,
    accumulate=8,
    rank=32,
    layer=19,
    lr=0.001,
):
    """Same train order, initialization and targets; choose epochs on development only."""
    import torch
    from safetensors.torch import load_file, save_file

    if (
        not train_cases
        or not dev_cases
        or any(c["split"] != "train" for c in train_cases)
        or any(c["split"] != "development" for c in dev_cases)
        or len({c["id"] for c in train_cases + dev_cases}) != len(train_cases) + len(dev_cases)
    ):
        raise ValueError("Invalid or overlapping training/development split")
    if (
        not 1 <= len(specs) <= 6
        or any(
            len(s) != 3
            or s[1] not in ("embedding", "contextual")
            or s[2] not in ("structured", "scalar", "constant")
            or s[0] != f"{s[1]}-{s[2]}"
            for s in specs
        )
        or len({s[0] for s in specs}) != len(specs)
    ):
        raise ValueError("Invalid or duplicate memory/feedback conditions")
    if (
        not 1 <= len(seeds) <= 2
        or len(set(seeds)) != len(seeds)
        or any(type(s) is not int or s < 0 for s in seeds)
        or type(epochs) is not int
        or not 1 <= epochs <= 2
        or type(accumulate) is not int
        or accumulate < 1
        or len(train_cases) % accumulate
        or not math.isfinite(lr)
        or lr <= 0
        or any(c["id"] not in refs for c in train_cases + dev_cases)
    ):
        raise ValueError("Invalid training contract")
    markers = ("training-targets.json", "training-steps.jsonl", "epochs.jsonl", "selection.json")
    if any((runner.output / name).exists() for name in markers):
        raise FileExistsError("Training output contains an earlier attempt")
    if any(p.requires_grad or p.grad is not None for p in runner.model.parameters()):
        raise ValueError("Original model must remain frozen")
    R = runpy.run_path(str(HERE.parent / "structured_correction/runtime.py"))
    output = runner.output
    device = next(runner.model.parameters()).device
    examples = {}
    for case in train_cases:
        item = runner.prepared[case["id"]]
        canonical = runner.tok.encode(C["target"](refs[case["id"]]), add_special_tokens=False)
        examples[case["id"]] = dict(
            target_ids=C["target_ids"](
                "train",
                item["grade"]["correct"],
                item["native"]["generated_token_ids"],
                canonical,
                runner.tok.convert_tokens_to_ids("<|end_of_text|>"),
            ),
            preserve_native=item["grade"]["correct"],
        )
    C["dump"](output / "training-targets.json", examples)
    selected, adapters = {}, {}
    for seed in seeds:
        for name, memory_kind, feedback_kind in specs:
            runner.deadline()
            torch.manual_seed(seed)
            adapter = R["B"]["Repair"](runner.model.config.hidden_size, rank).to(device)
            save_file(adapter.state_dict(), str(output / f"{name}-{seed}-initial.safetensors"))
            optimizer = torch.optim.AdamW(adapter.parameters(), lr=lr, weight_decay=0)
            scores = []
            for epoch in range(1, epochs + 1):
                order = list(train_cases)
                random.Random(seed + epoch).shuffle(order)
                optimizer.zero_grad(set_to_none=True)
                for step, case in enumerate(order):
                    runner.deadline()
                    item = runner.prepared[case["id"]]
                    values = C["signal"](feedback_kind, item["p"])
                    loss = R["loss_for"](
                        runner.model,
                        adapter,
                        item["prompt"],
                        examples[case["id"]]["target_ids"],
                        item["memories"][memory_kind],
                        values,
                        layer=layer,
                    )
                    if not torch.isfinite(loss):
                        raise ValueError("Nonfinite training loss")
                    (loss / accumulate).backward()
                    if any(p.grad is not None for p in runner.model.parameters()):
                        raise ValueError("Original model received gradients")
                    update = (step + 1) % accumulate == 0
                    if update:
                        norm = torch.nn.utils.clip_grad_norm_(adapter.parameters(), 1)
                        if not torch.isfinite(norm):
                            raise ValueError("Nonfinite adapter gradient")
                        optimizer.step()
                        optimizer.zero_grad(set_to_none=True)
                    F["append"](
                        output / "training-steps.jsonl",
                        dict(
                            condition=name,
                            memory=memory_kind,
                            feedback=feedback_kind,
                            probabilities=values,
                            memory_digest=D["tensor_digest"](item["memories"][memory_kind]),
                            seed=seed,
                            epoch=epoch,
                            step=step,
                            id=case["id"],
                            loss=float(loss.detach()),
                            optimizer_update=update,
                            at=F["now"](),
                        ),
                    )
                path = output / f"{name}-{seed}-epoch{epoch}.safetensors"
                save_file(adapter.state_dict(), str(path))
                correct = []
                for case in dev_cases:
                    runner.deadline()
                    item = runner.prepared[case["id"]]
                    row = runner.answer(
                        case,
                        f"development/{name}/{seed}/{epoch}",
                        item["prompt"],
                        adapter=adapter,
                        memory=item["memories"][memory_kind],
                        probabilities=C["signal"](feedback_kind, item["p"]),
                    )
                    correct.append(C["grade"](row["text"], refs[case["id"]])["correct"])
                score = sum(correct) / len(correct)
                scores.append(score)
                F["append"](
                    output / "epochs.jsonl",
                    dict(
                        condition=name,
                        seed=seed,
                        epoch=epoch,
                        accuracy=score,
                        sha256=C["sha"](path),
                        at=F["now"](),
                    ),
                )
            epoch = max(range(len(scores)), key=lambda i: scores[i]) + 1
            path = output / f"{name}-{seed}-epoch{epoch}.safetensors"
            adapter.load_state_dict(load_file(str(path), device="cpu"))
            adapter.eval().requires_grad_(False)
            selected[f"{name}/{seed}"] = dict(
                epoch=epoch,
                scores=scores,
                file=path.name,
                sha256=C["sha"](path),
                memory=memory_kind,
                feedback=feedback_kind,
            )
            adapters[name, seed] = adapter
    C["dump"](
        output / "selection.json",
        dict(models=selected, specs=specs, seeds=seeds, at=F["now"]()),
    )
    return adapters
