"""R27 bounded serial benchmark worker; references stay off the inference host."""

import argparse
import asyncio
import gc
import json
import platform
import runpy
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
A = runpy.run_path(str(HERE.parent / "selective_benchmarks/admission.py"))
C, F = A["C"], A["F"]
K = runpy.run_path(str(HERE / "contract.py"))
append, now = F["append"], F["now"]
MODELS, repair_case, verify_bindings = A["MODELS"], A["repair_case"], A["verify_bindings"]


async def run(folder, output, key_file):
    import torch
    import transformers
    from huggingface_hub import snapshot_download
    from safetensors.torch import load_file
    from transformers import AutoModelForCausalLM, AutoTokenizer

    from jev_guided_decoding.experiment_budget import InputTokenBudget
    from jev_guided_decoding.jev import JevScorer, load_api_key

    m = json.loads((folder / "manifest.json").read_text())
    verify_bindings(folder, m)
    if m["models"] != MODELS or m["protocol"] != "r27-benchmark-execution-v2":
        raise ValueError("Admission settings changed")
    cases = json.loads((folder / "cases.json").read_text())
    for case in cases:
        C["validate_case"](case)
    if not torch.cuda.is_available():
        raise ValueError("CUDA admission required")
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    C["dump"](
        output / "start.json", dict(at=now(), manifest_sha256=C["sha"](folder / "manifest.json"))
    )
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    runtime = runpy.run_path(str(HERE / "runtime.py"))
    original = runpy.run_path(str(HERE.parent / "gated_repair_fp32/runtime.py"))
    serial_ids = [
        c["id"] for c in sorted(cases, key=lambda c: C["digest"]("serial/" + c["id"]))[:3]
    ]

    def deadline():
        if time.monotonic() - started >= m["max_seconds"]:
            raise TimeoutError("Admission deadline; unfinished outputs remain missing")

    for name, config in m["models"].items():
        deadline()
        tick = time.monotonic()
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
                local,
                trust_remote_code=False,
                dtype=getattr(torch, config["dtype"]),
                attn_implementation="sdpa",
            )
            .to("cuda")
            .eval()
        )
        model.requires_grad_(False)
        eos = model.generation_config.eos_token_id
        eos = [eos] if isinstance(eos, int) else eos
        encoded = {
            c["id"]: tok.apply_chat_template(
                [dict(role="user", content=c["prompt"])],
                tokenize=True,
                add_generation_prompt=True,
                **({"enable_thinking": True} if config["thinking"] else {}),
            )
            for c in cases
        }
        if any(len(ids) > m["input_limit"] for ids in encoded.values()):
            raise ValueError("Admission input limit; no truncation")
        before = original["weight_digest"](model)
        C["dump"](
            output / (name + "-hardware.json"),
            dict(
                at=now(),
                profile=config,
                parameters=sum(p.numel() for p in model.parameters()),
                gpu=torch.cuda.get_device_name(),
                python=platform.python_version(),
                torch=torch.__version__,
                transformers=transformers.__version__,
                original_weights_sha256=before,
                eos_ids=eos,
                load_seconds=time.monotonic() - tick,
                files={p.name: C["sha"](p) for p in sorted(local.iterdir()) if p.is_file()},
            ),
        )
        adapters = {}
        if name == "granite_4_0_1b":
            for mode, item in m["checkpoints"].items():
                branch = runtime["B"]["Repair"](model.config.hidden_size).to("cuda")
                branch.load_state_dict(load_file(str(folder / item["file"]), device="cuda"))
                branch.eval().requires_grad_(False)
                adapters[mode] = branch
            first = encoded[cases[0]["id"]]
            admission = original["admission"](model, tok, first, eos, m["layer"])
            comparisons = [
                original["comparison"](model, encoded[c["id"]], adapters["live"], 0.7, m["layer"])
                for c in cases[:3]
            ]
            if any(not r["allclose"] or not r["argmax_equal"] for r in comparisons):
                C["dump"](output / "failed-cache-admission.json", comparisons)
                raise ValueError("Selected adapter cache admission failed")
            C["dump"](
                output / "cache-admission.json", dict(initial=admission, selected=comparisons)
            )
        ordering = sorted(cases, key=lambda c: (len(encoded[c["id"]]), c["id"]))
        native = {}

        def answer(
            group,
            arm,
            *,
            limit=None,
            adapter=None,
            gate=0.5,
            prefix=None,
            name=name,
            encoded=encoded,
            model=model,
            tok=tok,
            config=config,
            eos=eos,
        ):
            deadline()
            batch_id = name + "/" + arm + "/" + str(time.monotonic_ns())
            ids = [prefix] if prefix is not None else [encoded[c["id"]] for c in group]
            append(
                output / "jobs.jsonl",
                dict(
                    event="start",
                    model=name,
                    arm=arm,
                    ids=[c["id"] for c in group],
                    batch_id=batch_id,
                    at=now(),
                ),
            )
            rows, work = runtime["generate_batch"](
                model,
                tok,
                ids,
                limit=limit or config["max_new_tokens"],
                eos=eos,
                seed=K["case_seed"](group[0]["id"], m["seed"]),
                kind=group[0]["format"],
                thinking=config["thinking"],
                profile=config["profile"],
                adapter=adapter,
                gate=gate,
                layer=m["layer"],
                deadline=deadline,
            )
            append(
                output / "batches.jsonl",
                dict(model=name, arm=arm, batch_id=batch_id, at=now(), **work),
            )
            results = []
            for c, row in zip(group, rows, strict=True):
                final, status = runtime["final_text"](row["text"], config["thinking"])
                result = dict(
                    id=c["id"],
                    task=c["task"],
                    family=c["family"],
                    seed=K["case_seed"](c["id"], m["seed"]),
                    model=name,
                    arm=arm,
                    batch_id=batch_id,
                    prompt_sha256=C["digest"](c["prompt"]),
                    at=now(),
                    final=final,
                    status=status,
                    gate=gate if adapter is not None else None,
                    **row,
                )
                append(output / "outputs.jsonl", result)
                results.append(result)
            append(
                output / "jobs.jsonl",
                dict(
                    event="finish",
                    model=name,
                    arm=arm,
                    ids=[c["id"] for c in group],
                    batch_id=batch_id,
                    at=now(),
                ),
            )
            print(
                json.dumps(dict(model=name, arm=arm, cases=len(group), seconds=work["seconds"])),
                flush=True,
            )
            return results

        answer(ordering[:1], "warmup", limit=8)
        for offset in range(0, len(ordering), m["batch_size"]):
            for row in answer(ordering[offset : offset + m["batch_size"]], "native"):
                native[row["id"]] = row
        for c in cases:
            if name == "granite_4_0_1b" and c["id"] in serial_ids:
                answer([c], "serial_probe")
        if name == "granite_4_0_1b":
            # A separate extra-pass baseline: no Jev score or adapter affects this path.
            for c in cases:
                row = native[c["id"]]
                prefix = C["repair_prefix"](
                    tok, row["prompt_token_ids"], row["generated_token_ids"], c["format"]
                )
                answer([c], "self_refine", limit=m["repair_limit"], prefix=prefix)
            scores = {}
            with InputTokenBudget(
                output / "budget.jsonl", max_usd=m["jev_cap"], usd_per_million=m["usd_per_million"]
            ) as budget:
                async with JevScorer(
                    load_api_key(key_file=key_file), model=m["jev"], max_retries=0
                ) as scorer:
                    feedback = F["Feedback"](scorer, budget, output)
                    for c in cases:
                        deadline()
                        scores[c["id"]] = await feedback.score(
                            c, native[c["id"]]["final"] or "(empty response)"
                        )
                C["dump"](
                    output / "api-summary.json",
                    dict(
                        charged_tokens=budget.charged_tokens,
                        usd=budget.charged_tokens * m["usd_per_million"] / 1e6,
                        unresolved=len(budget.unresolved),
                        max_charged=len(budget.max_charged),
                    ),
                )
            donors = {}
            for task in sorted({c["task"] for c in cases}):
                ids = sorted(c["id"] for c in cases if c["task"] == task)
                donors.update({ident: ids[(i + 1) % len(ids)] for i, ident in enumerate(ids)})
            C["dump"](output / "donors.json", donors)
            for c in cases:
                row = native[c["id"]]

                def repair(arm, gate, c=c, row=row, tok=tok, adapters=adapters, answer=answer):
                    prefix = C["repair_prefix"](
                        tok, row["prompt_token_ids"], row["generated_token_ids"], c["format"]
                    )
                    branch = (
                        None
                        if arm == "blind"
                        else adapters["constant" if arm == "constant" else "live"]
                    )
                    return answer(
                        [c], arm, limit=m["repair_limit"], adapter=branch, gate=gate, prefix=prefix
                    )[0]

                for arm, selection in repair_case(
                    row, scores[c["id"]], scores[donors[c["id"]]], repair
                ):
                    chosen = selection.pop("output")
                    append(
                        output / "decisions.jsonl",
                        dict(
                            id=c["id"],
                            arm=arm,
                            selected_arm=chosen["arm"],
                            selected_tokens_sha256=C["digest"](
                                json.dumps(chosen["generated_token_ids"])
                            ),
                            donor_id=donors[c["id"]],
                            at=now(),
                            **selection,
                        ),
                    )
        after = original["weight_digest"](model)
        if before != after:
            raise ValueError("Original weights changed")
        C["dump"](
            output / (name + "-complete.json"),
            dict(at=now(), weights_unchanged=True, weights_sha256=after),
        )
        adapters.clear()
        del answer
        if name == "granite_4_0_1b":
            del repair
        del model, tok
        gc.collect()
        torch.cuda.empty_cache()
    C["dump"](
        output / "completion.json",
        dict(
            at=now(),
            seconds=time.monotonic() - started,
            models=list(m["models"]),
            cases=len(cases),
            fresh_test_cases=sum(c["split"] == "test" for c in cases),
        ),
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--freeze", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--key-file", type=Path, required=True)
    a = p.parse_args()
    asyncio.run(run(a.freeze, a.output, a.key_file))
