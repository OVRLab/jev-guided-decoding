"""R27 derived continuation; frozen generation kernel, no new provider requests."""

import argparse
import asyncio
import gc
import json
import platform
import runpy
import time
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
A = runpy.run_path(str(HERE.parent / "selective_benchmarks/admission.py"))
C, F = A["C"], A["F"]
FROZEN = HERE.parent / "benchmark_execution_v2"
K = runpy.run_path(str(FROZEN / "contract.py"))
S = runpy.run_path(str(HERE / "state.py"))
AUDIT = runpy.run_path(str(ROOT / "research/diagnostics/benchmark_execution_v3_audit.py"))
append, now = F["append"], F["now"]
MODELS, repair_case, verify_bindings = A["MODELS"], A["repair_case"], A["verify_bindings"]


async def run(folder, parent, output):
    import torch
    import transformers
    from huggingface_hub import snapshot_download
    from safetensors.torch import load_file
    from transformers import AutoModelForCausalLM, AutoTokenizer

    m = json.loads((folder / "manifest.json").read_text())
    verify_bindings(folder, m)
    if m["models"] != MODELS or m["protocol"] != "r27-benchmark-execution-v2":
        raise ValueError("Admission settings changed")
    cases = json.loads((folder / "cases.json").read_text())
    for case in cases:
        C["validate_case"](case)
    if not torch.cuda.is_available():
        raise ValueError("CUDA admission required")
    prior_rows, _, _, _ = S["journal"](parent)
    AUDIT["check_numerical"](json.loads((parent / "cache-admission.json").read_text()))
    prior_batches = {r["batch_id"]: r for r in S["lines"](parent / "batches.jsonl")}
    for row in prior_rows.values():
        AUDIT["check_batch"](prior_batches[row["batch_id"]], [row])
    native_prior = {
        r["id"]: r
        for r in prior_rows.values()
        if r["model"] == "granite_4_0_1b" and r["arm"] == "native"
    }
    if set(native_prior) != {c["id"] for c in cases}:
        raise ValueError("Original native answers incomplete")
    # Validates exact requests against native drafts, receipts and every charge.
    AUDIT["check_delivery"](parent, {c["id"]: c for c in cases}, native_prior, m)
    scores = {
        r["id"]: r["actual_probability_correct"] for r in S["lines"](parent / "feedback.jsonl")
    }
    state = S["prepare"](
        parent,
        output,
        manifest_sha256=C["sha"](folder / "manifest.json"),
        max_seconds=m["max_seconds"],
    )
    S["dump"](
        output / "recovery-sources.json",
        {
            str(p.relative_to(ROOT)): C["sha"](p)
            for p in [
                HERE / "run.py",
                HERE / "state.py",
                ROOT / "research/benchmark-interruption-recovery-v1.md",
            ]
        },
    )
    started = time.monotonic()
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    runtime = runpy.run_path(str(FROZEN / "runtime.py"))
    original = runpy.run_path(str(HERE.parent / "gated_repair_fp32/runtime.py"))
    serial_ids = [
        c["id"] for c in sorted(cases, key=lambda c: C["digest"]("serial/" + c["id"]))[:3]
    ]

    def deadline():
        if datetime.now(UTC) >= state.end:
            raise TimeoutError("Admission deadline; unfinished outputs remain missing")

    for name, config in m["models"].items():
        deadline()
        complete = output / (name + "-complete.json")
        if complete.exists():
            certificate = json.loads(complete.read_text())
            hardware = json.loads((output / (name + "-hardware.json")).read_text())
            if (
                not certificate["weights_unchanged"]
                or certificate["weights_sha256"] != hardware["original_weights_sha256"]
            ):
                raise ValueError("Prior weight certificate mismatch")
            existing = [
                r for r in prior_rows.values() if r["model"] == name and r["arm"] == "native"
            ]
            if {r["id"] for r in existing} != {c["id"] for c in cases}:
                raise ValueError("Completed model has missing native outputs")
            if name == "granite_4_0_1b" and len(S["lines"](output / "decisions.jsonl")) != len(
                cases
            ) * len(A["ARMS"]):
                raise ValueError("Completed original model has missing decisions")
            continue
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
        state.hardware(
            name,
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
            numerical = dict(initial=admission, selected=comparisons)
            AUDIT["check_numerical"](numerical)
            S["dump"](output / "recovery-cache-admission.json", numerical)
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
            if len(group) != 1:
                raise ValueError("Continuation is serial only")
            saved = state.cached(
                name, arm, group[0]["id"], ids[0], gate if adapter is not None else None
            )
            if saved is not None:
                AUDIT["check_output"](
                    group[0],
                    saved,
                    tok,
                    config,
                    eos,
                    native_prior[group[0]["id"]] if arm in {*A["ARMS"], "self_refine"} else None,
                )
                return [saved]
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
            donors = {}
            for task in sorted({c["task"] for c in cases}):
                ids = sorted(c["id"] for c in cases if c["task"] == task)
                donors.update({ident: ids[(i + 1) % len(ids)] for i, ident in enumerate(ids)})
            if json.loads((output / "donors.json").read_text()) != donors:
                raise ValueError("Prior donor binding changed")
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
                    state.decision(
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
            seconds=(
                datetime.now(UTC)
                - datetime.fromisoformat(json.loads((output / "start.json").read_text())["at"])
            ).total_seconds(),
            continuation_seconds=time.monotonic() - started,
            interrupted=True,
            models=list(m["models"]),
            cases=len(cases),
            fresh_test_cases=sum(c["split"] == "test" for c in cases),
        ),
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--freeze", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--parent", type=Path, required=True)
    a = p.parse_args()
    asyncio.run(run(a.freeze, a.parent, a.output))
