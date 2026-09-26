"""R16 FP32 execution amendment; frozen original runner and scientific design retained."""

import argparse
import asyncio
import hashlib
import json
import math
import platform
import random
import runpy
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent / "adaptive_attention"
D = runpy.run_path(str(HERE / "data.py"))
P = runpy.run_path(str(HERE / "policies.py"))
J = runpy.run_path(str(HERE / "journal.py"))
S = runpy.run_path(str(HERE / "scorer.py"))
DIRECT_ARMS = ("native", "r15", "tuned", "shuffled", "lexical")
STAGED_ARMS = ("native", "r15", "tuned", "dynamic", "shuffled_dynamic", "lexical_dynamic")
MODEL = "ibm-granite/granite-4.0-1b"
REVISION = "6a7381ba1f54d684ff508d991aeb7dc580157103"


def source_hashes():
    paths = list(HERE.glob("*.py"))
    paths += [Path(__file__).resolve(), ROOT / "research/adaptive-attention-fp32-amendment.md"]
    paths += [ROOT / "research/adaptive-attention-protocol.md"]
    paths += [
        ROOT / f"research/experiments/evidence_{x}.py" for x in ("attention", "runtime", "scorer")
    ]
    paths += list((ROOT / "src/jev_guided_decoding").rglob("*.py"))
    paths += [ROOT / "uv.lock"]
    return {str(p.relative_to(ROOT)): D["sha"](p) for p in sorted(paths)}


def all_cases(test, hotpot):
    transfers = [
        D["variant"](c, family)
        for c in test
        if c["index"] < 120
        for family in ("paraphrase", "dependency")
    ]
    return test + transfers + hotpot


def schedule(test, hotpot):
    result = []
    for case in all_cases(test, hotpot):
        if case["family"] == "original":
            panels = [
                ("constrained", DIRECT_ARMS + ("zero",)),
                ("open_explicit", DIRECT_ARMS),
                ("open_neutral", DIRECT_ARMS),
            ]
            if case["index"] < 120:
                panels.append(("staged", STAGED_ARMS))
        elif case["family"] == "hotpot":
            panels = [("open_explicit", DIRECT_ARMS), ("staged", STAGED_ARMS)]
        else:
            panels = [("staged", STAGED_ARMS)]
        for contract, arms in panels:
            arms = list(arms)
            random.Random(f"r16-order/{case['id']}/{contract}").shuffle(arms)
            result.extend(dict(case_id=case["id"], contract=contract, arm=a) for a in arms)
    return result


def prepare(folder, hotpot_path):
    from transformers import AutoTokenizer

    R = runpy.run_path(str(HERE / "runtime.py"))
    folder.mkdir(parents=True, exist_ok=False)
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL, revision=REVISION, local_files_only=True, trust_remote_code=False
    )
    dev, test = D["synthetic"]("development", 96), D["synthetic"]("test", 300)
    raw = sorted(json.loads(hotpot_path.read_text()), key=lambda c: c["id"])
    random.Random(460922191).shuffle(raw)
    chosen, eligibility = [], []
    for row in raw:
        sources = [
            {"id": f"D{i + 1:02}", "text": title + ": " + "".join(sentences)}
            for i, (title, sentences) in enumerate(
                zip(row["context"]["title"], row["context"]["sentences"], strict=True)
            )
        ]
        case = dict(
            id="hotpot/" + row["id"],
            world_id="hotpot/" + row["id"],
            upstream_id=row["id"],
            family="hotpot",
            question=row["question"],
            sources=sources,
            reference=row["answer"],
            depth=2,
            missing=False,
            condition="distractor",
            split="external",
            question_type=row["type"],
        )
        try:
            enc = R["encode"](tokenizer, D["public_view"](case), "staged")
            length = len(enc["input_ids"])
        except ValueError as exc:
            if str(exc) != "Input context limit":
                raise
            length = 2201
        eligible = len(sources) == 10 and length <= 2048
        eligibility.append(
            {
                "id": row["id"],
                "prompt_tokens": length,
                "eligible": eligible,
                "reason": "length/source-count only",
            }
        )
        if eligible:
            chosen.append(case)
        if len(chosen) == 212:
            break
    if len(chosen) != 212:
        raise ValueError("Insufficient eligible external questions")
    admission, hotpot = chosen[:12], chosen[12:]
    for name, value in [
        ("development", dev),
        ("test", test),
        ("hotpot", hotpot),
        ("admission", admission),
        ("eligibility", eligibility),
    ]:
        D["dump"](folder / f"{name}.json", value)
    planned = schedule(test, hotpot)
    D["dump"](folder / "schedule.json", planned)
    # Validate every public prompt, but never load model weights or obtain judgments.
    cases = {c["id"]: c for c in all_cases(test, hotpot)}
    seen = set()
    for job in planned:
        key = job["case_id"], job["contract"]
        if key not in seen:
            R["encode"](tokenizer, D["public_view"](cases[key[0]]), key[1])
            seen.add(key)
    D["dump"](
        folder / "manifest.json",
        dict(
            schema="adaptive-attention-r16-fp32",
            at=J["now"](),
            sources=source_hashes(),
            datasets={p.name: D["sha"](p) for p in folder.glob("*.json")},
            model=MODEL,
            revision=REVISION,
            jev_model="jev-1.13.0",
            source_revision=subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            raw_hotpot_sha256=D["sha"](hotpot_path),
            raw_hotpot_url="https://huggingface.co/datasets/hotpotqa/hotpot_qa/resolve/main/"
            "distractor/validation-00000-of-00001.parquet",
            max_seconds=7.5 * 3600,
            api_cap_usd=5,
            usd_per_million=0.05,
            cloud_allowance_usd=15,
            prior_cumulative_usd=11.17353471834785,
            planned_test_jobs=len(planned),
            seeds=D["SEEDS"],
            hotpot_seed=460922191,
        ),
    )
    print(json.dumps({"prepared": True, "test_jobs": len(planned), "hotpot": len(hotpot)}))


