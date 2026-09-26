"""Frozen R29 preparation, bounded model execution and checkpoint selection."""

import argparse
import asyncio
import json
import platform
import random
import runpy
import subprocess
import time
from pathlib import Path

from jev_guided_decoding.experiment_budget import InputTokenBudget
from jev_guided_decoding.jev import JevScorer, load_api_key

HERE = Path(__file__).resolve().parent
C = runpy.run_path(str(HERE / "common.py"))
F = runpy.run_path(str(HERE / "feedback.py"))
append, now = F["append"], F["now"]


def prepare(output):
    output.mkdir(parents=True, exist_ok=False)
    cases, refs = C["make_data"]()
    C["dump"](output / "cases.json", cases)
    C["dump"](output / "references.json", refs)
    revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=C["ROOT"], text=True
    ).strip()
    dirty = bool(
        subprocess.check_output(["git", "status", "--porcelain"], cwd=C["ROOT"], text=True).strip()
    )
    if dirty:
        raise ValueError("Freeze requires committed source")
    manifest = dict(
        study="R29-A",
        at=now(),
        git_revision=revision,
        source_dirty=False,
        sources=C["source_hashes"](),
        files={n: C["sha"](output / n) for n in ("cases.json", "references.json")},
        model=C["MODEL"],
        revision=C["REVISION"],
        layer=19,
        rank=32,
        seeds=C["SEEDS"],
        modes=C["MODES"],
        epochs=2,
        lr=0.001,
        accumulate=8,
        limit=128,
        max_seconds=16200,
        api_cap_usd=0.18,
        usd_per_million=0.05,
        planned_cases=256,
        planned_test_cases=96,
    )
    C["dump"](output / "manifest.json", manifest)
    print(json.dumps(dict(prepared=True, manifest_sha256=C["sha"](output / "manifest.json"))))


def verify(folder):
    manifest = json.loads((folder / "manifest.json").read_text())
    if manifest["sources"] != C["source_hashes"]():
        raise ValueError("Frozen source mismatch")
    if any(C["sha"](folder / name) != value for name, value in manifest["files"].items()):
        raise ValueError("Frozen data mismatch")
    return manifest


def load_model(device):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    tok = AutoTokenizer.from_pretrained(C["MODEL"], revision=C["REVISION"])
    model = (
        AutoModelForCausalLM.from_pretrained(
            C["MODEL"],
            revision=C["REVISION"],
            torch_dtype=torch.float32,
            attn_implementation="sdpa",
        )
        .to(device)
        .eval()
    )
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    eos = model.generation_config.eos_token_id
    eos = eos if isinstance(eos, list) else [eos]
    return model, tok, eos


