"""Prospectively frozen R17 development, selective assistance and held-out controls."""

import argparse
import asyncio
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
S = runpy.run_path(str(HERE / "scorer.py"))
J = runpy.run_path(str(HERE.parent / "adaptive_attention/journal.py"))
PRIOR = runpy.run_path(str(HERE.parent / "adaptive_attention_fp32.py"))
MODEL, REVISION = PRIOR["MODEL"], PRIOR["REVISION"]
ARMS = (
    "native",
    "r16",
    "mass_all",
    "always",
    "uncertainty_gate",
    "benefit_gate",
    "random_gate",
    "lexical",
    "shuffled",
)


def source_hashes():
    paths = list(HERE.glob("*.py")) + list((HERE.parent / "adaptive_attention").glob("*.py"))
    paths += [
        HERE.parent / "adaptive_attention_fp32.py",
        ROOT / "research/selective-attention-plan.md",
    ]
    paths += [
        ROOT / f"research/experiments/evidence_{s}.py" for s in ("attention", "runtime", "scorer")
    ]
    paths += list((ROOT / "src/jev_guided_decoding").rglob("*.py")) + [ROOT / "uv.lock"]
    return {str(p.relative_to(ROOT)): D["sha"](p) for p in sorted(paths)}


def schedule(cases):
    jobs = []
    ordered = list(cases)
    random.Random(570922331).shuffle(ordered)
    for c in ordered:
        others = [a for a in ARMS if a != "benefit_gate"]
        random.Random("r17-order/" + c["id"]).shuffle(others)
        jobs.extend(dict(case_id=c["id"], arm=a) for a in ["benefit_gate", *others])
    return jobs


def prepare(folder, hotpot):
    from transformers import AutoTokenizer

    R = runpy.run_path(str(HERE / "runtime.py"))
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL, revision=REVISION, local_files_only=True, trust_remote_code=False
    )
    folder.mkdir(parents=True, exist_ok=False)
    excluded = set()
    for name in ("hotpot", "admission"):
        path = ROOT / f"research/protocols/adaptive-attention-fp32/{name}.json"
        excluded.update(c["upstream_id"] for c in json.loads(path.read_text()))
    raw = sorted(json.loads(hotpot.read_text()), key=lambda c: c["id"])
    random.Random(470922329).shuffle(raw)
    chosen, eligibility = [], []
    for row in raw:
        if row["id"] in excluded:
            eligibility.append(dict(id=row["id"], eligible=False, reason="used in R16"))
            continue
        sources = [
            {"id": f"D{i + 1:02}", "text": title + ": " + "".join(sentences)}
            for i, (title, sentences) in enumerate(
                zip(row["context"]["title"], row["context"]["sentences"], strict=True)
            )
        ]
        c = dict(
            id="r17/hotpot/" + row["id"],
            world_id="r17/hotpot/" + row["id"],
            upstream_id=row["id"],
            family="hotpot",
            question=row["question"],
            sources=sources,
            reference=row["answer"],
            depth=2,
            missing=False,
            condition="distractor",
            question_type=row["type"],
        )
        try:
            length = len(R["encode"](tokenizer, D["public_view"](c))["input_ids"])
        except ValueError as exc:
            if str(exc) != "Input context limit":
                raise
            length = 3073
        eligible = len(sources) == 10 and length <= 3072
        eligibility.append(
            dict(
                id=row["id"],
                eligible=eligible,
                prompt_tokens=length,
                reason="length/source-count only",
            )
        )
        if eligible:
            chosen.append(c)
        if len(chosen) == 254:
            break
    if len(chosen) != 254:
        raise ValueError("Insufficient fresh external questions")
    admission, dev_ext, test_ext = chosen[:6], chosen[6:54], chosen[54:]
    for split, group in (("admission", admission), ("development", dev_ext), ("test", test_ext)):
        for c in group:
            c["split"] = split
    dev, test = D["synthetic"]("development", 108) + dev_ext, D["synthetic"]("test", 252) + test_ext
    payload_keys = [
        json.dumps(S["payload_for"](D["public_view"](c), "jev-1.13.0"), sort_keys=True)
        for c in dev + test
    ]
    if len(set(payload_keys)) != len(payload_keys):
        raise ValueError("Duplicate semantic scorer inputs across fresh cohort")
    for c in dev + test:
        R["encode"](tokenizer, D["public_view"](c))
    for name, value in (
        ("development", dev),
        ("test", test),
        ("admission", admission),
        ("eligibility", eligibility),
        ("schedule", schedule(test)),
    ):
        D["dump"](folder / f"{name}.json", value)
    D["dump"](
        folder / "manifest.json",
        dict(
            protocol="r17-selective-attention-v1",
            at=J["now"](),
            model=MODEL,
            revision=REVISION,
            jev_model="jev-1.13.0",
            precision="float32",
            max_seconds=7 * 3600,
            max_api_usd=3,
            source_hotpot_sha256=D["sha"](hotpot),
            policy_grid=P["grid"](),
            sources=source_hashes(),
            datasets={p.name: D["sha"](p) for p in sorted(folder.glob("*.json"))},
            primary_intervals=0.9875,
            gate_noninferiority_margin=0.03,
            prior_spend_usd=19.688713942733276,
            cloud_allowance_usd=15,
            cumulative_budget_usd=50,
        ),
    )
    print(
        json.dumps(
            dict(development_cases=len(dev), test_cases=len(test), test_jobs=len(schedule(test)))
        )
    )


