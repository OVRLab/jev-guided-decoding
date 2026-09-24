"""R26-A source/data freeze and exposed-case inference admission; no fresh test."""

import argparse
import asyncio
import gc
import gzip
import json
import platform
import re
import runpy
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
C = runpy.run_path(str(HERE / "common.py"))
F = runpy.run_path(str(HERE / "feedback.py"))
append, now = F["append"], F["now"]
ARMS = ("live", "blind", "constant", "live_constant", "inverted", "shuffled")
MODELS = {
    "granite_4_0_1b": dict(
        id="ibm-granite/granite-4.0-1b",
        revision="6a7381ba1f54d684ff508d991aeb7dc580157103",
        dtype="float32",
        thinking=False,
        max_new_tokens=2048,
        profile=dict(do_sample=False),
    ),
    "granite_4_2_3b": dict(
        id="ibm-granite/granite-4.2-3b",
        revision="e459acceac81e5fe67c07d9cfc72329a332e7eb1",
        dtype="bfloat16",
        thinking=True,
        max_new_tokens=8192,
        profile=dict(do_sample=True, temperature=1.0, top_p=0.95, top_k=0),
    ),
    "qwen3_4b_instruct": dict(
        id="Qwen/Qwen3-4B-Instruct-2507",
        revision="cdbee75f17c01a7cc42f958dc650907174af0554",
        dtype="bfloat16",
        thinking=False,
        max_new_tokens=16384,
        profile=dict(do_sample=True, temperature=0.7, top_p=0.8, top_k=20, min_p=0.0),
    ),
}


def convert(old, ref):
    if old["id"] != ref["id"] or C["digest"](old["prompt"]) != ref["prompt_sha256"]:
        raise ValueError("Original question/reference binding mismatch")
    kind = "instruction" if ref["kind"] == "ifbench" else ref["kind"]
    prompt = old["prompt"]
    if kind in ("choice", "number"):
        body, separator, _ = prompt.rpartition("\n\nReason through the problem")
        if not separator:
            raise ValueError("Missing known output-contract instruction")
        finish = (
            "Finish with a separate line starting Final: followed by the selected letter."
            if kind == "choice"
            else "Finish with a separate line starting #### followed by your numeric answer."
        )
        prompt = body + "\n\nSolve the problem. " + finish
    case = dict(
        id=old["id"],
        task=old["task"],
        family=old.get("family", old["task"]),
        prompt=prompt,
        format=kind,
        origin_id=old.get("origin_id", old.get("origin", old["id"])),
        cluster=old["id"],
        split="development",
    )
    C["validate_case"](case)
    new_ref = ref | {"prompt_sha256": C["digest"](prompt)}
    if kind == "choice":
        options = re.findall(r"(?m)^[A-Z]\. (.+)$", body)
        if len(options) != ref["choices"]:
            raise ValueError("Option extraction mismatch")
        new_ref = {k: v for k, v in new_ref.items() if k != "choices"} | {"options": options}
    return case, new_ref


def strength(arm, p, donor_p):
    C["probability"](p)
    if arm == "live":
        return 1 - p
    if arm in ("blind", "constant", "live_constant"):
        return 0.5
    if arm == "inverted":
        return p
    if arm == "shuffled":
        return 1 - C["probability"](0.5 if donor_p is None else donor_p)
    raise ValueError("Unknown selective arm")


def repair_case(native, probability, donor_probability, generate):
    rows = []
    for arm in ARMS:

        def repair(_gate, arm=arm):
            return generate(arm, strength(arm, probability, donor_probability))

        row = C["select"](native, probability, repair)
        row["gate"] = (
            strength(arm, probability, donor_probability)
            if row["repair_executed"] and arm != "blind"
            else None
        )
        rows.append((arm, row))
    return rows


def verify_bindings(folder, manifest):
    for group, base in [("sources", ROOT), ("datasets", folder)]:
        for name, expected in manifest[group].items():
            p = Path(name)
            if p.is_absolute() or ".." in p.parts or C["sha"](base / p) != expected:
                raise ValueError("Source/data binding mismatch: " + name)
    for item in manifest["checkpoints"].values():
        p = Path(item["file"])
        if p.is_absolute() or ".." in p.parts or C["sha"](folder / p) != item["sha256"]:
            raise ValueError("Checkpoint binding mismatch")


