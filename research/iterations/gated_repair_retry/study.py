"""R25 v4 continuation with bounded explicit-rejection delivery."""

import argparse
import asyncio
import json
import platform
import runpy
import shutil
import time
from pathlib import Path

from jev_guided_decoding.experiment_budget import InputTokenBudget
from jev_guided_decoding.jev import JevScorer, _probability, load_api_key

HERE = Path(__file__).resolve().parent
C = runpy.run_path(str(HERE / "common.py"))
S = runpy.run_path(str(HERE.parent / "gated_repair_fp32/study.py"))
F = runpy.run_path(str(HERE / "feedback.py"))
append, now = S["append"], S["now"]
PREFIXES = (
    "outputs.jsonl",
    "jobs.jsonl",
    "api-requests.jsonl",
    "api-responses.jsonl",
    "api-failures.jsonl",
    "budget.jsonl",
)


def prior_check(prior, m, cases):
    if any(
        (prior / name).exists()
        for name in ("training-steps.jsonl", "selection.json", "completion.json")
    ):
        raise ValueError("Only pre-training continuation is admitted")
    for name, binding in m["prior_files"].items():
        p = prior / name
        if (
            Path(name).name != name
            or p.stat().st_size != binding["bytes"]
            or C["sha"](p) != binding["sha256"]
        ):
            raise ValueError("Predecessor artifact changed")
    old = runpy.run_path(str(HERE.parent / "gated_repair_continue/study.py"))
    v3folder = C["ROOT"] / "research/protocols/gated-repair-continuation-v3"
    v3 = old["C"]["verify"](v3folder)
    if C["sha"](v3folder / "manifest.json") != m["predecessor_manifest_sha256"]:
        raise ValueError("Wrong predecessor manifest")
    old["prior_check"](prior.parent / "prior-v2", v3, cases)
    for name in PREFIXES:
        binding = v3["prior_files"][name]
        import hashlib

        if (
            hashlib.sha256((prior / name).read_bytes()[: binding["bytes"]]).hexdigest()
            != binding["sha256"]
        ):
            raise ValueError("Legacy v2 prefix changed")
    rows = F["records"](prior / "outputs.jsonl")
    index = F["mapping"](rows)
    expected = [c for c in cases if c["split"] in ("train", "development")]
    expected = [c for c in expected if c["split"] == "train"] + [
        c for c in expected if c["split"] == "development"
    ]
    if (
        len(rows) != m["legacy_cases"]
        or [r["id"] for r in rows] != [c["id"] for c in expected[: m["legacy_cases"]]]
        or any(r["arm"] != "native" or r["split"] != "train" for r in rows)
    ):
        raise ValueError("Unexpected prior model jobs")
    jobs = F["records"](prior / "jobs.jsonl")
    for event in ("start", "finish"):
        found = [r["id"] for r in jobs if r["event"] == event]
        if len(found) != m["legacy_cases"] or set(found) != set(index):
            raise ValueError("Incomplete prior native jobs")
    requests = F["mapping"](F["records"](prior / "api-requests.jsonl"))
    receipts = F["mapping"](F["records"](prior / "api-responses.jsonl"))
    failures = F["mapping"](F["records"](prior / "api-failures.jsonl"))
    if (
        set(requests) != set(index)
        or set(receipts) != (set(index) - set(m["legacy_missing_ids"]))
        or set(failures) != set(m["legacy_missing_ids"])
    ):
        raise ValueError("Unexpected prior provider coverage")
    ledger = F["records"](prior / "budget.jsonl")
    settled = {r["id"]: r["input_tokens"] for r in ledger if r["event"] == "settle"}
    for case in expected[: m["legacy_cases"]]:
        ident = case["id"]
        row = index[ident]
        req = requests[ident]
        if row["prompt_sha256"] != C["digest"](case["prompt"]) or req["payload"] != C[
            "feedback_payload"
        ](case, row["text"] or "(empty response)"):
            raise ValueError("Prior input binding mismatch")
        if ident in receipts:
            r = receipts[ident]
            if (
                r["reservation"] != req["reservation"]
                or r["model"] != m["jev"]
                or r["raw"]["model"] != m["jev"]
                or r["attempts"] != 1
                or r["probability_correct"] != _probability(r["raw"]["answers"], "correct")
                or r["raw"]["usage"]
                != {"input_tokens": r["input_tokens"], "output_tokens": r["output_tokens"]}
                or settled[r["reservation"]] != r["input_tokens"]
            ):
                raise ValueError("Prior receipt mismatch")
    return index


