"""Bounded R28 data collection; grading is deliberately absent from this worker."""

import argparse
import asyncio
import json
import platform
import runpy
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
C = runpy.run_path(str(HERE / "common.py"))
F = runpy.run_path(str(HERE / "feedback.py"))
A = runpy.run_path(str(HERE.parent / "selective_benchmarks/admission.py"))


async def run(folder, output, key_file):
    import torch
    import transformers
    from huggingface_hub import snapshot_download
    from safetensors.torch import load_file
    from transformers import AutoModelForCausalLM, AutoTokenizer

    from jev_guided_decoding.experiment_budget import InputTokenBudget
    from jev_guided_decoding.jev import JevScorer, load_api_key

    m = json.loads((folder / "manifest.json").read_text())
    A["verify_bindings"](folder, m)
    if m["protocol"] != "r28-routing-feedback-v1" or m["model"] != A["MODELS"]["granite_4_0_1b"]:
        raise ValueError("Changed inference profile")
    C["admit_cost"](m["prior_conservative_usd"], m["reserve_usd"], m["cumulative_cap_usd"])
    if not torch.cuda.is_available():
        raise ValueError("CUDA required")
    cases = json.loads((folder / "cases.json").read_text())
    for c in cases:
        C["validate_case"](c)
    if len(cases) != m["eligible_cases"]:
        raise ValueError("Changed eligible cohort")
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    C["dump"](
        output / "start.json",
        dict(at=F["now"](), manifest_sha256=C["sha"](folder / "manifest.json")),
    )

    def deadline():
        if time.monotonic() - started >= m["max_seconds"]:
            raise TimeoutError("R28 deadline: preserve missing work without scoring")

    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    runtime = runpy.run_path(str(HERE / "runtime.py"))
    old = runpy.run_path(str(HERE.parent / "gated_repair_fp32/runtime.py"))
    config = m["model"]
    local = Path(
        snapshot_download(
            config["id"],
            revision=config["revision"],
            allow_patterns=["*.json", "*.jinja", "*.txt", "*.safetensors"],
        )
    )
    tok = AutoTokenizer.from_pretrained(local, trust_remote_code=False)
    model = (
        AutoModelForCausalLM.from_pretrained(
            local, trust_remote_code=False, dtype=torch.float32, attn_implementation="sdpa"
        )
        .to("cuda")
        .eval()
    )
    model.requires_grad_(False)
    eos = model.generation_config.eos_token_id
    eos = [eos] if isinstance(eos, int) else eos
    before = old["weight_digest"](model)
    branch = runtime["BASE"]["B"]["Repair"](model.config.hidden_size).to("cuda")
    branch.load_state_dict(load_file(str(folder / m["checkpoints"]["live"]["file"]), device="cuda"))
    branch.eval().requires_grad_(False)
    C["dump"](
        output / "hardware.json",
        dict(
            at=F["now"](),
            gpu=torch.cuda.get_device_name(),
            python=platform.python_version(),
            torch=torch.__version__,
            transformers=transformers.__version__,
            original_weights_sha256=before,
            eos_ids=eos,
            profile=config,
            files={p.name: C["sha"](p) for p in local.iterdir() if p.is_file()},
            load_seconds=time.monotonic() - started,
        ),
    )
    # Exposed fixture, not a held-out benchmark answer or quality-directed tuning.
    fixture = tok.apply_chat_template(
        [dict(role="user", content="Return only the word hello.")],
        tokenize=True,
        add_generation_prompt=True,
    )
    admission = old["admission"](model, tok, fixture, eos, m["layer"])
    kwargs = dict(limit=8, eos=eos, seed=m["seed"], deadline=deadline)
    plain, plain_work = runtime["generate"](model, tok, fixture, **kwargs)
    observed, observed_work = runtime["generate"](model, tok, fixture, observe=True, **kwargs)
    if plain["generated_token_ids"] != observed["generated_token_ids"]:
        raise ValueError("Native observation changed tokens")
    C["dump"](
        output / "admission.json",
        dict(
            numerical=admission,
            plain=plain,
            observed=observed,
            work=[plain_work, observed_work],
            passed=True,
        ),
    )
    encoded = {
        c["id"]: tok.apply_chat_template(
            [dict(role="user", content=c["prompt"])], tokenize=True, add_generation_prompt=True
        )
        for c in cases
    }
    if any(len(p) > 16384 for p in encoded.values()):
        raise ValueError("Input overflow; no truncation allowed")
    native = {}

    def answer(case, arm, *, gate=None):
        deadline()
        ident = case["id"]
        prefix = (
            encoded[ident]
            if arm == "native"
            else C["BASE"]["repair_prefix"](
                tok, encoded[ident], native[ident]["generated_token_ids"], "instruction"
            )
        )
        F["append"](output / "jobs.jsonl", dict(event="start", id=ident, arm=arm, at=F["now"]()))
        row, work = runtime["generate"](
            model,
            tok,
            prefix,
            observe=arm == "native",
            limit=m["limit"],
            eos=eos,
            seed=m["seed"],
            deadline=deadline,
            adapter=None if arm == "native" else branch,
            gate=0.5 if gate is None else gate,
            layer=m["layer"],
            kind="instruction",
            thinking=False,
        )
        result = dict(
            id=ident,
            arm=arm,
            gate=gate,
            prompt_sha256=C["digest"](case["prompt"]),
            at=F["now"](),
            work=work,
            **row,
        )
        F["append"](output / "outputs.jsonl", result)
        F["append"](output / "jobs.jsonl", dict(event="finish", id=ident, arm=arm, at=F["now"]()))
        print(
            json.dumps(
                dict(
                    id=ident,
                    arm=arm,
                    tokens=len(row["generated_token_ids"]),
                    seconds=work["seconds"],
                )
            ),
            flush=True,
        )
        return result

    by_id = {c["id"]: c for c in cases}
    ordering = C["order"](by_id, "generation/2800")
    for ident in ordering:
        native[ident] = answer(by_id[ident], "native")
    probabilities = {}
    with InputTokenBudget(
        output / "budget.jsonl", max_usd=m["jev_cap"], usd_per_million=m["usd_per_million"]
    ) as budget:
        async with JevScorer(
            load_api_key(key_file=key_file), model=m["jev"], max_retries=0
        ) as scorer:
            feedback = F["Feedback"](scorer, budget, output)
            for ident in ordering:
                deadline()
                probabilities[ident] = await feedback.score(
                    by_id[ident], native[ident]["text"].strip() or "(empty response)"
                )
                if probabilities[ident] is None:
                    raise RuntimeError("Missing Jev judgment; no substitute")
                print(json.dumps(dict(phase="feedback", completed=len(probabilities))), flush=True)
        if budget.unresolved or budget.max_charged:
            raise RuntimeError("Unresolved API charge")
        C["dump"](
            output / "api-summary.json",
            dict(
                charged_tokens=budget.charged_tokens,
                usd=budget.charged_tokens * m["usd_per_million"] / 1e6,
                unresolved=0,
                max_charged=0,
                calls=len(probabilities),
            ),
        )
    plan = C["make_plan"](
        ordering, probabilities, {i: r["mean_log_probability"] for i, r in native.items()}
    )
    C["dump"](output / "selection.json", dict(at=F["now"](), plan=plan))
    donors = {i: d for block in plan["blocks"] for i, d in block["donors"].items()}
    for ident in ordering:
        answer(by_id[ident], "constant", gate=0.5)
        if ident in donors:
            arms = C["order"](["live", "shuffled"], f"arm/{ident}/2803")
            for arm in arms:
                p = probabilities[ident if arm == "live" else donors[ident]]
                answer(by_id[ident], arm, gate=1 - p)
    after = old["weight_digest"](model)
    if before != after:
        raise ValueError("Base weights changed")
    C["dump"](
        output / "completion.json",
        dict(
            at=F["now"](),
            weights_unchanged=True,
            weights_sha256=after,
            seconds=time.monotonic() - started,
            cases=len(cases),
            expected_outputs=len(C["required_outputs"](plan)),
        ),
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--folder", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--key-file", type=Path, required=True)
    args = p.parse_args()
    asyncio.run(run(args.folder, args.output, args.key_file))