class Runner:
    def __init__(self, runtime, log, receipts, manifest):
        self.runtime, self.log, self.receipts, self.manifest = runtime, log, receipts, manifest
        self.R = runpy.run_path(str(HERE / "runtime.py"))
        self.start, self.incidents, self.consecutive = time.monotonic(), 0, 0
        self.inputs, self.abort_reason = {}, None

    def deadline(self):
        if time.monotonic() - self.start > self.manifest["max_seconds"]:
            raise TimeoutError("Study deadline")
        if self.abort_reason or self.incidents >= 20 or self.consecutive >= 3:
            raise RuntimeError(self.abort_reason or "Provider incident stop")

    def encoded(self, c):
        if c["id"] not in self.inputs:
            value = {
                "id": c["id"],
                **self.R["encode"](self.runtime.base.tokenizer, D["public_view"](c)),
            }
            self.inputs[c["id"]] = value
            J["append"](self.log.folder / "inputs.jsonl", value)
        return self.inputs[c["id"]]

    async def receipt(self, view):
        self.deadline()
        count = len(self.receipts.receipts)
        r = await self.receipts.get(view)
        if self.receipts.new_failure:
            self.incidents += 1
            self.consecutive += 1
            code = r.get("diagnostics", {}).get("status_code")
            if code not in (429, 502, 503, 504, 529) and not (
                code is None
                and ("tim" in r["reason"].lower() or "request failed" in r["reason"].lower())
            ):
                self.abort_reason = "Non-transient provider error; fallback retained then stop"
            else:
                delay = max(60, float(r.get("diagnostics", {}).get("retry_after_seconds") or 0))
                J["append"](
                    self.log.folder / "events.jsonl",
                    dict(at=J["now"](), event="cooldown", seconds=delay, key=r["key"]),
                )
                while delay > 0:
                    if time.monotonic() - self.start > self.manifest["max_seconds"]:
                        break
                    await asyncio.sleep(min(30, delay))
                    delay -= 30
        elif len(self.receipts.receipts) > count:
            self.consecutive = 0
        return r

    async def job(self, c, arm, policy, *, stage, gate=None):
        self.deadline()
        ident = f"{stage}/{c['id']}/{arm}"
        metadata = dict(
            case_id=c["id"],
            world_id=c["world_id"],
            family=c["family"],
            domain=D["domain"](c),
            arm=arm,
            stage=stage,
            policy=policy,
            requested_gate=gate,
        )
        if not self.log.start(ident, metadata):
            return self.log.outputs[ident]
        before = len(self.receipts.receipts)
        try:
            row = await self.R["generate"](
                self.runtime,
                self.encoded(c),
                D["public_view"](c),
                policy,
                self.receipt,
                gate=gate,
                score_mode=arm if arm in ("lexical", "shuffled") else "jev",
            )
            physical = len(self.receipts.receipts) - before
            receipt = self.receipts.receipts.get(row["receipt_key"], {})
            row.update(
                metadata,
                physical_jev_attempts=physical,
                receipt_seconds=receipt.get("seconds", 0),
                estimated_uncached_wall_seconds=row["wall_seconds"]
                + (receipt.get("seconds", 0) if not physical else 0),
                grade=D["grade"](c, row["text"], "open_explicit"),
            )
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
        grid = P["grid"]()
        outputs = {}
        for index, c in enumerate(cases):
            order = [None, *grid]
            random.Random("r17-dev/" + c["id"]).shuffle(order)
            for policy in order:
                arm = policy["id"] if policy else "native"
                outputs[c["id"], arm] = await self.job(c, arm, policy, stage="development")
            print(
                json.dumps(
                    dict(development_cases=index + 1, planned=len(cases), incidents=self.incidents)
                ),
                flush=True,
            )
        metrics = []
        for p in grid:
            rows = [
                {
                    "family": D["domain"](c),
                    "quality": D["quality"](c, outputs[c["id"], p["id"]]["grade"]),
                }
                for c in cases
            ]
            metrics.append(dict(policy=p, quality=P["balanced"](rows, "quality")))
        selected = P["choose_policy"](metrics)
        gate_rows = []
        for c in cases:
            native, guided = outputs[c["id"], "native"], outputs[c["id"], selected["policy"]["id"]]
            tokens = native["final"]["tokens"][:8]
            text = self.runtime.base.tokenizer.decode(
                [t["token_id"] for t in tokens],
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False,
            )
            gate_rows.append(
                dict(
                    case_id=c["id"],
                    family=D["domain"](c),
                    features=P["features"](tokens, text, D["public_view"](c)),
                    native_quality=D["quality"](c, native["grade"]),
                    guided_quality=D["quality"](c, guided["grade"]),
                )
            )
        value = dict(
            at=J["now"](),
            selected=selected,
            all_policies=metrics,
            gates=P["fit_gates"](gate_rows),
            gate_development=gate_rows,
            development_sha256=self.manifest["datasets"]["development.json"],
        )
        D["dump"](path, value)
        return value


