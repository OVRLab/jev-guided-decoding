"""Separately admitted exposed-case worker; references never enter its runtime."""

import argparse
import asyncio
import gc
import json
import platform
import runpy
import time
from pathlib import Path

from jev_guided_decoding.experiment_budget import InputTokenBudget
from jev_guided_decoding.jev import JevScorer, load_api_key

HERE = Path(__file__).resolve().parent
CONTRACT = runpy.run_path(str(HERE / "contract.py"))
PIPE = runpy.run_path(str(HERE / "pipeline.py"))
COMP = runpy.run_path(str(HERE / "comparator.py"))
dump, now = COMP["dump"], PIPE["now"]


def load_original(device):
    return runpy.run_path(str(HERE.parent / "structured_correction/study.py"))["load_model"](device)


def load_larger(device):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(
        COMP["MODEL"], revision=COMP["REVISION"], trust_remote_code=False
    )
    model = (
        AutoModelForCausalLM.from_pretrained(
            COMP["MODEL"],
            revision=COMP["REVISION"],
            torch_dtype=torch.bfloat16,
            attn_implementation="sdpa",
            trust_remote_code=False,
            use_safetensors=True,
        )
        .to(device)
        .eval()
        .requires_grad_(False)
    )
    eos = model.generation_config.eos_token_id
    if model.config.model_type != "granite" or eos not in (100257, [100257]):
        raise ValueError("Unexpected pinned larger-model architecture or EOS")
    return model, tok, [100257]


def hardware(model, eos):
    import torch
    import transformers

    return dict(
        device=str(next(model.parameters()).device),
        dtype=str(next(model.parameters()).dtype),
        parameters=sum(p.numel() for p in model.parameters()),
        eos=eos,
        gpu=torch.cuda.get_device_name() if torch.cuda.is_available() else None,
        torch=torch.__version__,
        transformers=transformers.__version__,
        python=platform.python_version(),
    )


