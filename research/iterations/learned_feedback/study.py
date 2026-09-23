"""Frozen-cohort learned feedback bridge study, with matched training and ablations."""

import argparse
import asyncio
import json
import math
import platform
import random
import runpy
import subprocess
import time
from dataclasses import asdict
from pathlib import Path

from jev_guided_decoding.experiment_budget import InputTokenBudget
from jev_guided_decoding.jev import load_api_key
from jev_guided_decoding.local_claims import LocalClaimScorer

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
S = runpy.run_path(str(HERE.parent / "semantic_feedback/study.py"))
D = runpy.run_path(str(HERE.parent / "semantic_feedback_replication/data.py"))
J = S["J"]
SEEDS = (2201, 2202)
ARMS = (("native", 0),) + tuple(
    (mode, seed) for seed in SEEDS for mode in ("constant", "live", "permuted", "oracle")
)


def source_hashes():
    hashes = S["source_hashes"]()
    for p in [
        *HERE.glob("*.py"),
        HERE.parent / "semantic_feedback_replication/data.py",
        HERE.parent / "adaptive_attention/attention.py",
        ROOT / "research/learned-feedback-bridge-plan.md",
    ]:
        hashes[str(p.relative_to(ROOT))] = S["sha"](p)
    return dict(sorted(hashes.items()))


def verify(folder):
    m = json.loads((folder / "manifest.json").read_text())
    if m["sources"] != source_hashes() or any(
        S["sha"](folder / p) != h for p, h in m["datasets"].items()
    ):
        raise ValueError("Learned bridge source/data freeze mismatch")
    return m


def donor_map(cases):
    mapping = {}
    for motif in sorted({c["motif"] for c in cases}):
        ids = sorted(c["id"] for c in cases if c["motif"] == motif)
        if len(ids) < 2:
            raise ValueError("Permutation needs two cases per motif")
        random.Random("r22-permutation/" + motif).shuffle(ids)
        mapping.update({ident: ids[(i + 1) % len(ids)] for i, ident in enumerate(ids)})
    return mapping


def choose_epoch(scores):
    if len(scores) != 2 or any(
        type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 1 for v in scores
    ):
        raise ValueError("Invalid development scores")
    return max(range(2), key=lambda i: (scores[i], -i)) + 1


def prepare(folder, admission):
    # Bind the independently reconstructed R21B admission, not a provider's confidence.
    summary = json.loads((admission / "replication/analysis.json").read_text())
    audit = json.loads((admission / "replication-audit.json").read_text())
    if not summary["admitted"] or not audit["passed"] or not audit["admitted"]:
        raise ValueError("R21B feedback admission required")
    audited = audit.get("output_files", {})
    if not audited or audit.get("cases") != 384:
        raise ValueError("Missing bound feedback admission artifacts")
    for name, digest in audited.items():
        path = admission / "replication" / name
        if Path(name).name != name or not path.is_file() or S["sha"](path) != digest:
            raise ValueError("Feedback admission artifact mismatch")
    dirty = bool(
        subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()
    )
    folder.mkdir(parents=True, exist_ok=False)
    excluded = set()
    for name in ("semantic-feedback-v1", "semantic-feedback-replication-v1"):
        for c in json.loads((ROOT / "research/protocols" / name / "cases.json").read_text()):
            excluded.update(c["people"])
            excluded.add(c["parcel"].removeprefix("Parcel-"))
    cohorts = {}
    for part, count, seed in (
        ("train", 384, 220923101),
        ("development", 96, 220923102),
        ("test", 384, 220923103),
    ):
        values = D["worlds"](count, seed=seed, excluded=excluded)
        for c in values:
            c["split"] = part
            excluded.update(c["people"])
            excluded.add(c["parcel"].removeprefix("Parcel-"))
        cohorts[part] = values
        S["dump"](folder / (part + ".json"), values)
    S["dump"](folder / "donors.json", donor_map(cohorts["test"]))
    S["dump"](folder / "feedback-admission.json", dict(summary=summary, audit=audit))
    m = dict(
        protocol="r22-learned-feedback-bridge-v1",
        at=J["now"](),
        sources=source_hashes(),
        datasets={p.name: S["sha"](p) for p in folder.glob("*.json")},
        source_revision=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        source_dirty=dirty,
        model=S["MODEL"],
        revision=S["REVISION"],
        precision="float32",
        jev="jev-1.13.0",
        rank=16,
        layer=19,
        seeds=list(SEEDS),
        arms=list(ARMS),
        learning_rate=0.003,
        epochs=2,
        accumulate=8,
        gradient_clip=1.0,
        weight_decay=0.0,
        draft_limit=24,
        final_limit=8,
        max_input_tokens=2048,
        max_seconds=14400,
        max_api_usd=0.50,
        cloud_allowance_usd=10,
        usd_per_million=0.042,
        prior_spend_usd=32.58346360254077,
        cumulative_budget_usd=50,
        train_worlds=384,
        development_worlds=96,
        test_worlds=384,
        test_outputs=3456,
    )
    S["dump"](folder / "manifest.json", m)
    return m


