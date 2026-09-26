"""R18 prospective data freeze and serial single-prefill boundary study."""

import argparse
import asyncio
import hashlib
import json
import platform
import random
import runpy
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
D = runpy.run_path(str(HERE / "data.py"))
P = runpy.run_path(str(HERE / "policies.py"))
OLD = runpy.run_path(str(HERE.parent / "selective_attention/study.py"))
J, MODEL, REVISION = OLD["J"], OLD["MODEL"], OLD["REVISION"]
ARMS = (
    "native",
    "always",
    "boundary_never",
    "boundary_always",
    "boundary_gate",
    "boundary_random",
    "pilot_gate",
    "lexical",
    "shuffled",
)


def treatment():
    return next(
        p
        for p in OLD["P"]["grid"]()
        if p["mode"] == "additive" and p["envelope"] == "all" and p["strength"] == 5
    )


def source_hashes():
    values = OLD["source_hashes"]()
    for p in [*HERE.glob("*.py"), ROOT / "research/boundary-attention-plan.md"]:
        values[str(p.relative_to(ROOT))] = D["sha"](p)
    return dict(sorted(values.items()))


def schedule(cases):
    ordered = list(cases)
    random.Random(180922733).shuffle(ordered)
    jobs = []
    for c in ordered:
        others = [a for a in ARMS if a != "boundary_gate"]
        random.Random("r18-order/" + c["id"]).shuffle(others)
        jobs.extend(dict(case_id=c["id"], arm=a) for a in ["boundary_gate", *others])
    return jobs


