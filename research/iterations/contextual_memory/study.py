"""Bounded contextual-memory study; frozen protocol verification precedes inference."""

import argparse
import asyncio
import json
import platform
import runpy
import time
from pathlib import Path

from jev_guided_decoding.experiment_budget import InputTokenBudget
from jev_guided_decoding.jev import JevScorer, load_api_key

HERE = Path(__file__).resolve().parent
FROZEN = runpy.run_path(str(HERE / "contract.py"))
PIPE = runpy.run_path(str(HERE / "runtime.py"))
OLD, F = PIPE["OLD"], PIPE["F"]
dump, sha, now = FROZEN["dump"], FROZEN["sha"], F["now"]


async def execute(args):
    import torch
    import transformers

    m = FROZEN["verify"](args.input)
    args.output.mkdir(parents=True, exist_ok=False)
    try:
        dump(
            args.output / "execution.json",
            dict(
                at=now(),
                device=args.device,
                python=platform.python_version(),
                manifest_sha256=sha(args.input / "manifest.json"),
                sources=FROZEN["sources"](),
            ),
        )
        cases = json.loads((args.input / "cases.json").read_text())
        refs = json.loads((args.input / "references.json").read_text())
        exposed = json.loads((args.input / "admission-input.json").read_text())
        model, tok, eos = OLD["load_model"](args.device)
        R = runpy.run_path(str(HERE.parent / "structured_correction/runtime.py"))
        before = R["weight_digest"](model)
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
        admission = runpy.run_path(str(HERE / "admission.py"))["admission"]
        dump(
            args.output / "mechanical-admission.json",
            admission(
                model,
                tok,
                exposed["case"],
                exposed["native"],
                eos,
                layer=m["layer"],
                rank=m["rank"],
            ),
        )
        with InputTokenBudget(
            args.output / "budget.jsonl",
            max_usd=m["api_cap_usd"],
            usd_per_million=m["usd_per_million"],
        ) as budget:
            scorer = JevScorer(load_api_key(args.key_file), model="jev-1.13.0", max_retries=0)
            try:
                feedback = F["Feedback"](scorer, budget, args.output, delay=m["api_delay_seconds"])
                runner = PIPE["Runner"](model, tok, eos, m, args.output, feedback)
                train = [c for c in cases if c["split"] == "train"]
                dev = [c for c in cases if c["split"] == "development"]
                test = [c for c in cases if c["split"] == "test"]
                await runner.drafts(train + dev, refs)
                adapters = runner.train(train, dev, refs)
                selected_before = {
                    f"{name}/{seed}": R["weight_digest"](a) for (name, seed), a in adapters.items()
                }
                dump(args.output / "adapter-bindings.json", dict(at=now(), before=selected_before))
                await runner.drafts(test, refs)
                runner.test(test, adapters)
                FROZEN["N"]["coverage"](cases, runner.rows, m)
                after = R["weight_digest"](model)
                selected_after = {
                    f"{name}/{seed}": R["weight_digest"](a) for (name, seed), a in adapters.items()
                }
                if (
                    before != after
                    or selected_before != selected_after
                    or budget.unresolved
                    or any(p.grad is not None or p.requires_grad for p in model.parameters())
                    or len(runner.rows) != m["planned_outputs"]
                ):
                    raise ValueError(
                        "Frozen parameter, output or resolved-charge integrity failure"
                    )
                dump(
                    args.output / "complete.json",
                    dict(
                        at=now(),
                        outputs=len(runner.rows),
                        backbone_before=before,
                        backbone_after=after,
                        adapters_before=selected_before,
                        adapters_after=selected_after,
                        charged_input_tokens=budget.charged_tokens,
                        seconds=time.monotonic() - runner.started,
                    ),
                )
            finally:
                await scorer.__aexit__(None, None, None)
    except BaseException as exc:
        dump(args.output / "failed.json", dict(error_type=type(exc).__name__, at=now()))
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "verify", "run"))
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--device", choices=("cuda", "mps", "cpu"), default="cuda")
    parser.add_argument("--key-file", type=Path, default=Path.home() / ".typesafe.ai/jev")
    args = parser.parse_args()
    if args.command == "prepare":
        if args.output is None:
            parser.error("prepare requires --output")
        FROZEN["prepare"](args.output)
        print(json.dumps(dict(prepared=True, manifest_sha256=sha(args.output / "manifest.json"))))
    elif args.command == "verify":
        if args.input is None:
            parser.error("verify requires --input")
        FROZEN["verify"](args.input)
        print(json.dumps(dict(verified=True)))
    else:
        if args.input is None or args.output is None:
            parser.error("run requires --input and --output")
        asyncio.run(execute(args))


if __name__ == "__main__":
    main()