class Runner:
    def __init__(self, model, tok, eos, manifest, output, feedback):
        self.model, self.tok, self.eos, self.m = model, tok, eos, manifest
        self.output, self.feedback = output, feedback
        self.runtime = runpy.run_path(str(HERE / "runtime.py"))
        self.started = time.monotonic()
        self.prepared, self.rows = {}, []

    def deadline(self):
        if time.monotonic() - self.started > self.m["max_seconds"]:
            raise TimeoutError("R29 worker deadline")

    def answer(self, case, arm, prompt, *, adapter=None, memory=None, probabilities=None):
        self.deadline()
        append(self.output / "jobs.jsonl", dict(id=case["id"], arm=arm, event="start", at=now()))
        row = self.runtime["generate"](
            self.model,
            self.tok,
            prompt,
            limit=self.m["limit"],
            eos=self.eos,
            adapter=adapter,
            memory=memory,
            probabilities=probabilities,
            layer=self.m["layer"],
            deadline=self.deadline,
        )
        row.update(
            id=case["id"],
            arm=arm,
            task=case["task"],
            split=case["split"],
            probabilities=probabilities,
            at=now(),
        )
        append(self.output / "outputs.jsonl", row)
        self.rows.append(row)
        append(self.output / "jobs.jsonl", dict(id=case["id"], arm=arm, event="finish", at=now()))
        print(
            json.dumps(
                dict(
                    stage="generation",
                    id=case["id"],
                    arm=arm,
                    tokens=len(row["generated_token_ids"]),
                    seconds=row["seconds"],
                )
            ),
            flush=True,
        )
        return row

    async def drafts(self, cases, refs):
        for case in cases:
            self.deadline()
            C["validate_case"](case)
            ids = self.tok.apply_chat_template(
                [dict(role="user", content=case["prompt"])],
                tokenize=True,
                add_generation_prompt=True,
            )
            row = self.answer(case, "native", ids)
            p = await self.feedback.score(case, row["text"])
            memory = self.runtime["B"]["memory_for"](self.model, self.tok, case, row["text"])
            grade = C["grade"](row["text"], refs[case["id"]])
            self.prepared[case["id"]] = dict(
                native=row,
                p=p,
                grade=grade,
                memory=memory,
                prompt=C["repair_prefix"](self.tok, ids, row["generated_token_ids"]),
                text_prompt=C["repair_prefix"](
                    self.tok, ids, row["generated_token_ids"], feedback=p
                ),
            )

    def repair(self, case, arm, adapter, mode, p=None):
        item = self.prepared[case["id"]]
        values = C["signal"](mode, item["p"] if p is None else p, item["grade"]["slots"])
        return self.answer(
            case,
            arm,
            item["text_prompt"] if mode == "text" else item["prompt"],
            adapter=adapter,
            memory=item["memory"],
            probabilities=values,
        )

    def train(self, train, dev, refs):
        import torch
        from safetensors.torch import load_file, save_file

        device = next(self.model.parameters()).device
        examples = {}
        for case in train:
            item = self.prepared[case["id"]]
            canonical = self.tok.encode(C["target"](refs[case["id"]]), add_special_tokens=False)
            ids = C["target_ids"](
                "train",
                item["grade"]["correct"],
                item["native"]["generated_token_ids"],
                canonical,
                self.tok.convert_tokens_to_ids("<|end_of_text|>"),
            )
            examples[case["id"]] = dict(target_ids=ids, preserve_native=item["grade"]["correct"])
        C["dump"](self.output / "training-targets.json", examples)
        selected, adapters, thresholds = {}, {}, {}
        for seed in self.m["seeds"]:
            for mode in self.m["modes"]:
                torch.manual_seed(seed)
                adapter = self.runtime["B"]["Repair"](
                    self.model.config.hidden_size, self.m["rank"]
                ).to(device)
                save_file(
                    adapter.state_dict(), str(self.output / f"{mode}-{seed}-initial.safetensors")
                )
                opt = torch.optim.AdamW(adapter.parameters(), lr=self.m["lr"], weight_decay=0)
                scores, dev_results = [], []
                for epoch in range(1, self.m["epochs"] + 1):
                    order = list(train)
                    random.Random(seed + epoch).shuffle(order)
                    opt.zero_grad(set_to_none=True)
                    for step, case in enumerate(order):
                        self.deadline()
                        item = self.prepared[case["id"]]
                        p = C["signal"](mode, item["p"], item["grade"]["slots"])
                        prompt = item["text_prompt"] if mode == "text" else item["prompt"]
                        loss = self.runtime["loss_for"](
                            self.model,
                            adapter,
                            prompt,
                            examples[case["id"]]["target_ids"],
                            item["memory"],
                            p,
                            layer=self.m["layer"],
                        )
                        if not torch.isfinite(loss):
                            raise ValueError("Nonfinite training loss")
                        (loss / self.m["accumulate"]).backward()
                        if (step + 1) % self.m["accumulate"] == 0:
                            norm = torch.nn.utils.clip_grad_norm_(adapter.parameters(), 1)
                            if not torch.isfinite(norm):
                                raise ValueError("Nonfinite adapter gradient")
                            opt.step()
                            opt.zero_grad(set_to_none=True)
                        append(
                            self.output / "training-steps.jsonl",
                            dict(
                                mode=mode,
                                seed=seed,
                                epoch=epoch,
                                step=step,
                                id=case["id"],
                                loss=float(loss.detach()),
                                at=now(),
                            ),
                        )
                        if (step + 1) % 32 == 0:
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
                        p.grad is not None for p in self.model.parameters()
                    ):
                        raise ValueError("Invalid accumulation or base gradient")
                    path = self.output / f"{mode}-{seed}-epoch{epoch}.safetensors"
                    save_file(adapter.state_dict(), str(path))
                    correct = []
                    for case in dev:
                        row = self.repair(case, f"development/{mode}/{seed}/{epoch}", adapter, mode)
                        correct.append(C["grade"](row["text"], refs[case["id"]])["correct"])
                    score = sum(correct) / len(correct)
                    scores.append(score)
                    dev_results.append(correct)
                    append(
                        self.output / "epochs.jsonl",
                        dict(
                            mode=mode,
                            seed=seed,
                            epoch=epoch,
                            accuracy=score,
                            sha256=C["sha"](path),
                            at=now(),
                        ),
                    )
                epoch = max(range(len(scores)), key=lambda i: scores[i]) + 1
                path = self.output / f"{mode}-{seed}-epoch{epoch}.safetensors"
                adapter.load_state_dict(load_file(str(path), device="cpu"))
                adapter.eval()
                selected[f"{mode}/{seed}"] = dict(
                    epoch=epoch, scores=scores, file=path.name, sha256=C["sha"](path)
                )
                adapters[mode, seed] = adapter
                if mode == "structured":
                    thresholds[str(seed)] = C["choose_threshold"](
                        [min(self.prepared[c["id"]]["p"]) for c in dev],
                        [self.prepared[c["id"]]["grade"]["correct"] for c in dev],
                        dev_results[epoch - 1],
                    )
        C["dump"](
            self.output / "selection.json", dict(models=selected, thresholds=thresholds, at=now())
        )
        return adapters

    def test(self, cases, adapters):
        donors = {}
        for task in ("temporal", "compositional"):
            ids = sorted(c["id"] for c in cases if c["task"] == task)
            donors.update({ident: ids[(i + 1) % len(ids)] for i, ident in enumerate(ids)})
        C["dump"](self.output / "donors.json", donors)
        for case in cases:
            item = self.prepared[case["id"]]
            self.answer(case, "blind", item["prompt"])
            for seed in self.m["seeds"]:
                for mode in self.m["modes"]:
                    self.repair(case, f"{mode}/{seed}", adapters[mode, seed], mode)
                self.repair(
                    case,
                    f"shuffled/{seed}",
                    adapters["structured", seed],
                    "structured",
                    p=self.prepared[donors[case["id"]]]["p"],
                )