def prepare(folder, hotpot, squad):
    from transformers import AutoTokenizer, GenerationConfig

    R = runpy.run_path(str(HERE / "runtime.py"))
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL, revision=REVISION, local_files_only=True, trust_remote_code=False
    )
    generation = GenerationConfig.from_pretrained(MODEL, revision=REVISION, local_files_only=True)
    eos = generation.eos_token_id if generation.eos_token_id is not None else tokenizer.eos_token_id
    eos_ids = sorted(set(eos if isinstance(eos, list) else [eos]) - {None})
    if folder.exists():
        raise FileExistsError("Use a new frozen protocol directory")
    eligibility = []

    def eligible(c):
        try:
            length = len(R["encode"](tokenizer, D["public_view"](c))["input_ids"])
        except ValueError as exc:
            if str(exc) != "Input context limit":
                raise
            length = 3073
        yes = 1 <= len(c["sources"]) <= 32 and length <= 3072
        eligibility.append(
            dict(id=c["id"], eligible=yes, prompt_tokens=length, source_count=len(c["sources"]))
        )
        return yes

    excluded = set()
    for old in ("adaptive-attention-fp32", "selective-attention-v1"):
        for p in (ROOT / "research/protocols" / old).glob("*.json"):
            value = json.loads(p.read_text())
            if isinstance(value, list):
                excluded.update(
                    c["upstream_id"] for c in value if isinstance(c, dict) and "upstream_id" in c
                )
    raw = sorted(json.loads(hotpot.read_text()), key=lambda c: c["id"])
    random.Random(180922739).shuffle(raw)
    chosen = []
    for row in raw:
        if row["id"] in excluded:
            continue
        sources = [
            {"id": f"D{i + 1:02}", "text": title + ": " + "".join(sentences)}
            for i, (title, sentences) in enumerate(
                zip(row["context"]["title"], row["context"]["sentences"], strict=True)
            )
        ]
        if len(sources) != 10:
            continue
        ident = "r18/hotpot/" + row["id"]
        c = dict(
            id=ident,
            world_id=ident,
            upstream_id=row["id"],
            family="hotpot",
            question=row["question"],
            sources=sources,
            reference=row["answer"],
            references=[row["answer"]],
            missing=False,
            condition="distractor",
            question_type=row["type"],
        )
        if eligible(c):
            chosen.append(c)
        if len(chosen) == 315:
            break
    if len(chosen) != 315:
        raise ValueError("Insufficient fresh Hotpot questions")
    admission, development, test = (
        chosen[:3],
        D["synthetic"]("development", 108) + chosen[3:75],
        D["synthetic"]("test", 252) + chosen[75:],
    )
    articles = sorted(json.loads(squad.read_text())["data"], key=lambda a: a["title"])
    random.Random(180922743).shuffle(articles)
    partitions = [
        ("development", articles[:10], (40, 40)),
        ("admission", articles[10:12], (2, 1)),
        ("test", articles[12:], (120, 120)),
    ]
    article_split = {a["title"]: split for split, group, _ in partitions for a in group}
    for split, group, desired in partitions:
        pool = []
        for article in group:
            for index, paragraph in enumerate(article["paragraphs"]):
                for q in paragraph["qas"]:
                    ident = "r18/squad2/" + q["id"]
                    refs = sorted(set(a["text"] for a in q["answers"]))
                    pool.append(
                        dict(
                            id=ident,
                            world_id=ident,
                            cluster_id=article["title"],
                            upstream_id=q["id"],
                            paragraph_id=f"{article['title']}/{index}",
                            family="squad2",
                            article=article["title"],
                            question=q["question"],
                            sources=D["sentence_sources"](paragraph["context"]),
                            original_context_sha256=hashlib.sha256(
                                paragraph["context"].encode()
                            ).hexdigest(),
                            reference=refs[0] if refs else "",
                            references=refs,
                            missing=q["is_impossible"],
                            condition="original_passage",
                            split=split,
                        )
                    )
        random.Random("r18-squad/" + split).shuffle(pool)
        found, seen, counts = [], set(), [0, 0]
        for c in pool:
            cls = int(c["missing"])
            if counts[cls] >= desired[cls] or c["paragraph_id"] in seen:
                continue
            if eligible(c):
                found.append(c)
                seen.add(c["paragraph_id"])
                counts[cls] += 1
            if tuple(counts) == desired:
                break
        if tuple(counts) != desired:
            raise ValueError(f"Insufficient SQuAD paragraphs in {split}: {counts}")
        {"development": development, "admission": admission, "test": test}[split].extend(found)
    for split, cases in [("development", development), ("admission", admission), ("test", test)]:
        for c in cases:
            c["split"] = split
    if (len(development), len(test), len(admission)) != (260, 984, 6):
        raise ValueError("Cohort counts differ from plan")
    payloads = [
        json.dumps(OLD["S"]["payload_for"](D["public_view"](c), "jev-1.13.0"), sort_keys=True)
        for c in development + test
    ]
    if len(set(payloads)) != len(payloads):
        raise ValueError("Repeated exact scorer input")
    folder.mkdir(parents=True)
    for name, value in [
        ("development", development),
        ("test", test),
        ("admission", admission),
        ("eligibility", eligibility),
        ("squad-article-split", article_split),
        ("schedule", schedule(test)),
    ]:
        D["dump"](folder / f"{name}.json", value)
    D["dump"](
        folder / "manifest.json",
        dict(
            protocol="r18-boundary-attention-v1",
            at=J["now"](),
            model=MODEL,
            revision=REVISION,
            jev_model="jev-1.13.0",
            precision="float32",
            boundary=19,
            num_layers=40,
            eos_ids=eos_ids,
            generation_mode="greedy_full_vocabulary",
            treatment=treatment(),
            max_seconds=6 * 3600,
            max_api_usd=2,
            source_hotpot_sha256=D["sha"](hotpot),
            source_squad_sha256=D["sha"](squad),
            sources=source_hashes(),
            datasets={p.name: D["sha"](p) for p in sorted(folder.glob("*.json"))},
            prior_spend_usd=23.456365263925505,
            cloud_allowance_usd=13,
            cumulative_budget_usd=50,
            gate_development_ceiling=0.5,
            primary_interval=1 - 0.05 / 3,
        ),
    )
    print(
        json.dumps(
            dict(
                development=len(development),
                test=len(test),
                test_jobs=len(schedule(test)),
                admission=len(admission),
            )
        )
    )