class Runner:
    def __init__(self, runtime, journal, receipts, manifest):
        self.runtime, self.log, self.receipts, self.manifest = runtime, journal, receipts, manifest
        self.R = runpy.run_path(str(HERE / "runtime.py"))
        self.input_cache = {}
        for row in J["rows"](journal.folder / "inputs.jsonl"):
            self.input_cache[(row["id"], row["contract"])] = row
        self.start_time = time.monotonic()
        self.incidents = sum(r["status"] == "failed" for r in receipts.receipts.values())
        self.consecutive = 0
        for receipt in reversed(list(receipts.receipts.values())):
            if receipt["status"] == "complete":
                break
            self.consecutive += 1

    def deadline(self):
        if time.monotonic() - self.start_time > self.manifest["max_seconds"]:
            raise TimeoutError("Study time limit")

    def encoded(self, case, contract):
        key = case["id"], contract
        if key not in self.input_cache:
            enc = self.R["encode"](self.runtime.base.tokenizer, D["public_view"](case), contract)
            self.input_cache[key] = {"id": case["id"], **enc}
            J["append"](self.log.folder / "inputs.jsonl", self.input_cache[key])
        return self.input_cache[key]

    async def receipt(self, view, reasoning=""):
        self.deadline()
        if self.incidents >= 20 or self.consecutive >= 3:
            raise RuntimeError("Provider incident stop")
        count = len(self.receipts.receipts)
        receipt = await self.receipts.get(view, reasoning)
        if self.receipts.new_failure:
            self.incidents += 1
            self.consecutive += 1
            diag = receipt.get("diagnostics", {})
            code = diag.get("status_code")
            if code not in (429, 502, 503, 504, 529) and not (
                code is None
                and (
                    "tim" in receipt["reason"].lower()
                    or "request failed" in receipt["reason"].lower()
                )
            ):
                raise RuntimeError("Non-transient provider failure; retained receipt")
            J["append"](
                self.log.folder / "events.jsonl",
                {"event": "provider_cooldown", "at": J["now"](), "key": receipt["key"]},
            )
            # Shared transport's bounded diagnostics include Retry-After where available.
            delay = max(60, float(diag.get("retry_after_seconds") or 0))
            while delay > 0:
                self.deadline()
                await asyncio.sleep(min(60, delay))
                delay -= 60
        elif len(self.receipts.receipts) > count:
            self.consecutive = 0
        return receipt

    async def job(self, case, contract, arm, policy, *, stage="test"):
        self.deadline()
        ident = f"{stage}/{case['id']}/{contract}/{arm}"
        metadata = dict(
            case_id=case["id"],
            world_id=case["world_id"],
            contract=contract,
            arm=arm,
            stage=stage,
            family=case["family"],
            policy=policy,
        )
        if not self.log.start(ident, metadata):
            return self.log.outputs[ident]
        started = time.monotonic()
        encoded = self.encoded(case, contract)
        view = D["public_view"](case)
        session = self.runtime.session(encoded)
        used, updates = [], []
        dynamic = "dynamic" in arm
        lexical = arm.startswith("lexical")
        shuffled = arm.startswith("shuffled")
        active = arm not in ("native", "zero")
        current_scores = []

        async def maps(reasoning=""):
            nonlocal current_scores
            if not active:
                return {}
            if lexical:
                scores = D["lexical"](view, reasoning)
                receipt_key = None
            else:
                receipt = await self.receipt(view, reasoning)
                used.append(receipt["key"])
                if receipt["status"] != "complete":
                    return None
                scores = list(receipt["scores"])
                receipt_key = receipt["key"]
            raw_scores = list(scores)
            if shuffled:
                random.Random(f"r16-shuffle/{case['id']}/{reasoning}").shuffle(scores)
            current_scores = scores
            mapping = P["token_maps"](policy, encoded["span_token_indices"], scores)
            updates.append(
                dict(
                    reasoning=reasoning,
                    receipt_key=receipt_key,
                    raw_scores=raw_scores,
                    applied_scores=scores,
                    after_generated_tokens=sum(len(p["token_ids"]) for p in session.phases),
                )
            )
            return mapping

        try:
            bias = await maps()
            if bias is None:
                result = {"status": "provider_failed", "text": ""}
            elif contract == "constrained":
                labels = [*D["COLORS"], "UNKNOWN"]
                ids = [
                    self.runtime.base.tokenizer.encode(s, add_special_tokens=False) for s in labels
                ]
                if any(len(t) != 1 for t in ids):
                    raise ValueError("Label token contract")
                phase = session.generate(1, "final", maps=bias, allowed=[t[0] for t in ids])
                result = session.result()
                result["reference_logprob"] = phase["tokens"][0]["label_logprobs"][
                    labels.index(case["reference"])
                ]
            elif contract == "staged":
                tokenizer = self.runtime.base.tokenizer
                session.frame(
                    tokenizer.encode("Reasoning:\n", add_special_tokens=False), "reasoning cue"
                )
                for step in range(3):
                    phase = session.generate(
                        24, f"reasoning_{step + 1}", maps=bias, stop_newline=True
                    )
                    if phase["finish_reason"] == "eos":
                        break
                    if step < 2:
                        if dynamic:
                            first_frame = session.frames[0]
                            text = tokenizer.decode(
                                session.ids[first_frame["start"] + len(first_frame["token_ids"]) :],
                                skip_special_tokens=True,
                                clean_up_tokenization_spaces=False,
                            )
                            bias = await maps(text)
                            if bias is None:
                                break
                        if phase["finish_reason"] == "token_limit":
                            session.frame(
                                tokenizer.encode("\n", add_special_tokens=False), "chunk separator"
                            )
                if bias is None:
                    result = {**session.result(), "status": "provider_failed", "text": ""}
                else:
                    session.frame(
                        tokenizer.encode("\nFinal answer:", add_special_tokens=False), "final cue"
                    )
                    session.generate(32, "final", maps=bias)
                    result = session.result()
            else:
                session.generate(32, "final", maps=bias)
                result = session.result()
            result.update(
                metadata,
                updates=updates,
                receipt_keys=used,
                wall_seconds=time.monotonic() - started,
                prompt_digest=encoded["prompt_digest"],
            )
            result["grade"] = (
                D["grade"](case, result["text"], contract)
                if result["status"] == "complete"
                else {"correct": 0, "em": 0, "f1": 0.0, "parsed": None}
            )
            self.log.finish(ident, result)
            return self.log.outputs[ident]
        except BaseException as exc:
            partial = session.result()
            self.log.finish(
                ident,
                {
                    **partial,
                    **metadata,
                    "status": "error",
                    "text": "",
                    "error_type": type(exc).__name__,
                    "receipt_keys": used,
                    "updates": updates,
                    "wall_seconds": time.monotonic() - started,
                },
            )
            raise

    async def evaluate_policy(self, policy, cases):
        rows = [
            await self.job(c, "constrained", policy["id"], policy, stage="development")
            for c in cases
        ]
        complete = [r for r in rows if r["status"] == "complete"]
        return dict(
            policy=policy,
            accuracy=sum(r.get("grade", {}).get("correct", 0) for r in rows) / len(cases),
            mean_logprob=sum(r["reference_logprob"] for r in complete) / len(complete)
            if complete
            else -1000.0,
            completed=len(complete),
            cases=len(cases),
        )

    async def develop(self, cases):
        selected_path = self.log.folder / "selected.json"
        if selected_path.exists():
            return json.loads(selected_path.read_text())["selected"]["policy"]
        evaluated = {}

        async def evaluate(policy):
            if policy["id"] not in evaluated:
                evaluated[policy["id"]] = await self.evaluate_policy(policy, cases)
                J["append"](self.log.folder / "development-metrics.jsonl", evaluated[policy["id"]])
                print(
                    json.dumps(
                        {
                            "development_policies": len(evaluated),
                            "accuracy": evaluated[policy["id"]]["accuracy"],
                        }
                    ),
                    flush=True,
                )
            return evaluated[policy["id"]]

        diagnostics = [await evaluate(p) for p in P["diagnostic_policies"]()]
        current = P["choose"](diagnostics)
        path = [{"stage": "diagnostic", "selected": current["policy"]["id"]}]
        for index in range(12):
            candidates = []
            for strength in P["LEVELS"]:
                weights = list(current["policy"]["weights"])
                weights[index] = strength
                candidates.append(await evaluate(P["changed"](current["policy"], weights=weights)))
            current = P["choose"](candidates)
            path.append({"head_index": index, "selected": current["policy"]["id"]})
        candidates = []
        for mapping, threshold in [
            ("threshold", 0.35),
            ("threshold", 0.5),
            ("threshold", 0.65),
            ("threshold", 0.8),
            ("soft", 0.5),
        ]:
            candidates.append(
                await evaluate(
                    P["changed"](current["policy"], mapping=mapping, threshold=threshold)
                )
            )
        selected = P["choose"](candidates)
        D["dump"](
            selected_path,
            {
                "at": J["now"](),
                "selected": selected,
                "path": path,
                "all_metrics": list(evaluated.values()),
                "development_data_sha256": self.manifest["datasets"]["development.json"],
            },
        )
        return selected["policy"]