def arm_config(arm, selected):
    policy, gate = selected["selected"]["policy"], None
    if arm == "native":
        policy = None
    elif arm in ("r16", "mass_all"):
        policy = next(
            p
            for p in P["grid"]()
            if p["strength"] == 5
            and p["envelope"] == "all"
            and p["mode"] == ("additive" if arm == "r16" else "conserve")
        )
    elif arm in ("benefit_gate", "uncertainty_gate"):
        gate = selected["gates"][arm.removesuffix("_gate")]["gate"]
    elif arm == "random_gate":
        gate = {"kind": "random", "fraction": selected["gates"]["benefit"]["call_fraction"]}
    return policy, gate


def admission(runtime, cases, output):
    import torch

    R = runpy.run_path(str(HERE / "runtime.py"))
    old_runtime = R["OLD"]["Runtime"](runtime.base)
    checks = []
    for c in cases:
        enc = R["encode"](runtime.base.tokenizer, D["public_view"](c))
        first, second = runtime.session(enc), runtime.session(enc)
        first.extend(4)
        second.extend(2)
        second.extend(2)
        if first.result()["token_ids"] != second.result()["token_ids"]:
            raise ValueError("Split native identity failed")
        old = old_runtime.session(enc)
        old.generate(4, "final", maps={}) if len(enc["input_ids"]) < 2300 else None
        if old.phases and old.phases[0]["token_ids"] != first.result()["token_ids"]:
            raise ValueError("Prior native equivalence failed")
        scores = [float(i % 2 == 0) for i in range(len(c["sources"]))]
        per_mode = []
        for mode in ("additive", "conserve"):
            p = next(
                p
                for p in P["grid"]()
                if p["mode"] == mode and p["envelope"] == "all" and p["strength"] == 5
            )
            session = runtime.session(enc)
            session.extend(2, p, scores)
            prior = R["OLD"]["P"]["identified"](
                dict(
                    heads=p["heads"],
                    weights=[5] * len(p["heads"]),
                    mapping="threshold",
                    threshold=0.65,
                )
            )
            maps = R["OLD"]["P"]["token_maps"](prior, enc["span_token_indices"], scores)
            ids, past = session.ids, session.processed
            with (
                torch.inference_mode(),
                runtime.hook.apply(
                    ids[past:],
                    query_start=enc["query_start"],
                    source_keys=session.source_keys,
                    maps=maps,
                    mode=mode,
                    past_length=past,
                ),
            ):
                cached = (
                    runtime.base.model(
                        input_ids=torch.tensor([ids[past:]], device=runtime.base.device),
                        attention_mask=torch.ones(
                            (1, len(ids)), device=runtime.base.device, dtype=torch.long
                        ),
                        past_key_values=session.cache,
                        use_cache=True,
                        cache_position=torch.arange(past, len(ids), device=runtime.base.device),
                        logits_to_keep=1,
                    )
                    .logits[0, -1]
                    .float()
                )
            with (
                torch.inference_mode(),
                runtime.hook.apply(
                    ids,
                    query_start=enc["query_start"],
                    source_keys=session.source_keys,
                    maps=maps,
                    mode=mode,
                ),
            ):
                full = (
                    runtime.base.model(
                        input_ids=torch.tensor([ids], device=runtime.base.device),
                        attention_mask=torch.ones(
                            (1, len(ids)), device=runtime.base.device, dtype=torch.long
                        ),
                        use_cache=False,
                        logits_to_keep=1,
                    )
                    .logits[0, -1]
                    .float()
                )
            delta = float((full - cached).abs().max())
            if delta > 0.0001 or int(full.argmax()) != int(cached.argmax()):
                raise ValueError(f"Cache/full admission failed {mode}: {delta}")
            per_mode.append(dict(mode=mode, cache_full_max_difference=delta, same_argmax=True))
        checks.append(
            dict(
                case_id=c["id"],
                prompt_tokens=len(enc["input_ids"]),
                native_token_ids=first.result()["token_ids"],
                modes=per_mode,
            )
        )
    D["dump"](output / "admission.json", dict(at=J["now"](), checks=checks, passed=True))