def source_hashes():
    paths = [
        *HERE.glob("*.py"),
        ROOT / "research/selective-benchmark-admission-plan.md",
        ROOT / "research/iterations/public_critic.py",
        ROOT / "research/diagnostics/public_baseline_readout.py",
        ROOT / "research/iterations/benchmark_baseline/common.py",
        ROOT / "research/iterations/learned_feedback/bridge.py",
        ROOT / "research/iterations/adaptive_attention/attention.py",
        ROOT / "research/iterations/gated_repair_fp32/runtime.py",
        *list((ROOT / "research/iterations/gated_repair").glob("*.py")),
        *list((ROOT / "src").rglob("*.py")),
        ROOT / "pyproject.toml",
        ROOT / "uv.lock",
    ]
    return {str(p.relative_to(ROOT)): C["sha"](p) for p in sorted(set(paths))}


def prepare(folder):
    source_dirty = bool(
        subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()
    )
    folder.mkdir(parents=True, exist_ok=False)
    old = ROOT / "research/protocols/public-baseline-v1"
    r25 = ROOT / "research/protocols/gated-repair-retry-v4"
    candidates = []
    origins = {}
    for base, ref_file in [(old, "references.json"), (r25, "development-references.json")]:
        cases = json.loads((base / "cases.json").read_text())
        refs = {r["id"]: r for r in json.loads((base / ref_file).read_text())}
        for name in ["cases.json", ref_file]:
            origins[str((base / name).relative_to(ROOT))] = C["sha"](base / name)
        for c in cases:
            if c["id"] in refs and (base == r25 or c["task"] != "gsm8k_train"):
                candidates.append(convert(c, refs[c["id"]]))
    selected = []
    for task, family in sorted({(c["task"], c["family"]) for c, _ in candidates}):
        n = {"gsm8k": 10, "arc": 10, "mmlu_pro": 1, "musr": 2, "ifbench": 10}[task]
        group = [p for p in candidates if (p[0]["task"], p[0]["family"]) == (task, family)]
        selected += sorted(group, key=lambda p: C["digest"]("r26-admission/" + p[0]["id"]))[:n]
    if len(selected) != 50 or len({c["id"] for c, _ in selected}) != 50:
        raise ValueError("Admission cohort mismatch")
    C["dump"](folder / "cases.json", [c for c, _ in selected])
    C["dump"](folder / "references.json", [r for _, r in selected])
    report = ROOT / "reports/2026-09-23-gated-repair"
    analysis = json.loads((report / "analysis.json").read_text())
    checkpoints = {}
    for mode in ("live", "constant"):
        item = analysis["selection"]["models"][mode + "/2501"]
        blob = gzip.decompress(
            (report / "artifacts/gated-repair-retry-v4" / (item["file"] + ".gz")).read_bytes()
        )
        destination = folder / item["file"]
        destination.write_bytes(blob)
        if C["sha"](destination) != item["sha256"]:
            raise ValueError("Selected checkpoint corrupted")
        checkpoints[mode] = item
    C["dump"](
        folder / "manifest.json",
        dict(
            protocol="r26-selective-admission-v1",
            at=now(),
            sources=source_hashes(),
            datasets={n: C["sha"](folder / n) for n in ["cases.json", "references.json"]},
            origins=origins,
            checkpoints=checkpoints,
            models=MODELS,
            seed=2601,
            batch_size=4,
            repair_limit=2048,
            input_limit=16384,
            layer=19,
            max_seconds=9000,
            jev="jev-1.13.0",
            jev_cap=0.15,
            usd_per_million=0.042,
            prior_spend_usd=42.62708084740686,
            cumulative_cap_usd=110,
            stage_reserve_usd=6,
            scope="exposed development admission only",
            source_revision=subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            source_dirty=source_dirty,
        ),
    )


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
    if m["models"] != MODELS or m["protocol"] != "r26-selective-admission-v1":
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
        c["id"] for c in sorted(cases, key=lambda c: C["digest"]("serial/" + c["id"]))[:8]
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
                seed=m["seed"],
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
            if c["id"] in serial_ids:
                answer([c], "serial_probe")
        if name == "granite_4_0_1b":
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
            fresh_test_cases=0,
        ),
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--prepare", type=Path)
    p.add_argument("--freeze", type=Path)
    p.add_argument("--output", type=Path)
    p.add_argument("--key-file", type=Path)
    a = p.parse_args()
    if a.prepare:
        prepare(a.prepare)
    else:
        asyncio.run(run(a.freeze, a.output, a.key_file))