def weight_hash(base):
    result = hashlib.sha256()
    for name, tensor in base.model.state_dict().items():
        result.update(name.encode())
        result.update(
            tensor.detach().cpu().contiguous().view(__import__("torch").uint8).numpy().tobytes()
        )
    return result.hexdigest()


def admission(runtime, dev, external, output):
    import torch

    R = runpy.run_path(str(HERE / "runtime.py"))
    old = R["OLD"]["EvidenceRuntime"](runtime.base)
    checks = []
    for case in dev[:3]:
        view = D["public_view"](case)
        encoded = R["encode"](runtime.base.tokenizer, view, "constrained")
        oldview = {k: view[k] for k in ("id", "question", "sources")} | {
            "labels": [*D["COLORS"], "UNKNOWN"]
        }
        prior_encoded = old.encode(oldview)
        if encoded["input_ids"] != prior_encoded["input_ids"]:
            raise ValueError("R15 prompt lineage")
        scores = [float(i % 2 == 0) for i in range(len(view["sources"]))]
        policy = P["r15"]()
        bias = P["token_maps"](policy, encoded["span_token_indices"], scores)
        prior, prior_logits = old.forward(
            prior_encoded,
            heads=policy["heads"],
            scores=scores,
            strength=math.log(16),
            full_logits=True,
        )
        new = runtime.session(encoded).logits(bias).cpu()
        delta = float((prior_logits - new).abs().max())
        if delta != 0:
            raise ValueError(f"R15 hook equivalence failed: {delta}")
        checks.append(
            {
                "case": case["id"],
                "r15_full_vocab_max_difference": delta,
                "old_label": prior["label"],
            }
        )
    for case in dev[:3] + external[:3]:
        encoded = R["encode"](runtime.base.tokenizer, D["public_view"](case), "open_explicit")
        one, two = runtime.session(encoded), runtime.session(encoded)
        first, second = one.generate(4, "final", maps={}), two.generate(4, "final", maps={})
        if first["token_ids"] != second["token_ids"]:
            raise ValueError("Zero token identity")
        scores = [float(i % 2 == 0) for i in range(len(case["sources"]))]
        bias = P["token_maps"](P["r15"](), encoded["span_token_indices"], scores)
        cached = runtime.session(encoded)
        cached.generate(2, "check", maps=bias)
        incremental = cached.logits(bias)
        ids = torch.tensor([cached.ids], device=runtime.base.device)
        with (
            torch.inference_mode(),
            runtime.hook.apply(cached.ids, query_start=encoded["query_start"], maps=bias),
        ):
            full = (
                runtime.base.model(
                    input_ids=ids,
                    attention_mask=torch.ones_like(ids),
                    use_cache=False,
                    logits_to_keep=1,
                )
                .logits[0, -1]
                .float()
            )
        delta = float((incremental - full).abs().max())
        if delta > 0.0001 or int(incremental.argmax()) != int(full.argmax()):
            raise ValueError(f"Static cache check failed: {delta}")
        checks.append(
            {
                "case": case["id"],
                "zero_tokens": first["token_ids"],
                "cache_full_max_difference": delta,
                "same_argmax": True,
            }
        )
    D["dump"](output / "admission.json", {"at": J["now"](), "checks": checks, "passed": True})