class Runner(S["Runner"]):
    def __init__(self, *args):
        super().__init__(*args)
        self.native = F["mapping"](F["records"](self.output / "outputs.jsonl"))
        self.started_jobs = {
            (r["id"], r["arm"])
            for r in F["records"](self.output / "jobs.jsonl")
            if r["event"] == "start"
        }
        self.feedback = F["Feedback"](self.scorer, self.budget, self.output)

    def answer(self, case, arm, ids, **kwargs):
        key = case["id"], arm
        if key in self.started_jobs:
            raise ValueError("Refused duplicate model dispatch")
        self.started_jobs.add(key)
        return super().answer(case, arm, ids, **kwargs)

    async def drafts(self, cases):
        for case in cases:
            C["validate_case"](case)
            self.deadline()
            ids = self.tok.apply_chat_template(
                [dict(role="user", content=case["prompt"])],
                tokenize=True,
                add_generation_prompt=True,
            )
            native = self.native.get(case["id"])
            if native is None:
                native = self.answer(case, "native", ids)
            else:
                tokens = native["generated_token_ids"]
                body = tokens[:-1] if tokens[-1] in self.eos else tokens
                if (
                    native["prompt_token_ids"] != ids
                    or self.tok.decode(body, skip_special_tokens=False) != native["text"]
                ):
                    raise ValueError("Reused token provenance mismatch")
            self.deadline()
            actual = await self.feedback.score(case, native["text"] or "(empty response)")
            value = F["effective"](actual)
            append(
                self.output / "feedback-availability.jsonl",
                dict(
                    id=case["id"],
                    actual_probability_correct=actual,
                    effective_probability_correct=value,
                    source="jev" if actual is not None else "missing_neutral",
                    at=now(),
                ),
            )
            prefix = C["repair_prefix"](self.tok, ids, native["generated_token_ids"])
            if len(prefix) > self.m["input_limit"]:
                raise ValueError("Repair context exceeds admission limit")
            self.prepared[case["id"]] = dict(native=native, p=value, actual_p=actual, prefix=prefix)

    def test(self, cases, adapters):
        donors = C["donors"](cases)
        C["dump"](self.output / "donors.json", donors)
        for case in cases:
            item = self.prepared[case["id"]]
            self.answer(case, "blind", item["prefix"])
            prefix = C["repair_prefix"](
                self.tok,
                item["native"]["prompt_token_ids"],
                item["native"]["generated_token_ids"],
                probability=item["actual_p"],
            )
            self.answer(case, "text", prefix)
            for seed in self.m["seeds"]:
                self.answer(
                    case,
                    f"constant/{seed}",
                    item["prefix"],
                    adapter=adapters["constant", seed],
                    gate=0.5,
                )
                for name, gate in [
                    ("live", 1 - item["p"]),
                    ("shuffled", 1 - self.prepared[donors[case["id"]]]["p"]),
                    ("inverted", item["p"]),
                ]:
                    self.answer(
                        case,
                        f"{name}/{seed}",
                        item["prefix"],
                        adapter=adapters["live", seed],
                        gate=gate,
                    )


