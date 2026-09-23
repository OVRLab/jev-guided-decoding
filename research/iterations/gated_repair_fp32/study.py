"""R25 v2: full-precision drafts, bounded feedback and matched repair training."""

import argparse
import asyncio
import json
import os
import platform
import random
import runpy
import time
from datetime import UTC, datetime
from pathlib import Path

from jev_guided_decoding.experiment_budget import InputTokenBudget
from jev_guided_decoding.jev import JevScorer, _probability, load_api_key

HERE = Path(__file__).resolve().parent
C = runpy.run_path(str(HERE / "common.py"))


def now():
    return datetime.now(UTC).isoformat()


def append(path, value):
    with path.open("a") as f:
        f.write(json.dumps(value, allow_nan=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def training_target(case, targets):
    if case["split"] != "train" or case["id"] not in targets:
        raise ValueError("Training target outside admitted train split")
    return targets[case["id"]]


async def request_feedback(case, draft, scorer, budget, output):
    payload = C["feedback_payload"](case, draft)
    reservation = budget.reserve()
    append(
        output / "api-requests.jsonl",
        dict(id=case["id"], payload=payload, reservation=reservation, at=now()),
    )
    try:
        p, version, tokens, out, attempts, seconds, raw = await scorer._evaluate(
            payload, lambda a: _probability(a, "correct"), timeout=30, max_attempts=1
        )
        if version != "jev-1.13.0" or attempts != 1:
            raise ValueError("Unexpected model version/attempts")
        budget.settle(reservation, tokens)
        receipt = dict(
            id=case["id"],
            probability_correct=p,
            model=version,
            input_tokens=tokens,
            output_tokens=out,
            attempts=attempts,
            seconds=seconds,
            raw=raw,
            reservation=reservation,
            at=now(),
        )
        append(output / "api-responses.jsonl", receipt)
        return p
    except Exception as exc:
        append(
            output / "api-failures.jsonl",
            dict(
                id=case["id"],
                error_type=type(exc).__name__,
                usage_unknown=True,
                reservation=reservation,
                at=now(),
            ),
        )
        raise


class Runner:
    def __init__(self, model, tok, eos, m, output, scorer, budget, started):
        self.model, self.tok, self.eos, self.m, self.output = model, tok, eos, m, output
        self.scorer, self.budget, self.started = scorer, budget, started
        self.runtime = runpy.run_path(str(HERE / "runtime.py"))
        self.prepared = {}

    def deadline(self):
        if time.monotonic() - self.started > self.m["max_seconds"]:
            raise TimeoutError("Study deadline; unfinished work stays incomplete")

    def answer(self, case, arm, ids, *, adapter=None, gate=0.5):
        self.deadline()
        append(self.output / "jobs.jsonl", dict(event="start", id=case["id"], arm=arm, at=now()))
        result = self.runtime["generate"](
            self.model,
            self.tok,
            ids,
            limit=self.m["draft_limit"] if arm == "native" else self.m["repair_limit"],
            eos=self.eos,
            adapter=adapter,
            gate=gate,
            layer=self.m["layer"],
            deadline=self.deadline,
        )
        row = dict(
            id=case["id"],
            task=case["task"],
            split=case["split"],
            arm=arm,
            prompt_sha256=C["digest"](case["prompt"]),
            gate=gate if adapter is not None else None,
            at=now(),
            **result,
        )
        append(self.output / "outputs.jsonl", row)
        append(self.output / "jobs.jsonl", dict(event="finish", id=case["id"], arm=arm, at=now()))
        print(
            json.dumps(
                dict(
                    stage="generation",
                    id=case["id"],
                    split=case["split"],
                    arm=arm,
                    tokens=len(result["generated_token_ids"]),
                    seconds=result["seconds"],
                )
            ),
            flush=True,
        )
        return row

    async def drafts(self, cases):
        for case in cases:
            C["validate_case"](case)
            self.deadline()
            ids = self.tok.apply_chat_template(
                [dict(role="user", content=case["prompt"])],
                tokenize=True,
                add_generation_prompt=True,
            )
            native = self.answer(case, "native", ids)
            self.deadline()
            p = await request_feedback(
                case, native["text"] or "(empty response)", self.scorer, self.budget, self.output
            )
            prefix = C["repair_prefix"](self.tok, ids, native["generated_token_ids"])
            if len(prefix) > self.m["input_limit"]:
                raise ValueError("Repair context exceeds admission limit")
            self.prepared[case["id"]] = dict(native=native, p=p, prefix=prefix)

    def train(self, train, dev, targets, refs):
        import torch
        from safetensors.torch import load_file, save_file

        examples = []
        for case in train:
            target = self.tok.encode(training_target(case, targets), add_special_tokens=False) + [
                self.tok.convert_tokens_to_ids("<|end_of_text|>")
            ]
            prefix = self.prepared[case["id"]]["prefix"]
            if (
                len(target) > self.m["target_limit"]
                or len(prefix) + len(target) > self.m["input_limit"]
            ):
                raise ValueError("Oversized training example; admission failed")
            examples.append(dict(id=case["id"], prompt_ids=prefix, target_ids=target))
        C["dump"](self.output / "training-examples.json", examples)
        selected, adapters = {}, {}
        for seed in self.m["seeds"]:
            for mode in ("constant", "live"):
                torch.manual_seed(seed)
                adapter = self.runtime["B"]["Repair"](
                    self.model.config.hidden_size, self.m["rank"]
                ).to("cuda")
                save_file(
                    adapter.state_dict(), str(self.output / f"{mode}-{seed}-initial.safetensors")
                )
                optimizer = torch.optim.AdamW(adapter.parameters(), lr=self.m["lr"], weight_decay=0)
                scores = []
                updates = 0
                for epoch in range(1, self.m["epochs"] + 1):
                    order = list(range(len(examples)))
                    random.Random(seed * 10 + epoch).shuffle(order)
                    optimizer.zero_grad(set_to_none=True)
                    for step, index in enumerate(order):
                        self.deadline()
                        example = examples[index]
                        gate = 1 - self.prepared[example["id"]]["p"] if mode == "live" else 0.5
                        loss = self.runtime["loss_for"](
                            self.model,
                            adapter,
                            example["prompt_ids"],
                            example["target_ids"],
                            gate,
                            layer=self.m["layer"],
                        )
                        if not torch.isfinite(loss):
                            raise ValueError("Nonfinite loss")
                        (loss / self.m["accumulate"]).backward()
                        if (step + 1) % self.m["accumulate"] == 0:
                            norm = torch.nn.utils.clip_grad_norm_(
                                adapter.parameters(), self.m["clip"]
                            )
                            if not torch.isfinite(norm):
                                raise ValueError("Nonfinite gradient")
                            optimizer.step()
                            optimizer.zero_grad(set_to_none=True)
                            updates += 1
                        append(
                            self.output / "training-steps.jsonl",
                            dict(
                                mode=mode,
                                seed=seed,
                                epoch=epoch,
                                step=step,
                                id=example["id"],
                                gate=gate,
                                loss=float(loss.detach()),
                                updates=updates,
                                at=now(),
                            ),
                        )
                        if (step + 1) % 64 == 0:
                            print(
                                json.dumps(
                                    dict(
                                        stage="training",
                                        mode=mode,
                                        seed=seed,
                                        epoch=epoch,
                                        step=step + 1,
                                    )
                                ),
                                flush=True,
                            )
                    if len(order) % self.m["accumulate"] or any(
                        p.grad is not None or p.requires_grad for p in self.model.parameters()
                    ):
                        raise ValueError("Gradient ownership/accumulation failure")
                    path = self.output / f"{mode}-{seed}-epoch{epoch}.safetensors"
                    save_file(adapter.state_dict(), str(path))
                    correct = []
                    for case in dev:
                        item = self.prepared[case["id"]]
                        row = self.answer(
                            case,
                            f"dev/{mode}/{seed}/{epoch}",
                            item["prefix"],
                            adapter=adapter,
                            gate=1 - item["p"] if mode == "live" else 0.5,
                        )
                        correct.append(
                            C["R"]["readout"](case["prompt"], row["text"], refs[case["id"]])[
                                "correct"
                            ]
                        )
                    score = sum(correct) / len(correct)
                    scores.append(score)
                    append(
                        self.output / "epochs.jsonl",
                        dict(
                            mode=mode,
                            seed=seed,
                            epoch=epoch,
                            accuracy=score,
                            updates=updates,
                            sha256=C["sha"](path),
                            at=now(),
                        ),
                    )
                epoch = C["choose_epoch"](scores)
                path = self.output / f"{mode}-{seed}-epoch{epoch}.safetensors"
                adapter.load_state_dict(load_file(str(path), device="cuda"))
                adapter.eval()
                adapters[mode, seed] = adapter
                selected[f"{mode}/{seed}"] = dict(
                    epoch=epoch, scores=scores, file=path.name, sha256=C["sha"](path)
                )
        C["dump"](self.output / "selection.json", dict(at=now(), models=selected))
        return adapters

    def test(self, cases, adapters):
        donors = C["donors"](cases)
        C["dump"](self.output / "donors.json", donors)
        for case in cases:
            item = self.prepared[case["id"]]
            self.answer(case, "blind", item["prefix"])
            prefix = C["repair_prefix"](
                self.tok,
                item["native"]["prompt_token_ids"],
                item["native"]["generated_token_ids"],
                probability=item["p"],
            )
            self.answer(case, "text", prefix)
            for seed in self.m["seeds"]:
                self.answer(
                    case,
                    f"constant/{seed}",
                    item["prefix"],
                    adapter=adapters["constant", seed],
                    gate=0.5,
                )
                for name, gate in [
                    ("live", 1 - item["p"]),
                    ("shuffled", 1 - self.prepared[donors[case["id"]]]["p"]),
                    ("inverted", item["p"]),
                ]:
                    self.answer(
                        case,
                        f"{name}/{seed}",
                        item["prefix"],
                        adapter=adapters["live", seed],
                        gate=gate,
                    )


async def run(folder, output, key_file):
    import torch
    import transformers
    from huggingface_hub import snapshot_download
    from transformers import AutoModelForCausalLM, AutoTokenizer

    m = C["verify"](folder)
    cases = json.loads((folder / "cases.json").read_text())
    for c in cases:
        C["validate_case"](c)
    if not torch.cuda.is_available():
        raise ValueError("CUDA L40S required")
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    C["dump"](
        output / "start.json", dict(at=now(), manifest_sha256=C["sha"](folder / "manifest.json"))
    )
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    local = Path(
        snapshot_download(
            m["model"],
            revision=m["revision"],
            allow_patterns=["*.json", "*.jinja", "*.txt", "*.safetensors"],
        )
    )
    tok = AutoTokenizer.from_pretrained(local, trust_remote_code=False)
    model = (
        AutoModelForCausalLM.from_pretrained(
            local, trust_remote_code=False, dtype=torch.float32, attn_implementation="sdpa"
        )
        .to("cuda")
        .eval()
        .requires_grad_(False)
    )
    eos = model.generation_config.eos_token_id
    eos = [eos] if isinstance(eos, int) else eos
    runtime = runpy.run_path(str(HERE / "runtime.py"))
    before = runtime["weight_digest"](model)
    C["dump"](
        output / "hardware.json",
        dict(
            at=now(),
            gpu=torch.cuda.get_device_name(),
            python=platform.python_version(),
            torch=torch.__version__,
            transformers=transformers.__version__,
            parameters=sum(p.numel() for p in model.parameters()),
            original_weights_sha256=before,
            eos_ids=eos,
            model_files={p.name: C["sha"](p) for p in sorted(local.iterdir()) if p.is_file()},
        ),
    )
    ids = tok.apply_chat_template(
        [dict(role="user", content=cases[0]["prompt"])], tokenize=True, add_generation_prompt=True
    )
    C["dump"](output / "admission.json", runtime["admission"](model, tok, ids, eos, m["layer"]))
    parts = {
        part: [c for c in cases if c["split"] == part] for part in ("train", "development", "test")
    }
    targets = {
        r["id"]: r["target"] for r in json.loads((folder / "training-targets.json").read_text())
    }
    refs = {r["id"]: r for r in json.loads((folder / "development-references.json").read_text())}
    with InputTokenBudget(
        output / "budget.jsonl", max_usd=m["jev_cap"], usd_per_million=m["usd_per_million"]
    ) as budget:
        async with JevScorer(load_api_key(key_file), model=m["jev"], max_retries=0) as scorer:
            runner = Runner(model, tok, eos, m, output, scorer, budget, started)
            await runner.drafts(parts["train"] + parts["development"])
            adapters = runner.train(parts["train"], parts["development"], targets, refs)
            await runner.drafts(parts["test"])
            runner.test(parts["test"], adapters)
        after = runtime["weight_digest"](model)
        if before != after or any(
            p.requires_grad or p.grad is not None for p in model.parameters()
        ):
            raise ValueError("Original weights changed")
        C["dump"](
            output / "completion.json",
            dict(
                at=now(),
                seconds=time.monotonic() - started,
                original_weights_sha256=after,
                original_weights_unchanged=True,
                known_input_tokens=sum(budget.settled.values()),
                reserved_unknown_calls=len(budget.unresolved),
                usd=budget.charged_tokens * m["usd_per_million"] / 1e6,
                peak_allocated_bytes=torch.cuda.max_memory_allocated(),
            ),
        )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--freeze", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--key-file", type=Path, required=True)
    a = p.parse_args()
    try:
        asyncio.run(run(a.freeze, a.output, a.key_file))
    except Exception as exc:
        if a.output.is_dir():
            append(a.output / "failure.jsonl", dict(at=now(), error_type=type(exc).__name__))
        raise