async def run(args):
    from jev_guided_decoding.backends.transformers import TransformersBackend
    from jev_guided_decoding.experiment_budget import InputTokenBudget

    R = runpy.run_path(str(HERE / "runtime.py"))
    manifest = json.loads((args.manifest / "manifest.json").read_text())
    if manifest["sources"] != source_hashes():
        raise ValueError("Source freeze mismatch")
    if any(
        D["sha"](args.manifest / name) != digest for name, digest in manifest["datasets"].items()
    ):
        raise ValueError("Dataset freeze mismatch")
    data = {
        n: json.loads((args.manifest / f"{n}.json").read_text())
        for n in ("development", "test", "admission", "schedule")
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
        runtime = R["Runtime"](base)
        before = PRIOR["weight_hash"](base)
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
            admission(runtime, data["development"][:3] + data["admission"], args.output)
        if args.admission_only:
            print("ADMISSION PASSED", flush=True)
            return
        key = args.key_file.expanduser().read_text().strip()
        with InputTokenBudget(
            args.output / "ledger.jsonl", max_usd=3, usd_per_million=0.05
        ) as budget:
            async with S["StudyClient"](
                key, model=manifest["jev_model"], request_timeout=90, max_retries=0
            ) as client:
                receipts = S["ReceiptStore"](args.output / "receipts.jsonl", client, budget)
                runner = Runner(runtime, log, receipts, manifest)
                selected = await runner.develop(data["development"])
                freeze = dict(
                    selected_sha256=D["sha"](args.output / "selected.json"),
                    schedule_sha256=manifest["datasets"]["schedule.json"],
                    sources=manifest["sources"],
                )
                path = args.output / "test-freeze.json"
                if path.exists():
                    if json.loads(path.read_text()) != freeze:
                        raise ValueError("Test freeze mismatch")
                else:
                    D["dump"](path, freeze)
                cases = {c["id"]: c for c in data["test"]}
                for i, job in enumerate(data["schedule"]):
                    policy, gate = arm_config(job["arm"], selected)
                    await runner.job(
                        cases[job["case_id"]], job["arm"], policy, gate=gate, stage="test"
                    )
                    if i % 36 == 0:
                        print(
                            json.dumps(
                                dict(
                                    test_done=i + 1,
                                    planned=len(data["schedule"]),
                                    receipts=len(receipts.receipts),
                                    incidents=runner.incidents,
                                    charged_tokens=budget.charged_tokens,
                                )
                            ),
                            flush=True,
                        )
                after = PRIOR["weight_hash"](base)
                if after != before:
                    raise ValueError("Weights changed")
                D["dump"](
                    args.output / "completion.json",
                    dict(
                        at=J["now"](),
                        outputs=len(log.outputs),
                        receipts=len(receipts.receipts),
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
    p.add_argument("--output", type=Path)
    p.add_argument("--key-file", type=Path, default=Path("~/.typesafe.ai/jev"))
    p.add_argument("--device", default="cuda")
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--admission-only", action="store_true")
    args = p.parse_args()
    if args.command == "prepare":
        prepare(args.manifest, args.hotpot)
    else:
        asyncio.run(run(args))


if __name__ == "__main__":
    main()
