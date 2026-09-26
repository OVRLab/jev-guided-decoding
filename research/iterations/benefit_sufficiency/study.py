"""R19 fit/calibration/frozen-test workflow, with durable one-attempt hosted receipts."""

import argparse
import asyncio
import json
import platform
import random
import runpy
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OLD = runpy.run_path(str(HERE.parent / "boundary_attention/study.py"))
D = runpy.run_path(str(HERE / "data.py"))
P = runpy.run_path(str(HERE / "policies.py"))
S = runpy.run_path(str(HERE / "scorer.py"))
J, MODEL, REVISION, treatment, Profile = (
    OLD[k] for k in ("J", "MODEL", "REVISION", "treatment", "Profile")
)
ARMS = ("native", "relevance", "sufficiency", "dual", "benefit_gate", "random_gate", "r18_gate")
DEV_ARMS = ("native", "relevance", "dual_2", "dual_5")
R18_GATE = dict(
    kind="threshold", feature="head_disagreement", direction="le", threshold=0.05478179526607767
)


def source_hashes():
    values = OLD["source_hashes"]()
    for p in [*HERE.glob("*.py"), ROOT / "research/benefit-sufficiency-plan.md"]:
        values[str(p.relative_to(ROOT))] = D["sha"](p)
    return dict(sorted(values.items()))


def schedule(cases):
    cases = list(cases)
    random.Random(190922863).shuffle(cases)
    jobs = []
    for c in cases:
        others = [a for a in ARMS if a != "benefit_gate"]
        random.Random("r19-order/" + c["id"]).shuffle(others)
        jobs.extend(dict(case_id=c["id"], arm=a) for a in ["benefit_gate", *others])
    return jobs


def prepare(folder, hotpot, squad):
    from transformers import AutoTokenizer, GenerationConfig

    if folder.exists():
        raise FileExistsError("Use a new freeze directory")
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL, revision=REVISION, local_files_only=True, trust_remote_code=False
    )
    generation = GenerationConfig.from_pretrained(MODEL, revision=REVISION, local_files_only=True)
    eos = generation.eos_token_id
    data, eligibility, articles = D["cohorts"](tokenizer, hotpot, squad)
    folder.mkdir(parents=True)
    for name, value in list(data.items()) + [
        ("eligibility", eligibility),
        ("squad-article-split", articles),
        ("schedule", schedule(data["test"])),
    ]:
        D["dump"](folder / f"{name}.json", value)
    D["dump"](
        folder / "manifest.json",
        dict(
            protocol="r19-benefit-sufficiency-v1",
            at=J["now"](),
            model=MODEL,
            revision=REVISION,
            jev_model="jev-1.13.0",
            precision="float32",
            boundary=19,
            num_layers=40,
            eos_ids=sorted(set(eos if isinstance(eos, list) else [eos])),
            treatment=treatment(),
            max_seconds=5 * 3600,
            max_api_usd=2,
            source_hotpot_sha256=D["sha"](hotpot),
            source_squad_sha256=D["sha"](squad),
            sources=source_hashes(),
            datasets={p.name: D["sha"](p) for p in sorted(folder.glob("*.json"))},
            prior_spend_usd=27.22974113467281,
            cloud_allowance_usd=10,
            cumulative_budget_usd=50,
            primary_interval=1 - 0.05 / 6,
            seeds=D["SEEDS"],
        ),
    )
    print(json.dumps({s: len(c) for s, c in data.items()}))


class Runner(OLD["Runner"]):
    def __init__(self, base, log, receipts, manifest):
        super().__init__(base, log, receipts, manifest)
        self.R = runpy.run_path(str(HERE / "runtime.py"))
        self.current = self.R["Runtime"](base)

    async def job(self, c, arm, selected=None, *, stage):
        self.deadline()
        while self.cooldown > 0:
            delay = min(30, self.cooldown)
            await asyncio.sleep(delay)
            self.cooldown -= delay
            self.deadline()
        gate, mode, strength = configuration(arm, selected)
        metadata = dict(
            case_id=c["id"],
            world_id=c["world_id"],
            domain=D["domain"](c),
            family=c["family"],
            stage=stage,
            arm=arm,
            policy=treatment(),
            requested_gate=gate,
        )
        ident = f"{stage}/{c['id']}/{arm}"
        if not self.log.start(ident, metadata):
            return self.log.outputs[ident]
        before = len(self.receipts.receipts)
        try:
            encoded = self.encoded(c)
            with Profile(self.base) as profile:
                row = await self.R["generate"](
                    self.current,
                    encoded,
                    D["public_view"](c),
                    treatment(),
                    self.receipt,
                    gate=gate,
                    mode=mode,
                    instruction_strength=strength,
                )
            physical = len(self.receipts.receipts) - before
            receipt = self.receipts.receipts.get(row["receipt_key"], {})
            extra = receipt.get("seconds", 0) if row["logical_jev_calls"] and not physical else 0
            row.update(
                metadata,
                physical_jev_attempts=physical,
                receipt_seconds=receipt.get("seconds", 0),
                estimated_uncached_wall_seconds=row["wall_seconds"] + extra,
                forward_events=profile.events,
                peak_gpu_bytes=profile.peak,
                grade=D["grade"](c, row["text"]),
            )
            if (
                row["model_forwards"] != len(profile.events)
                or row["layer_calls"] != profile.layer_calls
                or row["layer_token_counts"] != profile.layer_tokens
            ):
                raise ValueError("Independent profile mismatch")
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

    async def develop(self, fit, calibration):
        path = self.log.folder / "selected.json"
        if path.exists():
            return json.loads(path.read_text())
        datasets = {}
        for stage, cases in [("fit", fit), ("calibration", calibration)]:
            values = []
            for i, c in enumerate(cases):
                arms = list(DEV_ARMS)
                random.Random("r19-dev/" + c["id"]).shuffle(arms)
                outputs = {a: await self.job(c, a, stage=stage) for a in arms}
                if any(r["features"] != outputs["native"]["features"] for r in outputs.values()):
                    raise ValueError("Treatment contaminated pre-call observation")
                values.append(
                    dict(
                        case_id=c["id"],
                        domain=D["domain"](c),
                        x=outputs["native"]["benefit_features"],
                        **{a: D["quality"](c, r["grade"]) for a, r in outputs.items()},
                    )
                )
                print(
                    json.dumps(
                        dict(stage=stage, done=i + 1, planned=len(cases), incidents=self.incidents)
                    ),
                    flush=True,
                )
            datasets[stage] = values
        selected = dict(
            at=J["now"](),
            **P["select"](datasets["fit"], datasets["calibration"]),
            development=datasets,
        )
        D["dump"](path, selected)
        return selected