class Profile:
    def __init__(self, base):
        self.base, self.events = base, []
        self.layer_calls = [0] * len(base.model.model.layers)
        self.layer_tokens = [0] * len(self.layer_calls)
        self.handles, self.pending = [], None

    def __enter__(self):
        import torch

        self.started = time.monotonic()
        self.peak = None
        if self.base.device.type == "cuda":
            torch.cuda.reset_peak_memory_stats(self.base.device)

        def begin(module, args, kwargs):
            ids = kwargs.get("input_ids", args[0] if args else None)
            self.pending = ids.shape[-1]

        def finish(module, args, output):
            self.base._sync()
            self.events.append(
                dict(seconds=time.monotonic() - self.started, query_tokens=self.pending)
            )

        def layer(index):
            def record(module, args):
                self.layer_calls[index] += 1
                self.layer_tokens[index] += args[0].shape[1]

            return record

        self.handles.append(self.base.model.register_forward_pre_hook(begin, with_kwargs=True))
        self.handles.append(self.base.model.register_forward_hook(finish))
        for i, item in enumerate(self.base.model.model.layers):
            self.handles.append(item.register_forward_pre_hook(layer(i)))
        return self

    def __exit__(self, *args):
        import torch

        for handle in self.handles:
            handle.remove()
        if self.base.device.type == "cuda":
            self.peak = torch.cuda.max_memory_allocated(self.base.device)


class ReceiptStore(OLD["S"]["ReceiptStore"]):
    def charge_unknown(self, reservation):
        self.budget.acknowledge_max_charge(
            reservation,
            reason="Failed R18 attempt; never replay this payload",
            authorization="User authorized bounded R18 study; prospective failure policy",
        )