async def run(folder, output, prior, key_file):
    import torch
    import transformers
    from huggingface_hub import snapshot_download
    from transformers import AutoModelForCausalLM, AutoTokenizer

    m = C["verify"](folder)
    cases = json.loads((folder / "cases.json").read_text())
    prior_check(prior, m, cases)
    if not torch.cuda.is_available():
        raise ValueError("CUDA L40S required")
    output.mkdir(parents=True, exist_ok=False)
    for name in PREFIXES:
        shutil.copyfile(prior / name, output / name)
    C["dump"](
        output / "predecessor.json",
        dict(manifest_sha256=m["predecessor_manifest_sha256"], files=m["prior_files"]),
    )
    started = time.monotonic()
    C["dump"](
        output / "start.json", dict(at=now(), manifest_sha256=C["sha"](folder / "manifest.json"))
    )
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    local = Path(
        snapshot_download(
            m["model"],
            revision=m["revision"],
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
        .requires_grad_(False)
    )
    eos = model.generation_config.eos_token_id
    eos = [eos] if isinstance(eos, int) else eos
    runtime = runpy.run_path(str(HERE.parent / "gated_repair_fp32/runtime.py"))
    before = runtime["weight_digest"](model)
    if before != json.loads((prior / "hardware.json").read_text())["original_weights_sha256"]:
        raise ValueError("Backbone differs from reused drafts")
    C["dump"](
        output / "hardware.json",
        dict(
            at=now(),
            gpu=torch.cuda.get_device_name(),
            python=platform.python_version(),
            torch=torch.__version__,
            transformers=transformers.__version__,
            parameters=sum(p.numel() for p in model.parameters()),
            original_weights_sha256=before,
            eos_ids=eos,
            precision="float32",
            model_files={p.name: C["sha"](p) for p in sorted(local.iterdir()) if p.is_file()},
        ),
    )
    ids = tok.apply_chat_template(
        [dict(role="user", content=cases[0]["prompt"])], tokenize=True, add_generation_prompt=True
    )
    C["dump"](output / "admission.json", runtime["admission"](model, tok, ids, eos, m["layer"]))
    parts = {p: [c for c in cases if c["split"] == p] for p in ("train", "development", "test")}
    targets = {
        r["id"]: r["target"] for r in json.loads((folder / "training-targets.json").read_text())
    }
    refs = {r["id"]: r for r in json.loads((folder / "development-references.json").read_text())}
    with InputTokenBudget(
        output / "budget.jsonl", max_usd=m["jev_cap"], usd_per_million=m["usd_per_million"]
    ) as budget:
        async with JevScorer(
            load_api_key(key_file), model=m["jev"], max_retries=0, request_timeout=90
        ) as scorer:
            runner = Runner(model, tok, eos, m, output, scorer, budget, started)
            await runner.drafts(parts["train"] + parts["development"])
            adapters = runner.train(parts["train"], parts["development"], targets, refs)
            await runner.drafts(parts["test"])
            runner.test(parts["test"], adapters)
        after = runtime["weight_digest"](model)
        if before != after or any(
            p.requires_grad or p.grad is not None for p in model.parameters()
        ):
            raise ValueError("Original weights changed")
        C["dump"](
            output / "completion.json",
            dict(
                at=now(),
                seconds=time.monotonic() - started,
                original_weights_sha256=after,
                original_weights_unchanged=True,
                known_input_tokens=sum(budget.settled.values()),
                reserved_unknown_calls=len(budget.unresolved),
                unknown_max_charged_calls=len(budget.max_charged),
                usd=budget.charged_tokens * m["usd_per_million"] / 1e6,
                peak_allocated_bytes=torch.cuda.max_memory_allocated(),
            ),
        )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--freeze", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--prior", type=Path, required=True)
    p.add_argument("--key-file", type=Path, required=True)
    a = p.parse_args()
    try:
        asyncio.run(run(a.freeze, a.output, a.prior, a.key_file))
    except Exception as exc:
        if a.output.is_dir():
            append(a.output / "failure.jsonl", dict(at=now(), error_type=type(exc).__name__))
        raise