async def execute(args):
    m = CONTRACT["verify"](args.input)
    args.output.mkdir(parents=True, exist_ok=False)
    try:
        import torch
        from safetensors.torch import load_file

        if args.device != "cuda" or not torch.cuda.is_available():
            raise ValueError("Registered R32a execution requires CUDA")
        execution_started = time.monotonic()
        dump(
            args.output / "execution.json",
            dict(
                at=now(),
                device=args.device,
                manifest_sha256=CONTRACT["sha"](args.input / "manifest.json"),
                sources=CONTRACT["sources"](),
            ),
        )
        cases = json.loads((args.input / "cases.json").read_text())
        groups = json.loads((args.input / "groups.json").read_text())
        exposed = json.loads((args.input / "admission-input.json").read_text())
        selection = json.loads((args.input / "selection.json").read_text())
        model, tok, eos = load_original(args.device)
        started = time.monotonic()
        runtime = runpy.run_path(str(HERE / "runtime.py"))
        before = runtime["weight_digest"](model)
        if before != m["backbone_digest"]:
            raise ValueError("Original Granite differs from frozen R31 backbone")
        dump(args.output / "original-hardware.json", hardware(model, eos))
        aligned = PIPE["S"]["positions_for"](
            tok, exposed["case"], exposed["native"], eos=eos[0], limit=m["context_limit"]
        )
        repair = PIPE["S"]["repair_prefix"](
            tok, exposed["native"]["prompt_token_ids"], exposed["native"]["generated_token_ids"]
        )
        admission = runpy.run_path(str(HERE / "admission.py"))["admission"]
        dump(
            args.output / "mechanical-admission.json",
            admission(
                model,
                aligned["ids"],
                aligned["positions"],
                repair,
                layer=m["layer"],
                rank=m["rank"],
            ),
        )
        adapters = {}
        for name, seed in m["specs"]:
            row = selection[f"{name}/{seed}"]
            adapter = runtime["B"]["Repair"](model.config.hidden_size, m["rank"])
            adapter.load_state_dict(
                load_file(str(args.input / "adapters" / row["file"])), strict=True
            )
            if any(not torch.isfinite(p).all() for p in adapter.parameters()):
                raise ValueError("Nonfinite selected adapter")
            adapters[name, seed] = adapter.to(args.device).eval().requires_grad_(False)
        adapter_before = {f"{n}/{s}": runtime["weight_digest"](a) for (n, s), a in adapters.items()}
        dump(args.output / "adapter-bindings.json", dict(at=now(), before=adapter_before))
        runner = PIPE["Runner"](model, tok, eos, m, args.output / "original", None)
        # Include extraction/mechanical admission in the common post-load deadline.
        runner.started_at = started
        with InputTokenBudget(
            runner.output / "budget.jsonl",
            max_usd=m["api_cap_usd"],
            usd_per_million=m["usd_per_million"],
        ) as budget:
            scorer = JevScorer(load_api_key(args.key_file), model="jev-1.13.0", max_retries=0)
            try:
                runner.feedback = PIPE["F"]["Feedback"](
                    scorer, budget, runner.output, delay=m["api_delay_seconds"]
                )
                await runner.drafts(cases)
                runner.repairs(cases, groups, adapters)
                if budget.unresolved:
                    raise ValueError("Unknown charged request remains")
                charged = budget.charged_tokens
            finally:
                await scorer.__aexit__(None, None, None)
        after = runtime["weight_digest"](model)
        adapter_after = {f"{n}/{s}": runtime["weight_digest"](a) for (n, s), a in adapters.items()}
        runtime["idle_frozen"](model)
        if (
            before != after
            or adapter_before != adapter_after
            or any(
                p.requires_grad or p.grad is not None
                for a in adapters.values()
                for p in a.parameters()
            )
        ):
            raise ValueError("Original or adapter weight ownership changed")
        dump(
            args.output / "original-complete.json",
            dict(
                at=now(),
                outputs=len(runner.rows),
                backbone_before=before,
                backbone_after=after,
                adapters_before=adapter_before,
                adapters_after=adapter_after,
                charged_input_tokens=charged,
                seconds=time.monotonic() - started,
            ),
        )
        del runner, adapter, adapters, model, tok
        gc.collect()
        torch.cuda.empty_cache()
        model, tok, eos = load_larger(args.device)
        dump(args.output / "larger-hardware.json", hardware(model, eos))
        remaining = m["max_seconds"] - (time.monotonic() - started)
        comparator = COMP["Comparator"](
            model, tok, eos, args.output / "larger", max_seconds=remaining
        )
        comparator.run(cases, m["larger_profiles"])
        CONTRACT["verify"](args.input)
        if time.monotonic() - started > m["max_seconds"]:
            raise TimeoutError("Combined R32a deadline exceeded")
        total = m["planned_cases"] * (3 + 3 * len(m["specs"]) + len(m["larger_profiles"]))
        if total != m["planned_outputs"]:
            raise ValueError("Changed planned coverage")
        dump(
            args.output / "complete.json",
            dict(
                at=now(),
                outputs=total,
                requests=m["planned_requests"],
                charged_input_tokens=charged,
                seconds=time.monotonic() - execution_started,
                post_original_load_seconds=time.monotonic() - started,
            ),
        )
    except BaseException as exc:
        dump(args.output / "failed.json", dict(error_type=type(exc).__name__, at=now()))
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "verify", "run"))
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--dataset", type=Path)
    parser.add_argument("--device", choices=("cuda",), default="cuda")
    parser.add_argument("--key-file", type=Path, default=Path.home() / ".typesafe.ai/jev")
    args = parser.parse_args()
    if args.command == "prepare":
        if args.output is None or args.dataset is None:
            parser.error("prepare requires --output and --dataset")
        CONTRACT["prepare"](args.output, args.dataset)
        print(
            json.dumps(
                dict(prepared=True, manifest_sha256=CONTRACT["sha"](args.output / "manifest.json"))
            )
        )
    elif args.command == "verify":
        if args.input is None:
            parser.error("verify requires --input")
        CONTRACT["verify"](args.input)
        print(json.dumps(dict(verified=True)))
    else:
        if args.input is None or args.output is None:
            parser.error("run requires --input and --output")
        asyncio.run(execute(args))


if __name__ == "__main__":
    main()
