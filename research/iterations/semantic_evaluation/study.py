"""Frozen R20 preparation and three-arm generation using the unchanged R19 runtime."""

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
S = runpy.run_path(str(HERE.parent / "benefit_sufficiency/study.py"))
D = runpy.run_path(str(HERE / "data.py"))
G = runpy.run_path(str(HERE / "judge.py"))
J = S["J"]
BASE_D = S["D"]
ARMS = ("native", "static", "dual")


def source_hashes():
    values = S["source_hashes"]()
    for p in [
        *HERE.glob("*.py"),
        ROOT / "research/semantic-evaluation-plan.md",
        ROOT / "research/diagnostics/benefit_sufficiency_audit.py",
        ROOT / "research/benefit-sufficiency-audit-portability.md",
    ]:
        values[str(p.relative_to(ROOT))] = BASE_D["sha"](p)
    return dict(sorted(values.items()))


def verify(folder):
    m = json.loads((folder / "manifest.json").read_text())
    if m["sources"] != source_hashes() or any(
        BASE_D["sha"](folder / n) != h for n, h in m["datasets"].items()
    ):
        raise ValueError("Scientific source/data freeze mismatch")
    return m


def configuration(arm):
    if arm not in ARMS:
        raise ValueError("Unknown arm")
    return dict(kind="never" if arm == "native" else "always"), arm == "static"


def prepare(folder, hotpot, squad):
    from transformers import AutoTokenizer

    if folder.exists():
        raise FileExistsError("New freeze directory required")
    tok = AutoTokenizer.from_pretrained(S["MODEL"], revision=S["REVISION"], local_files_only=True)
    cases, eligibility = D["cohorts"](tok, hotpot, squad)
    fixtures = runpy.run_path(str(HERE / "fixtures.py"))["fixtures"]()
    admission = json.loads(
        (ROOT / "research/protocols/benefit-sufficiency-v1/fit.json").read_text()
    )[:3]
    jobs = []
    ordered = list(cases)
    random.Random(203092323).shuffle(ordered)
    for c in ordered:
        arms = list(ARMS)
        random.Random("r20-order/" + c["id"]).shuffle(arms)
        jobs.extend(dict(case_id=c["id"], arm=a) for a in arms)
    packets = []
    for part in ("development", "validation"):
        packets += [
            dict(id=x["id"], packet=x["packet"], packet_digest=G["digest"](x["packet"]))
            for x in fixtures[part]
        ]
    packets += [
        dict(id="repeat/" + x["id"], packet=x["packet"], packet_digest=G["digest"](x["packet"]))
        for x in fixtures["validation"][:12]
    ]
    random.Random(203092327).shuffle(packets)
    folder.mkdir(parents=True)
    for name, v in [
        ("test", cases),
        ("eligibility", eligibility),
        ("fixtures", fixtures),
        ("admission", admission),
        ("schedule", jobs),
        ("validation-packets", packets),
    ]:
        BASE_D["dump"](folder / (name + ".json"), v)
    previous = json.loads(
        (ROOT / "research/protocols/benefit-sufficiency-v1/manifest.json").read_text()
    )
    manifest = {
        k: previous[k]
        for k in (
            "model",
            "revision",
            "jev_model",
            "precision",
            "boundary",
            "num_layers",
            "eos_ids",
            "treatment",
        )
    }
    manifest.update(
        protocol="r20-semantic-evaluation-v1",
        at=J["now"](),
        sources=source_hashes(),
        datasets={p.name: BASE_D["sha"](p) for p in folder.glob("*.json")},
        max_seconds=6000,
        max_api_usd=1,
        cloud_allowance_usd=8,
        prior_spend_usd=30.22803312122089,
        cumulative_budget_usd=50,
        judge_model=G["MODEL"],
        judge_revision=G["REVISION"],
        source_hotpot_sha256=BASE_D["sha"](hotpot),
        source_squad_sha256=BASE_D["sha"](squad),
        primary_interval=1 - 0.05 / 6,
        arms=list(ARMS),
        test_cases=len(cases),
        test_jobs=len(jobs),
    )
    BASE_D["dump"](folder / "manifest.json", manifest)
    print(
        json.dumps(
            dict(
                test_cases=len(cases),
                generation_jobs=len(jobs),
                judge_validation_packets=len(packets),
            )
        )
    )