def configuration(arm, selected=None):
    if arm not in (*ARMS, *DEV_ARMS):
        raise ValueError("Unknown arm")
    strength = (
        int(arm[-1])
        if arm in ("dual_2", "dual_5")
        else selected["instruction_strength"]
        if selected
        else 2
    )
    gate = {"kind": "never" if arm == "native" else "always"}
    if arm == "benefit_gate":
        gate = selected["gate"]
    elif arm == "random_gate":
        gate = dict(kind="random", fraction=selected["fraction"])
    elif arm == "r18_gate":
        gate = R18_GATE
    mode = arm if arm in ("relevance", "sufficiency") else "dual"
    return gate, mode, strength


async def run(args):
    from jev_guided_decoding.backends.transformers import TransformersBackend
    from jev_guided_decoding.experiment_budget import InputTokenBudget

    manifest = json.loads((args.manifest / "manifest.json").read_text())
    if manifest["sources"] != source_hashes() or any(
        D["sha"](args.manifest / n) != v for n, v in manifest["datasets"].items()
    ):
        raise ValueError("Source/data freeze mismatch")
    data = {
        n: json.loads((args.manifest / f"{n}.json").read_text())
        for n in ("fit", "calibration", "test", "schedule")
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
            raise ValueError("Checkpoint mismatch")
        weights = OLD["OLD"]["PRIOR"]["weight_hash"](base)
        J["append"](
            args.output / "loads.jsonl",
            dict(
                at=J["now"](),
                weights_before=weights,
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
            await runpy.run_path(str(HERE / "admission.py"))["admission"](
                base, data["fit"][:3], args.output, treatment()
            )
        if args.admission_only:
            print("ADMISSION PASSED", flush=True)
            return
        key = args.key_file.expanduser().read_text().strip()
        with InputTokenBudget(
            args.output / "ledger.jsonl", max_usd=manifest["max_api_usd"], usd_per_million=0.05
        ) as budget:
            async with S["StudyClient"](
                key, model=manifest["jev_model"], request_timeout=90, max_retries=0
            ) as client:
                store = S["ReceiptStore"](args.output / "receipts.jsonl", client, budget)
                runner = Runner(base, log, store, manifest)
                selected = await runner.develop(data["fit"], data["calibration"])
                freeze = dict(
                    at=J["now"](),
                    selected_sha256=D["sha"](args.output / "selected.json"),
                    schedule_sha256=manifest["datasets"]["schedule.json"],
                    sources=manifest["sources"],
                )
                freeze_path = args.output / "test-freeze.json"
                if freeze_path.exists():
                    previous = json.loads(freeze_path.read_text())
                    if any(previous[k] != v for k, v in freeze.items() if k != "at"):
                        raise ValueError("Test selection freeze mismatch")
                else:
                    D["dump"](freeze_path, freeze)
                cases = {c["id"]: c for c in data["test"]}
                for i, job in enumerate(data["schedule"]):
                    await runner.job(cases[job["case_id"]], job["arm"], selected, stage="test")
                    if i % 35 == 0:
                        print(
                            json.dumps(
                                dict(
                                    stage="test",
                                    done=i + 1,
                                    planned=len(data["schedule"]),
                                    receipts=len(store.receipts),
                                    incidents=runner.incidents,
                                    charged_tokens=budget.charged_tokens,
                                )
                            ),
                            flush=True,
                        )
                after = OLD["OLD"]["PRIOR"]["weight_hash"](base)
                if after != weights:
                    raise ValueError("Weights changed")
                D["dump"](
                    args.output / "completion.json",
                    dict(
                        at=J["now"](),
                        outputs=len(log.outputs),
                        receipts=len(store.receipts),
                        charged_tokens=budget.charged_tokens,
                        weights_before=weights,
                        weights_after=after,
                        completed_schedule=True,
                        test_jobs=len(data["schedule"]),
                    ),
                )
                print("STUDY COMPLETE", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["prepare", "run"])
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--hotpot", type=Path)
    parser.add_argument("--squad", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--key-file", type=Path, default=Path("~/.typesafe.ai/jev"))
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--admission-only", action="store_true")
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.manifest, args.hotpot, args.squad)
    else:
        asyncio.run(run(args))


if __name__ == "__main__":
    main()