def analyze(cases, rows):
    index = {(r["case_id"], r["mode"], r["seed"]): r for r in rows}
    expected = {(c["id"], mode, seed) for c in cases for mode, seed in ARMS}
    if len(index) != len(rows) or set(index) != expected:
        raise ValueError("Test output coverage mismatch")
    by_arm = {}
    for mode, seed in ARMS:
        values = [index[c["id"], mode, seed] for c in cases]
        by_arm[f"{mode}/{seed}"] = dict(
            correct=sum(r["grade"]["correct"] for r in values),
            n=len(values),
            accuracy=sum(r["grade"]["correct"] for r in values) / len(values),
            generated_tokens=sum(len(r["token_ids"]) for r in values),
            forwards=sum(r["forwards"] for r in values),
            processed_tokens=sum(r["processed_tokens"] for r in values),
            mean_seconds=sum(r["seconds"] for r in values) / len(values),
        )
    contrasts = {}
    for control in ("native", "constant", "permuted", "oracle"):
        deltas = []
        for c in cases:
            live = sum(index[c["id"], "live", seed]["grade"]["correct"] for seed in SEEDS) / 2
            other = (
                int(index[c["id"], "native", 0]["grade"]["correct"])
                if control == "native"
                else sum(index[c["id"], control, seed]["grade"]["correct"] for seed in SEEDS) / 2
            )
            deltas.append(live - other)
        rng = random.Random("r22-bootstrap/" + control)
        draws = sorted(sum(rng.choices(deltas, k=len(deltas))) / len(deltas) for _ in range(10000))
        contrasts["live-" + control] = dict(
            difference=sum(deltas) / len(deltas),
            interval=[draws[124], draws[9874]],
            primary=control in ("native", "constant"),
            interval_level=0.975,
        )
    return dict(worlds=len(cases), outputs=len(rows), arms=by_arm, contrasts=contrasts)