class Runner:
    def __init__(self, base, log, receipts, manifest):
        self.base, self.log, self.receipts, self.manifest = base, log, receipts, manifest
        self.R = runpy.run_path(str(HERE / "runtime.py"))
        self.previous = self.R["OLD"]["Runtime"](base)
        self.current = self.R["Runtime"](base)
        self.started, self.inputs = time.monotonic(), {}
        self.incidents = self.consecutive = 0
        self.abort_reason = None
        self.cooldown = 0

    def deadline(self):
        if time.monotonic() - self.started > self.manifest["max_seconds"]:
            raise TimeoutError("Study deadline")
        if self.abort_reason or self.incidents >= 20 or self.consecutive >= 3:
            raise RuntimeError(self.abort_reason or "Provider incident stop")

    async def receipt(self, view):
        self.deadline()
        before = len(self.receipts.receipts)
        response = await self.receipts.get(view)
        if self.receipts.new_failure:
            self.incidents += 1
            self.consecutive += 1
            code = response.get("diagnostics", {}).get("status_code")
            if code not in (429, 502, 503, 504, 529) and not (
                code is None
                and (
                    "tim" in response["reason"].lower()
                    or "request failed" in response["reason"].lower()
                )
            ):
                self.abort_reason = (
                    "Non-transient provider error; native fallback retained then stop"
                )
            else:
                self.cooldown = max(
                    60, float(response.get("diagnostics", {}).get("retry_after_seconds") or 0)
                )
        elif len(self.receipts.receipts) > before:
            self.consecutive = 0
        return response

    def encoded(self, c):
        if c["id"] not in self.inputs:
            value = {"id": c["id"], **self.R["encode"](self.base.tokenizer, D["public_view"](c))}
            self.inputs[c["id"]] = value
            J["append"](self.log.folder / "inputs.jsonl", value)
        return self.inputs[c["id"]]

    async def job(self, c, arm, gate=None, *, stage):
        self.deadline()
        while self.cooldown > 0:
            delay = min(30, self.cooldown)
            await asyncio.sleep(delay)
            self.cooldown -= delay
            self.deadline()
        ident = f"{stage}/{c['id']}/{arm}"
        policy = None if arm == "native" else treatment()
        metadata = dict(
            case_id=c["id"],
            world_id=c["world_id"],
            domain=D["domain"](c),
            family=c["family"],
            stage=stage,
            arm=arm,
            policy=policy,
            requested_gate=gate,
        )
        if not self.log.start(ident, metadata):
            return self.log.outputs[ident]
        before = len(self.receipts.receipts)
        try:
            encoded = self.encoded(c)
            with Profile(self.base) as profile:
                if arm.startswith("boundary_"):
                    row = await self.R["generate"](
                        self.current,
                        encoded,
                        D["public_view"](c),
                        policy,
                        self.receipt,
                        gate=gate,
                    )
                else:
                    row = await self.R["OLD"]["generate"](
                        self.previous,
                        encoded,
                        D["public_view"](c),
                        policy,
                        self.receipt,
                        gate=gate,
                        score_mode=arm if arm in ("lexical", "shuffled") else "jev",
                    )
            physical = len(self.receipts.receipts) - before
            receipt = self.receipts.receipts.get(row["receipt_key"], {})
            discarded = (
                len(row["pilot"]["tokens"]) if row["pilot"] and not row["pilot_reused"] else 0
            )
            ttf = profile.events[discarded]["seconds"]
            estimated_extra = (
                receipt.get("seconds", 0) if row["logical_jev_calls"] and not physical else 0
            )
            row.update(
                metadata,
                physical_jev_attempts=physical,
                receipt_seconds=receipt.get("seconds", 0),
                estimated_uncached_wall_seconds=row["wall_seconds"] + estimated_extra,
                first_token_seconds=ttf,
                estimated_uncached_first_token_seconds=ttf + estimated_extra,
                layer_calls=profile.layer_calls,
                layer_token_counts=profile.layer_tokens,
                forward_events=profile.events,
                prefills=sum(
                    e["query_tokens"] == len(self.inputs[c["id"]]["input_ids"])
                    for e in profile.events
                ),
                discarded_tokens=discarded,
                peak_gpu_bytes=profile.peak,
                grade=D["grade"](c, row["text"]),
            )
            if row["model_forwards"] != len(profile.events):
                raise ValueError("Measured forward count mismatch")
            self.log.finish(ident, row)
        except BaseException as exc:
            self.log.finish(
                ident,
                {
                    **metadata,
                    "status": "error",
                    "error_type": type(exc).__name__,
                    "text": "",
                    "work_unknown": True,
                    "physical_jev_attempts": len(self.receipts.receipts) - before,
                },
            )
            raise
        return self.log.outputs[ident]

    async def develop(self, cases):
        path = self.log.folder / "selected.json"
        if path.exists():
            return json.loads(path.read_text())
        fitted = []
        for i, c in enumerate(cases):
            order = [("boundary_never", {"kind": "never"}), ("boundary_always", {"kind": "always"})]
            random.Random("r18-dev/" + c["id"]).shuffle(order)
            outputs = {
                arm: await self.job(c, arm, gate, stage="development") for arm, gate in order
            }
            native, guided = outputs["boundary_never"], outputs["boundary_always"]
            if native["features"] != guided["features"]:
                raise ValueError("Treatment contaminated native gate features")
            tokens = native["final"]["tokens"][:8]
            text = self.base.tokenizer.decode(
                [t["token_id"] for t in tokens],
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False,
            )
            fitted.append(
                dict(
                    case_id=c["id"],
                    domain=D["domain"](c),
                    features=native["features"],
                    pilot_features=OLD["P"]["features"](tokens, text, D["public_view"](c)),
                    native_quality=D["quality"](c, native["grade"]),
                    guided_quality=D["quality"](c, guided["grade"]),
                )
            )
            print(
                json.dumps(
                    dict(development_cases=i + 1, planned=len(cases), incidents=self.incidents)
                ),
                flush=True,
            )
        selected = dict(
            at=J["now"](),
            treatment=treatment(),
            boundary=P["fit"](fitted),
            pilot=P["fit"](
                [{**r, "features": r["pilot_features"]} for r in fitted], names=P["PILOT_FEATURES"]
            ),
            development=fitted,
            development_sha256=self.manifest["datasets"]["development.json"],
        )
        D["dump"](path, selected)
        return selected


def gate_for(arm, selected):
    if arm in ("boundary_never", "boundary_always"):
        return {"kind": "never" if arm == "boundary_never" else "always"}
    if arm == "boundary_gate":
        return selected["boundary"]["gate"]
    if arm == "boundary_random":
        return {"kind": "random", "fraction": selected["boundary"]["call_fraction"]}
    if arm == "pilot_gate":
        return selected["pilot"]["gate"]
    return None