class Runner(S["Runner"]):
    async def job(self, c, arm):
        self.deadline()
        while self.cooldown > 0:
            delay = min(30, self.cooldown)
            await asyncio.sleep(delay)
            self.cooldown -= delay
            self.deadline()
        gate, canned = configuration(arm)
        metadata = dict(
            case_id=c["id"],
            world_id=c["world_id"],
            domain=BASE_D["domain"](c),
            family=c["family"],
            stage="test",
            arm=arm,
            policy=S["treatment"](),
            requested_gate=gate,
        )
        ident = f"test/{c['id']}/{arm}"
        if not self.log.start(ident, metadata):
            return self.log.outputs[ident]
        before = len(self.receipts.receipts)

        async def callback(view):
            if canned:
                return dict(
                    status="complete",
                    key="canned-static-instruction",
                    scores=[0.5] * len(view["sources"]),
                    sufficient=0.0,
                )
            return await self.receipt(view)

        try:
            encoded = self.encoded(c)
            with S["Profile"](self.base) as profile:
                row = await self.R["generate"](
                    self.current,
                    encoded,
                    BASE_D["public_view"](c),
                    S["treatment"](),
                    callback,
                    gate=gate,
                    mode="dual",
                    instruction_strength=5,
                )
            physical = len(self.receipts.receipts) - before
            row.update(
                metadata,
                physical_jev_attempts=physical,
                local_callback_count=int(canned),
                provider_kind="canned" if canned else "jev" if arm == "dual" else "none",
                forward_events=profile.events,
                peak_gpu_bytes=profile.peak,
                grade=BASE_D["grade"](c, row["text"]),
            )
            if canned:
                row["logical_jev_calls"] = 0
            if (
                row["model_forwards"] != len(profile.events)
                or row["layer_calls"] != profile.layer_calls
                or row["layer_token_counts"] != profile.layer_tokens
            ):
                raise ValueError("Independent forward profile mismatch")
            self.log.finish(ident, row)
        except BaseException as exc:
            self.log.finish(
                ident,
                dict(
                    **metadata,
                    status="error",
                    error_type=type(exc).__name__,
                    text="",
                    work_unknown=True,
                    physical_jev_attempts=len(self.receipts.receipts) - before,
                ),
            )
            raise
        return self.log.outputs[ident]


async def generate(folder, output, key_file, admission_file):
    from jev_guided_decoding.backends.transformers import TransformersBackend
    from jev_guided_decoding.experiment_budget import InputTokenBudget

    m = verify(folder)
    admitted = json.loads(admission_file.read_text())
    if not admitted["passed"] or admitted["manifest_sha256"] != BASE_D["sha"](
        folder / "manifest.json"
    ):
        raise ValueError("Judge must pass frozen validation before test generation")
    cases = {c["id"]: c for c in json.loads((folder / "test.json").read_text())}
    schedule = json.loads((folder / "schedule.json").read_text())
    with J["Journal"](output, m) as log:
        base = TransformersBackend.load(
            m["model"],
            revision=m["revision"],
            device="cuda",
            dtype="float32",
            local_files_only=True,
        )
        weights = S["OLD"]["OLD"]["PRIOR"]["weight_hash"](base)
        J["append"](
            output / "loads.jsonl",
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
        if not (output / "admission.json").exists():
            await runpy.run_path(str(HERE.parent / "benefit_sufficiency/admission.py"))[
                "admission"
            ](base, json.loads((folder / "admission.json").read_text()), output, S["treatment"]())
        with InputTokenBudget(
            output / "ledger.jsonl", max_usd=m["max_api_usd"], usd_per_million=0.05
        ) as budget:
            async with S["S"]["StudyClient"](
                key_file.expanduser().read_text().strip(),
                model=m["jev_model"],
                request_timeout=90,
                max_retries=0,
            ) as client:
                store = S["S"]["ReceiptStore"](output / "receipts.jsonl", client, budget)
                runner = Runner(base, log, store, m)
                for i, job in enumerate(schedule):
                    await runner.job(cases[job["case_id"]], job["arm"])
                    if i % 30 == 0:
                        print(
                            json.dumps(
                                dict(
                                    generated=i + 1,
                                    total=len(schedule),
                                    receipts=len(store.receipts),
                                )
                            ),
                            flush=True,
                        )
                after = S["OLD"]["OLD"]["PRIOR"]["weight_hash"](base)
                if after != weights:
                    raise ValueError("Model weights changed")
                BASE_D["dump"](
                    output / "completion.json",
                    dict(
                        at=J["now"](),
                        outputs=len(log.outputs),
                        weights_before=weights,
                        weights_after=after,
                        receipts=len(store.receipts),
                        charged_tokens=budget.charged_tokens,
                        completed_schedule=True,
                    ),
                )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=("prepare", "generate"))
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--output", type=Path)
    p.add_argument("--hotpot", type=Path)
    p.add_argument("--squad", type=Path)
    p.add_argument("--key-file", type=Path, default=Path("~/.typesafe.ai/jev"))
    p.add_argument("--judge-admission", type=Path)
    a = p.parse_args()
    if a.command == "prepare":
        prepare(a.manifest, a.hotpot, a.squad)
    else:
        asyncio.run(generate(a.manifest, a.output, a.key_file, a.judge_admission))


if __name__ == "__main__":
    main()