class Runner:
    def __init__(self, folder, output, manifest, journal, base, runtime, scorer):
        self.folder, self.output, self.m, self.log = folder, output, manifest, journal
        self.base, self.runtime, self.scorer = base, runtime, scorer
        self.started = time.monotonic()
        self.prepared = {}

    def deadline(self):
        if time.monotonic() - self.started > self.m["max_seconds"]:
            raise TimeoutError("R22 process deadline")

    async def prepare_case(self, c):
        self.deadline()
        ident = "prepare/" + c["id"]
        metadata = dict(case_id=c["id"], part=c["split"], motif=c["motif"])
        if not self.log.start(ident, metadata):
            raise ValueError("No repeated preparation/paid attempts")
        row = {**metadata, "status": "started"}
        tok = self.base.tokenizer
        try:
            messages = D["messages"](c)
            prompt = tok.apply_chat_template(messages, tokenize=True, add_generation_prompt=True)
            if len(prompt) > self.m["max_input_tokens"]:
                raise ValueError("Input token ceiling")
            row.update(messages=messages, prompt_token_ids=prompt)
            if c["split"] == "train":
                draft = c["owner"]
                row["draft_origin"] = "authored_training_pair"
            else:
                generated = self.runtime["generate"](self.base, prompt, limit=self.m["draft_limit"])
                draft = generated["text"]
                row.update(
                    draft_origin="granite",
                    draft_generation=generated,
                    draft_oracle=D["assess"](c, draft),
                )
                final = self.runtime["final_prefix"](
                    tok, prompt, generated["token_ids"], c["final_question"]
                )
                row.update(final_prompt_ids=final["ids"], framing_ids=final["framing_ids"])
            row["draft"] = draft
            J["append"](self.output / "prepared-drafts.jsonl", {**row, "at": J["now"]()})
            request, candidates, order = S["feedback_inputs"](c, draft)
            row.update(
                question_order=order, payload=self.scorer._build_payload(request, "", candidates)
            )
            J["append"](self.output / "provider-attempts.jsonl", {**row, "at": J["now"]()})
            result = await self.scorer.score(request, "", candidates, timeout=60)
            judgments = dict(zip(order, result.judgments, strict=True))
            feedback = {k: [v.support, v.assessable] for k, v in judgments.items()}
            row.update(jev=asdict(result), feedback=feedback, status="complete")
            if c["split"] == "train":
                variants = []
                for kind, name in (
                    ("constructed_supported", c["owner"]),
                    ("constructed_unsupported", c["wrong_owner"]),
                ):
                    draft_ids = tok.encode(name, add_special_tokens=False) + [
                        tok.convert_tokens_to_ids("<|end_of_text|>")
                    ]
                    final = self.runtime["final_prefix"](
                        tok, prompt, draft_ids, c["final_question"]
                    )
                    target = tok.encode(c["answer"], add_special_tokens=False) + [
                        tok.convert_tokens_to_ids("<|end_of_text|>")
                    ]
                    variants.append(
                        dict(
                            kind=kind,
                            draft_token_ids=draft_ids,
                            framing_ids=final["framing_ids"],
                            prompt_ids=final["ids"],
                            target_ids=target,
                            feedback=feedback[kind],
                        )
                    )
                row["variants"] = variants
            self.log.finish(ident, row)
            self.prepared[c["id"]] = row
            return row
        except BaseException as exc:
            row.update(status="failed", error_type=type(exc).__name__)
            self.log.finish(ident, row)
            raise

    def answer(self, c, mode, seed, adapter, feedback, *, part, epoch=0):
        self.deadline()
        row = self.prepared[c["id"]]
        ident = f"{part}/{mode}/{seed}/{epoch}/{c['id']}"
        meta = dict(case_id=c["id"], mode=mode, seed=seed, part=part, epoch=epoch)
        if not self.log.start(ident, meta):
            raise ValueError("Generated result cannot be replayed")
        try:
            result = self.runtime["generate"](
                self.base,
                row["final_prompt_ids"],
                limit=self.m["final_limit"],
                adapter=adapter,
                feedback=feedback,
                layer=self.m["layer"],
            )
            result.update(
                meta,
                feedback=list(feedback),
                grade=self.runtime["grade"](c["answer"], result["text"]),
                status="complete",
            )
            self.log.finish(ident, result)
            J["append"](self.output / (part + "-answers.jsonl"), result)
            return result
        except BaseException as exc:
            self.log.finish(ident, dict(**meta, status="failed", error_type=type(exc).__name__))
            raise

    def train(self, train_cases, dev_cases):
        import torch
        from safetensors.torch import load_file, save_file

        B = self.runtime["B"]
        selected, adapters = {}, {}
        examples = [
            (c["id"], variant)
            for c in train_cases
            for variant in self.prepared[c["id"]]["variants"]
        ]
        for seed in SEEDS:
            for mode in ("constant", "live"):
                self.deadline()
                torch.manual_seed(seed)
                adapter = B["Bridge"](self.base.model.config.hidden_size, self.m["rank"]).to(
                    self.base.device
                )
                save_file(
                    adapter.state_dict(), str(self.output / f"{mode}-{seed}-initial.safetensors")
                )
                optimizer = torch.optim.AdamW(
                    adapter.parameters(), lr=self.m["learning_rate"], weight_decay=0
                )
                scores, updates = [], 0
                for epoch in (1, 2):
                    ident = f"train/{mode}/{seed}/{epoch}"
                    self.log.start(ident, dict(mode=mode, seed=seed, epoch=epoch))
                    order = list(range(len(examples)))
                    random.Random(seed * 10 + epoch).shuffle(order)
                    optimizer.zero_grad(set_to_none=True)
                    loss_sum, tick = 0.0, time.monotonic()
                    for step, index in enumerate(order):
                        self.deadline()
                        case_id, v = examples[index]
                        feedback = v["feedback"] if mode == "live" else [0.5, 0.5]
                        loss = self.runtime["loss_for"](
                            self.base.model,
                            adapter,
                            v["prompt_ids"],
                            v["target_ids"],
                            feedback,
                            layer=self.m["layer"],
                        )
                        if not torch.isfinite(loss):
                            raise ValueError("Nonfinite adapter loss")
                        (loss / self.m["accumulate"]).backward()
                        value = float(loss.detach())
                        loss_sum += value
                        if (step + 1) % self.m["accumulate"] == 0:
                            norm = torch.nn.utils.clip_grad_norm_(
                                adapter.parameters(), self.m["gradient_clip"]
                            )
                            if not torch.isfinite(norm):
                                raise ValueError("Nonfinite gradient")
                            optimizer.step()
                            optimizer.zero_grad(set_to_none=True)
                            updates += 1
                        J["append"](
                            self.output / "training-steps.jsonl",
                            dict(
                                mode=mode,
                                seed=seed,
                                epoch=epoch,
                                step=step,
                                example_index=index,
                                case_id=case_id,
                                kind=v["kind"],
                                loss=value,
                                updates=updates,
                                input_tokens=len(v["prompt_ids"]) + len(v["target_ids"]) - 1,
                                target_tokens=len(v["target_ids"]),
                                at=J["now"](),
                            ),
                        )
                        if (step + 1) % 128 == 0:
                            print(
                                json.dumps(
                                    dict(
                                        stage="training",
                                        mode=mode,
                                        seed=seed,
                                        epoch=epoch,
                                        examples=step + 1,
                                        mean_loss=loss_sum / (step + 1),
                                    )
                                ),
                                flush=True,
                            )
                    if any(
                        p.grad is not None or p.requires_grad for p in self.base.model.parameters()
                    ):
                        raise ValueError("Original weights acquired gradients")
                    checkpoint = self.output / f"{mode}-{seed}-epoch{epoch}.safetensors"
                    save_file(adapter.state_dict(), str(checkpoint))
                    answers = [
                        self.answer(
                            c,
                            mode,
                            seed,
                            adapter,
                            self.prepared[c["id"]]["feedback"]["granite_draft"]
                            if mode == "live"
                            else [0.5, 0.5],
                            part="development",
                            epoch=epoch,
                        )
                        for c in dev_cases
                    ]
                    score = sum(r["grade"]["correct"] for r in answers) / len(answers)
                    scores.append(score)
                    self.log.finish(
                        ident,
                        dict(
                            status="complete",
                            mode=mode,
                            seed=seed,
                            epoch=epoch,
                            examples=len(order),
                            updates=updates,
                            mean_loss=loss_sum / len(order),
                            development_accuracy=score,
                            seconds=time.monotonic() - tick,
                            checkpoint_sha256=S["sha"](checkpoint),
                        ),
                    )
                chosen = choose_epoch(scores)
                path = self.output / f"{mode}-{seed}-epoch{chosen}.safetensors"
                adapter.load_state_dict(load_file(str(path), device=str(self.base.device)))
                adapters[mode, seed] = adapter.eval()
                selected[f"{mode}/{seed}"] = dict(
                    epoch=chosen,
                    development_scores=scores,
                    checkpoint=path.name,
                    sha256=S["sha"](path),
                    updates=updates,
                )
        S["dump"](self.output / "selection.json", dict(at=J["now"](), models=selected))
        return adapters


