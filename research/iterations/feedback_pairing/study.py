"""Frozen-checkpoint R30 execution reuses the audited R29 serial runtime."""

import argparse
import asyncio
import json
import platform
import runpy
import shutil
import subprocess
import time
from pathlib import Path

from jev_guided_decoding.experiment_budget import InputTokenBudget
from jev_guided_decoding.jev import JevScorer, load_api_key

HERE = Path(__file__).resolve().parent
C = runpy.run_path(str(HERE / "common.py"))
R29 = runpy.run_path(str(HERE.parent / "structured_correction/study.py"))
F = R29["F"]
dump, sha, now = C["dump"], C["sha"], F["now"]


def prepare(folder, upstream):
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=C["ROOT"], text=True).strip():
        raise ValueError("Freeze requires committed source")
    cases, refs = C["worlds"]()
    old, _ = C["R29"]["make_data"]()
    if {c["prompt"] for c in cases} & {c["prompt"] for c in old}:
        raise ValueError("R29/R30 overlap")
    provenance = json.loads(
        (C["ROOT"] / "reports/2026-09-26-structured-correction/provenance.json").read_text()
    )
    selected = C["selected_checkpoints"](upstream, provenance)
    folder.mkdir(parents=True, exist_ok=False)
    (folder / "checkpoints").mkdir()
    dump(folder / "cases.json", cases)
    dump(folder / "references.json", refs)
    shutil.copyfile(upstream / "selection.json", folder / "r29-selection.json")
    dump(folder / "r29-provenance.json", provenance)
    checkpoints = {}
    for key, row in selected.items():
        name = "checkpoints/" + row["file"]
        shutil.copyfile(upstream / row["file"], folder / name)
        checkpoints[key] = dict(file=name, sha256=row["sha256"], epoch=row["epoch"])
    manifest = dict(
        study="R30",
        at=now(),
        git_revision=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=C["ROOT"], text=True
        ).strip(),
        source_dirty=False,
        sources=C["sources"](),
        files={
            str(p.relative_to(folder)): sha(p) for p in sorted(folder.rglob("*")) if p.is_file()
        },
        model=C["R29"]["MODEL"],
        revision=C["R29"]["REVISION"],
        checkpoints=checkpoints,
        seeds=C["SEEDS"],
        modes=C["MODES"],
        layer=19,
        rank=32,
        limit=128,
        max_seconds=16200,
        api_cap_usd=0.18,
        usd_per_million=0.05,
        api_delay_seconds=0.25,
        planned_cases=384,
        planned_outputs=7680,
        data_seed=30001,
    )
    dump(folder / "manifest.json", manifest)
    print(json.dumps(dict(prepared=True, manifest_sha256=sha(folder / "manifest.json"))))


def verify(folder):
    m = json.loads((folder / "manifest.json").read_text())
    fixed = dict(
        study="R30",
        source_dirty=False,
        model=C["R29"]["MODEL"],
        revision=C["R29"]["REVISION"],
        seeds=list(C["SEEDS"]),
        modes=list(C["MODES"]),
        layer=19,
        rank=32,
        limit=128,
        max_seconds=16200,
        api_cap_usd=0.18,
        usd_per_million=0.05,
        api_delay_seconds=0.25,
        planned_cases=384,
        planned_outputs=7680,
        data_seed=30001,
    )
    expected_keys = {f"{mode}/{seed}" for mode in ("structured", "scalar") for seed in C["SEEDS"]}
    if (
        any(m.get(k) != value for k, value in fixed.items())
        or set(m.get("checkpoints", {})) != expected_keys
    ):
        raise ValueError("Frozen protocol contract mismatch")
    if m["sources"] != C["sources"]():
        raise ValueError("Frozen source mismatch")
    actual = {
        str(p.relative_to(folder)): sha(p)
        for p in folder.rglob("*")
        if p.is_file() and p != folder / "manifest.json"
    }
    if actual != m["files"]:
        raise ValueError("Frozen input inventory or byte mismatch")
    cases, refs = C["worlds"](m["planned_cases"], m["data_seed"])
    if (
        json.loads((folder / "cases.json").read_text()) != cases
        or json.loads((folder / "references.json").read_text()) != refs
    ):
        raise ValueError("Unreproducible frozen cohort")
    for row in m["checkpoints"].values():
        if row["file"] not in actual or row["sha256"] != actual[row["file"]]:
            raise ValueError("Checkpoint manifest mismatch")
    provenance = json.loads((folder / "r29-provenance.json").read_text())
    public = json.loads(
        (C["ROOT"] / "reports/2026-09-26-structured-correction/provenance.json").read_text()
    )
    if (
        provenance != public
        or sha(folder / "r29-selection.json")
        != public["original_backup_inventory"]["selection.json"]
    ):
        raise ValueError("Frozen checkpoint selection contract mismatch")
    selection = json.loads((folder / "r29-selection.json").read_text())["models"]
    for key, row in m["checkpoints"].items():
        chosen = selection[key]
        if (
            row
            != dict(
                file="checkpoints/" + chosen["file"], sha256=chosen["sha256"], epoch=chosen["epoch"]
            )
            or chosen["sha256"] != public["original_backup_inventory"][chosen["file"]]
        ):
            raise ValueError("Frozen checkpoint lineage contract mismatch")
    return m