async def run(args):
    from jev_guided_decoding.backends.transformers import TransformersBackend
    from jev_guided_decoding.experiment_budget import InputTokenBudget

    R = runpy.run_path(str(HERE / "runtime.py"))
    manifest = json.loads((args.manifest / "manifest.json").read_text())
    if manifest["sources"] != source_hashes():
        raise ValueError("Source freeze mismatch")
    for name, digest in manifest["datasets"].items():
        if D["sha"](args.manifest / name) != digest:
            raise ValueError("Dataset freeze mismatch")

    def read(name):
        return json.loads((args.manifest / f"{name}.json").read_text())

    dev, test, hotpot, external = (
        read("development"),
        read("test"),
        read("hotpot"),
        read("admission"),
    )
    jobs = schedule(test, hotpot)
    if jobs != read("schedule"):
        raise ValueError("Schedule freeze mismatch")
    with J["Journal"](args.output, manifest) as log:
        base = TransformersBackend.load(
            MODEL,
            revision=REVISION,
            device=args.device,
            dtype="float32",
            local_files_only=args.local_files_only,
        )
        runtime = R["Runtime"](base)
        before = weight_hash(base)
        J["append"](
            args.output / "loads.jsonl",
            {
                "at": J["now"](),
                "weights_before": before,
                "python": platform.python_version(),
                "backend": base.metadata(),
            },
        )
        if not (args.output / "admission.json").exists():
            admission(runtime, dev, external, args.output)
        if args.admission_only:
            print("ADMISSION PASSED", flush=True)
            return
        key = args.key_file.expanduser().read_text().strip()
        with InputTokenBudget(
            args.output / "ledger.jsonl", max_usd=5, usd_per_million=0.05
        ) as budget:
            async with S["StudyClient"](
                key, model=manifest["jev_model"], request_timeout=90, max_retries=0
            ) as client:
                receipts = S["ReceiptStore"](args.output / "receipts.jsonl", client, budget)
                runner = Runner(runtime, log, receipts, manifest)
                selected = await runner.develop(dev)
                freeze_path = args.output / "test-freeze.json"
                freeze = {
                    "selected": selected,
                    "sources": manifest["sources"],
                    "schedule_sha256": manifest["datasets"]["schedule.json"],
                }
                if freeze_path.exists():
                    if json.loads(freeze_path.read_text()) != freeze:
                        raise ValueError("Test policy freeze changed")
                else:
                    D["dump"](freeze_path, freeze)
                cases = {c["id"]: c for c in all_cases(test, hotpot)}
                for index, job in enumerate(jobs):
                    policy = (
                        None
                        if job["arm"] in ("native", "zero")
                        else (P["r15"]() if job["arm"] == "r15" else selected)
                    )
                    await runner.job(cases[job["case_id"]], job["contract"], job["arm"], policy)
                    if index % 50 == 0:
                        print(
                            json.dumps(
                                {
                                    "test_done": index + 1,
                                    "planned": len(jobs),
                                    "receipts": len(receipts.receipts),
                                    "incidents": runner.incidents,
                                    "charged_tokens": budget.charged_tokens,
                                }
                            ),
                            flush=True,
                        )
                after = weight_hash(base)
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
                        test_jobs=len(jobs),
                        completed_schedule=True,
                    ),
                )
                print("STUDY COMPLETE", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["prepare", "run"])
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--hotpot", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--key-file", type=Path, default=Path("~/.typesafe.ai/jev"))
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--admission-only", action="store_true")
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.manifest, args.hotpot)
    else:
        asyncio.run(run(args))


if __name__ == "__main__":
    main()