async def execute(folder, output, device, key_file):
    import torch
    import transformers

    from jev_guided_decoding.backends.transformers import TransformersBackend

    m = verify(folder)
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    runtime = runpy.run_path(str(HERE / "runtime.py"))
    cohorts = {
        s: json.loads((folder / (s + ".json")).read_text())
        for s in ("train", "development", "test")
    }
    with (
        J["Journal"](output, m) as journal,
        InputTokenBudget(
            output / "jev-budget.jsonl",
            max_usd=m["max_api_usd"],
            usd_per_million=m["usd_per_million"],
        ) as budget,
    ):
        if journal.starts or budget.reserved:
            raise ValueError("Study cannot resume/replay attempted jobs")
        base = TransformersBackend.load(
            m["model"],
            revision=m["revision"],
            device=device,
            dtype=m["precision"],
            local_files_only=True,
        )
        before = S["weight_digest"](base.model)
        prompt = base.tokenizer.apply_chat_template(
            D["messages"](cohorts["train"][0]), tokenize=True, add_generation_prompt=True
        )
        admission = runtime["mechanical_admission"](base, prompt, layer=m["layer"])
        S["dump"](output / "mechanical-admission.json", admission)
        S["dump"](
            output / "hardware.json",
            dict(
                at=J["now"](),
                python=platform.python_version(),
                torch=torch.__version__,
                transformers=transformers.__version__,
                device=str(base.device),
                gpu=torch.cuda.get_device_name() if device == "cuda" else None,
                original_weights_sha256=before,
                original_parameters=sum(p.numel() for p in base.model.parameters()),
                adapter_parameters=sum(
                    p.numel()
                    for p in runtime["B"]["Bridge"](
                        base.model.config.hidden_size, m["rank"]
                    ).parameters()
                ),
                eos_ids=sorted(base.eos_ids),
            ),
        )
        async with LocalClaimScorer(
            load_api_key(key_file), budget=budget, model=m["jev"]
        ) as scorer:
            runner = Runner(folder, output, m, journal, base, runtime, scorer)
            for part in ("train", "development"):
                for i, c in enumerate(cohorts[part]):
                    await runner.prepare_case(c)
                    if (i + 1) % 32 == 0:
                        print(
                            json.dumps(dict(stage="prepare", part=part, complete=i + 1)), flush=True
                        )
            adapters = runner.train(cohorts["train"], cohorts["development"])
            # Freeze/checkpoint selection is durable before any test draft or feedback.
            for i, c in enumerate(cohorts["test"]):
                await runner.prepare_case(c)
                if (i + 1) % 32 == 0:
                    print(
                        json.dumps(dict(stage="prepare", part="test", complete=i + 1)), flush=True
                    )
            donors = json.loads((folder / "donors.json").read_text())
            rows = []
            for i, c in enumerate(cohorts["test"]):
                arms = list(ARMS)
                random.Random("r22-arm-order/" + c["id"]).shuffle(arms)
                item = runner.prepared[c["id"]]
                for mode, seed in arms:
                    adapter = (
                        None
                        if mode == "native"
                        else adapters["constant" if mode == "constant" else "live", seed]
                    )
                    feedback = item["feedback"]["granite_draft"]
                    if mode in ("native", "constant"):
                        feedback = [0.5, 0.5]
                    elif mode == "permuted":
                        feedback = runner.prepared[donors[c["id"]]]["feedback"]["granite_draft"]
                    elif mode == "oracle":
                        oracle = item["draft_oracle"]
                        feedback = [float(oracle["supported"]), 1.0] if oracle else [0.0, 0.0]
                    rows.append(runner.answer(c, mode, seed, adapter, feedback, part="test"))
                if (i + 1) % 24 == 0:
                    print(
                        json.dumps(dict(stage="test", worlds=i + 1, outputs=len(rows))), flush=True
                    )
            after = S["weight_digest"](base.model)
            if before != after:
                raise ValueError("Original model weights changed")
            S["dump"](
                output / "completion.json",
                dict(
                    at=J["now"](),
                    unchanged_weights=True,
                    before_sha256=before,
                    after_sha256=after,
                    elapsed_seconds=time.monotonic() - runner.started,
                    successful_calls=len(budget.settled),
                    unknown_calls=len(budget.unresolved),
                    input_tokens=budget.charged_tokens,
                    jev_estimate_usd=budget.charged_tokens * m["usd_per_million"] / 1e6,
                    test_outputs=len(rows),
                    peak_cuda_bytes=torch.cuda.max_memory_allocated() if device == "cuda" else None,
                ),
            )
            S["dump"](output / "analysis.json", analyze(cohorts["test"], rows))
            print(json.dumps(dict(stage="complete", test_outputs=len(rows))), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=("prepare", "run"))
    p.add_argument("--freeze", type=Path, required=True)
    p.add_argument("--output", type=Path)
    p.add_argument("--admission", type=Path)
    p.add_argument("--device", choices=("cuda", "mps", "cpu"), default="cuda")
    p.add_argument("--key-file", type=Path)
    a = p.parse_args()
    if a.command == "prepare":
        if a.admission is None:
            p.error("--admission required")
        print(json.dumps(prepare(a.freeze, a.admission), indent=2))
    elif a.output is None:
        p.error("--output required")
    else:
        asyncio.run(execute(a.freeze, a.output, a.device, a.key_file))


if __name__ == "__main__":
    main()