async def run(args):
    from jev_guided_decoding.backends.transformers import TransformersBackend
    from jev_guided_decoding.experiment_budget import InputTokenBudget

    A = runpy.run_path(str(HERE / "admission.py"))
    manifest = json.loads((args.manifest / "manifest.json").read_text())
    if manifest["sources"] != source_hashes() or any(
        D["sha"](args.manifest / name) != digest for name, digest in manifest["datasets"].items()
    ):
        raise ValueError("Source/data freeze mismatch")
    data = {
        name: json.loads((args.manifest / f"{name}.json").read_text())
        for name in ("development", "test", "admission", "schedule")
    }
    if schedule(data["test"]) != data["schedule"]:
        raise ValueError("Schedule mismatch")
    with J["Journal"](args.output, manifest) as log:
        base = TransformersBackend.load(
            MODEL,
            revision=REVISION,
            device=args.device,
            dtype="float32",
            local_files_only=args.local_files_only,
        )
        if (
            sorted(base.eos_ids) != manifest["eos_ids"]
            or len(base.model.model.layers) != manifest["num_layers"]
        ):
            raise ValueError("Checkpoint EOS/layer configuration mismatch")
        before = OLD["PRIOR"]["weight_hash"](base)
        J["append"](
            args.output / "loads.jsonl",
            dict(
                at=J["now"](),
                weights_before=before,
                python=platform.python_version(),
                backend=base.metadata(),
                revision=subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
                ).strip(),
                dirty=subprocess.check_output(
                    ["git", "status", "--porcelain"], cwd=ROOT, text=True
                ),
            ),
        )
        if not (args.output / "admission.json").exists():
            await A["admission"](
                base, data["development"][:3] + data["admission"], args.output, treatment()
            )
        if args.admission_only:
            print("ADMISSION PASSED", flush=True)
            return
        key = args.key_file.expanduser().read_text().strip()
        with InputTokenBudget(
            args.output / "ledger.jsonl", max_usd=manifest["max_api_usd"], usd_per_million=0.05
        ) as budget:
            async with OLD["S"]["StudyClient"](
                key, model=manifest["jev_model"], request_timeout=90, max_retries=0
            ) as client:
                store = ReceiptStore(args.output / "receipts.jsonl", client, budget)
                runner = Runner(base, log, store, manifest)
                selected = await runner.develop(data["development"])
                freeze = dict(
                    at=J["now"](),
                    selected_sha256=D["sha"](args.output / "selected.json"),
                    schedule_sha256=manifest["datasets"]["schedule.json"],
                    sources=manifest["sources"],
                )
                path = args.output / "test-freeze.json"
                if path.exists():
                    old = json.loads(path.read_text())
                    if any(old[k] != v for k, v in freeze.items() if k != "at"):
                        raise ValueError("Test freeze mismatch")
                else:
                    D["dump"](path, freeze)
                cases = {c["id"]: c for c in data["test"]}
                for i, job in enumerate(data["schedule"]):
                    await runner.job(
                        cases[job["case_id"]],
                        job["arm"],
                        gate_for(job["arm"], selected),
                        stage="test",
                    )
                    if i % 36 == 0:
                        print(
                            json.dumps(
                                dict(
                                    test_done=i + 1,
                                    planned=len(data["schedule"]),
                                    receipts=len(store.receipts),
                                    incidents=runner.incidents,
                                    charged_tokens=budget.charged_tokens,
                                )
                            ),
                            flush=True,
                        )
                after = OLD["PRIOR"]["weight_hash"](base)
                if after != before:
                    raise ValueError("Weights changed")
                D["dump"](
                    args.output / "completion.json",
                    dict(
                        at=J["now"](),
                        outputs=len(log.outputs),
                        receipts=len(store.receipts),
                        charged_tokens=budget.charged_tokens,
                        weights_before=before,
                        weights_after=after,
                        completed_schedule=True,
                        test_jobs=len(data["schedule"]),
                    ),
                )
                print("STUDY COMPLETE", flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("command", choices=["prepare", "run"])
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--hotpot", type=Path)
    p.add_argument("--squad", type=Path)
    p.add_argument("--output", type=Path)
    p.add_argument("--key-file", type=Path, default=Path("~/.typesafe.ai/jev"))
    p.add_argument("--device", default="cuda")
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--admission-only", action="store_true")
    args = p.parse_args()
    if args.command == "prepare":
        prepare(args.manifest, args.hotpot, args.squad)
    else:
        asyncio.run(run(args))


if __name__ == "__main__":
    main()