async def execute(args):
    manifest = verify(args.input)
    args.output.mkdir(parents=True, exist_ok=False)
    C["dump"](
        args.output / "execution.json",
        dict(
            at=now(),
            device=args.device,
            python=platform.python_version(),
            manifest_sha256=C["sha"](args.input / "manifest.json"),
            sources=C["source_hashes"](),
        ),
    )
    cases = json.loads((args.input / "cases.json").read_text())
    refs = json.loads((args.input / "references.json").read_text())
    model, tok, eos = load_model(args.device)
    import torch
    import transformers

    C["dump"](
        args.output / "hardware.json",
        dict(
            device=args.device,
            gpu=torch.cuda.get_device_name() if args.device == "cuda" else None,
            torch=torch.__version__,
            transformers=transformers.__version__,
            python=platform.python_version(),
            parameters=sum(p.numel() for p in model.parameters()),
            dtype=str(next(model.parameters()).dtype),
            eos=eos,
        ),
    )
    runtime = runpy.run_path(str(HERE / "runtime.py"))
    before = runtime["weight_digest"](model)
    C["dump"](
        args.output / "mechanical-admission.json", runtime["admission"](model, tok, cases[0], eos)
    )
    with InputTokenBudget(
        args.output / "budget.jsonl",
        max_usd=manifest["api_cap_usd"],
        usd_per_million=manifest["usd_per_million"],
    ) as budget:
        scorer = JevScorer(load_api_key(args.key_file), model="jev-1.13.0", max_retries=0)
        try:
            feedback = F["Feedback"](scorer, budget, args.output)
            runner = Runner(model, tok, eos, manifest, args.output, feedback)
            train = [c for c in cases if c["split"] == "train"]
            dev = [c for c in cases if c["split"] == "development"]
            test = [c for c in cases if c["split"] == "test"]
            await runner.drafts(train + dev, refs)
            native_errors = sum(not runner.prepared[c["id"]]["grade"]["correct"] for c in dev)
            C["dump"](
                args.output / "development-admission.json",
                dict(native_errors=native_errors, n=len(dev), passed=native_errors >= 4),
            )
            if native_errors < 4:
                C["dump"](
                    args.output / "stopped.json",
                    dict(reason="Fewer than four development errors", at=now()),
                )
                return
            adapters = runner.train(train, dev, refs)
            await runner.drafts(test, refs)
            runner.test(test, adapters)
            after = runtime["weight_digest"](model)
            if before != after or budget.unresolved:
                raise ValueError("Backbone changed or unresolved charge")
            C["dump"](
                args.output / "complete.json",
                dict(
                    at=now(),
                    outputs=len(runner.rows),
                    backbone_before=before,
                    backbone_after=after,
                    charged_input_tokens=budget.charged_tokens,
                    seconds=time.monotonic() - runner.started,
                ),
            )
        finally:
            await scorer.__aexit__(None, None, None)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run"))
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--device", default="cuda", choices=("cuda", "mps", "cpu"))
    parser.add_argument("--key-file", type=Path, default=Path.home() / ".typesafe.ai/jev")
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.output)
    else:
        try:
            asyncio.run(execute(args))
        except BaseException as exc:
            if args.output.is_dir():
                C["dump"](
                    args.output / "failed.json", dict(error_type=type(exc).__name__, at=now())
                )
            raise


if __name__ == "__main__":
    main()