def run_repairs(runner, cases, adapters):
    donors = C["donors"](cases)
    dump(runner.output / "donors.json", donors)
    for case in cases:
        item = runner.prepared[case["id"]]
        runner.answer(case, "blind", item["prompt"])
        for seed in runner.m["seeds"]:
            for mode in C["MODES"]:
                p = C["signal"](
                    mode,
                    item["p"],
                    donor=runner.prepared[donors[case["id"]]]["p"],
                    truth=item["grade"]["slots"],
                    draft=item["native"]["text"],
                )
                key = ("scalar" if mode == "scalar_trained" else "structured", seed)
                runner.answer(
                    case,
                    f"{mode}/{seed}",
                    item["prompt"],
                    adapter=adapters[key],
                    memory=item["memory"],
                    probabilities=p,
                )


async def execute(args):
    import torch
    import transformers
    from safetensors.torch import load_file

    m = verify(args.input)
    args.output.mkdir(parents=True, exist_ok=False)
    dump(
        args.output / "execution.json",
        dict(
            at=now(),
            device=args.device,
            python=platform.python_version(),
            manifest_sha256=sha(args.input / "manifest.json"),
            sources=C["sources"](),
        ),
    )
    cases = json.loads((args.input / "cases.json").read_text())
    refs = json.loads((args.input / "references.json").read_text())
    model, tok, eos = R29["load_model"](args.device)
    runtime = runpy.run_path(str(HERE.parent / "structured_correction/runtime.py"))
    dump(
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
    before = runtime["weight_digest"](model)
    dump(args.output / "mechanical-admission.json", runtime["admission"](model, tok, cases[0], eos))
    adapters, adapter_before = {}, {}
    for key, row in m["checkpoints"].items():
        mode, seed = key.split("/")
        adapter = runtime["B"]["Repair"](model.config.hidden_size, m["rank"]).to(args.device)
        adapter.load_state_dict(load_file(str(args.input / row["file"]), device="cpu"))
        adapter.eval().requires_grad_(False)
        adapters[mode, int(seed)] = adapter
        adapter_before[key] = runtime["weight_digest"](adapter)
    dump(
        args.output / "adapter-bindings.json",
        dict(checkpoints=m["checkpoints"], before=adapter_before),
    )
    with InputTokenBudget(
        args.output / "budget.jsonl", max_usd=m["api_cap_usd"], usd_per_million=m["usd_per_million"]
    ) as budget:
        scorer = JevScorer(load_api_key(args.key_file), model="jev-1.13.0", max_retries=0)
        try:
            feedback = F["Feedback"](scorer, budget, args.output, delay=m["api_delay_seconds"])
            runner = R29["Runner"](model, tok, eos, m, args.output, feedback)
            await runner.drafts(cases, refs)
            run_repairs(runner, cases, adapters)
            C["coverage"](cases, runner.rows, m["seeds"])
            after = runtime["weight_digest"](model)
            adapter_after = {
                f"{mode}/{seed}": runtime["weight_digest"](a)
                for (mode, seed), a in adapters.items()
            }
            if (
                before != after
                or adapter_before != adapter_after
                or budget.unresolved
                or any(p.grad is not None for p in model.parameters())
            ):
                raise ValueError("Frozen parameter or resolved-charge integrity failure")
            dump(
                args.output / "complete.json",
                dict(
                    at=now(),
                    outputs=len(runner.rows),
                    backbone_before=before,
                    backbone_after=after,
                    adapters_before=adapter_before,
                    adapters_after=adapter_after,
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
    parser.add_argument("--upstream", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--device", default="cuda", choices=("cuda", "mps", "cpu"))
    parser.add_argument("--key-file", type=Path, default=Path.home() / ".typesafe.ai/jev")
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.output, args.upstream)
    else:
        try:
            asyncio.run(execute(args))
        except BaseException as exc:
            if args.output.is_dir():
                dump(args.output / "failed.json", dict(error_type=type(exc).__name__, at=now()))
            raise


if __name__ == "__main__":
    main()
