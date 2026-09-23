"""R21 stage A: exact Granite drafts, focused live feedback, independent admission."""

import argparse
import asyncio
import hashlib
import json
import platform
import random
import runpy
import subprocess
import time
from dataclasses import asdict
from pathlib import Path

from jev_guided_decoding.experiment_budget import InputTokenBudget
from jev_guided_decoding.jev import load_api_key
from jev_guided_decoding.local_claims import LocalClaimScorer
from jev_guided_decoding.types import Candidate, Request

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
D = runpy.run_path(str(HERE / "data.py"))
A = runpy.run_path(str(HERE / "analyze.py"))
J = runpy.run_path(str(HERE.parent / "adaptive_attention/journal.py"))
MODEL = "ibm-granite/granite-4.0-1b"
REVISION = "6a7381ba1f54d684ff508d991aeb7dc580157103"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    with Path(path).open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def source_hashes():
    paths = (
        list(HERE.glob("*.py"))
        + list((ROOT / "src").rglob("*.py"))
        + [
            ROOT / "research/semantic-feedback-plan.md",
            HERE.parent / "adaptive_attention/journal.py",
        ]
    )
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted(paths)}


def prepare(folder):
    folder.mkdir(parents=True, exist_ok=False)
    cases = D["worlds"]()
    dump(folder / "cases.json", cases)
    manifest = dict(
        protocol="r21-semantic-feedback-admission-v1",
        at=J["now"](),
        sources=source_hashes(),
        datasets={"cases.json": sha(folder / "cases.json")},
        source_revision=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        dirty=bool(
            subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()
        ),
        model=MODEL,
        revision=REVISION,
        jev="jev-1.13.0",
        cases=len(cases),
        precision="float32",
        do_sample=False,
        max_new_tokens=24,
        max_input_tokens=2048,
        max_seconds=5400,
        max_api_usd=0.50,
        usd_per_million=0.042,
        prior_spend_usd=32.55153075054077,
        cumulative_budget_usd=50,
    )
    dump(folder / "manifest.json", manifest)
    return manifest


def verify(folder):
    m = json.loads((folder / "manifest.json").read_text())
    if m["sources"] != source_hashes() or any(
        sha(folder / n) != h for n, h in m["datasets"].items()
    ):
        raise ValueError("Scientific source/data freeze mismatch")
    return m


def trim_ids(ids, eos):
    for i, value in enumerate(ids):
        if value in eos:
            return ids[: i + 1], "eos"
    return ids, "length"


def weight_digest(model):
    h = hashlib.sha256()
    for name, parameter in model.named_parameters():
        if parameter.requires_grad:
            raise ValueError("Original weights must be frozen")
        h.update(name.encode())
        h.update(parameter.detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()


def feedback_inputs(c, text):
    labels = ("constructed_supported", "constructed_unsupported", "granite_draft")
    claims = [D["claim"](c, value) for value in (c["owner"], c["wrong_owner"], text)]
    order = list(range(3))
    random.Random("r21-question-order/" + c["id"]).shuffle(order)
    candidates = tuple(Candidate((), claims[i], 0, "sentence") for i in order)
    # Names/true labels are bookkeeping, not fields in the provider request.
    request = Request("Evaluate each local assignment claim.", D["feedback_view"](c)["evidence"])
    return request, candidates, [labels[i] for i in order]


async def execute(folder, output, device, key_file=None):
    import torch
    import transformers

    from jev_guided_decoding.backends.transformers import TransformersBackend

    m = verify(folder)
    cases = json.loads((folder / "cases.json").read_text())
    started = time.monotonic()
    with (
        J["Journal"](output, m) as journal,
        InputTokenBudget(
            output / "jev-budget.jsonl",
            max_usd=m["max_api_usd"],
            usd_per_million=m["usd_per_million"],
        ) as budget,
    ):
        if journal.starts or budget.reserved:
            raise ValueError("R21 stage A cannot replay or resume an attempted run")
        base = TransformersBackend.load(
            MODEL, revision=REVISION, device=device, dtype="float32", local_files_only=True
        )
        tok, model = base.tokenizer, base.model
        before = weight_digest(model)
        dump(
            output / "hardware.json",
            dict(
                at=J["now"](),
                python=platform.python_version(),
                platform=platform.platform(),
                torch=torch.__version__,
                transformers=transformers.__version__,
                device=str(base.device),
                dtype=str(next(model.parameters()).dtype),
                load_and_hash_seconds=time.monotonic() - started,
                parameter_count=sum(p.numel() for p in model.parameters()),
                original_weights_sha256=before,
                eos_ids=sorted(base.eos_ids),
            ),
        )
        async with LocalClaimScorer(
            load_api_key(key_file), budget=budget, model=m["jev"]
        ) as scorer:
            for index, c in enumerate(cases):
                if time.monotonic() - started > m["max_seconds"]:
                    raise TimeoutError("R21 stage deadline")
                metadata = dict(id=c["id"], motif=c["motif"])
                if not journal.start(c["id"], metadata):
                    raise ValueError("Started job cannot be replayed")
                row = {**metadata, "status": "started"}
                try:
                    messages = D["messages"](c)
                    ids = tok.apply_chat_template(
                        messages, tokenize=True, add_generation_prompt=True
                    )
                    if len(ids) > m["max_input_tokens"]:
                        raise ValueError("Input limit exceeded")
                    x = torch.tensor([ids], device=base.device)
                    if device == "mps":
                        torch.mps.synchronize()
                    t0 = time.monotonic()
                    with torch.inference_mode():
                        generated = model.generate(
                            input_ids=x,
                            attention_mask=torch.ones_like(x),
                            do_sample=False,
                            max_new_tokens=m["max_new_tokens"],
                            use_cache=True,
                            pad_token_id=base.pad_id,
                            eos_token_id=sorted(base.eos_ids),
                        )[0, len(ids) :].tolist()
                    token_ids, stop = trim_ids(generated, base.eos_ids)
                    text = tok.decode(token_ids, skip_special_tokens=True)
                    row.update(
                        messages=messages,
                        prompt_token_ids=ids,
                        draft_token_ids=token_ids,
                        draft=text,
                        draft_oracle=D["assess"](c, text),
                        stop=stop,
                        generation_seconds=time.monotonic() - t0,
                    )
                    # Persist the exact generation before any paid attempt.
                    J["append"](output / "drafts.jsonl", {**row, "at": J["now"]()})
                    request, candidates, order = feedback_inputs(c, text)
                    payload = scorer._build_payload(request, "", candidates)
                    row.update(payload=payload, question_order=order)
                    J["append"](
                        output / "requests.jsonl",
                        dict(
                            id=c["id"],
                            at=J["now"](),
                            payload=payload,
                            payload_sha256=hashlib.sha256(
                                json.dumps(payload, sort_keys=True).encode()
                            ).hexdigest(),
                        ),
                    )
                    result = await scorer.score(request, "", candidates, timeout=60)
                    by_label = dict(zip(order, result.judgments, strict=True))
                    labels = ("constructed_supported", "constructed_unsupported", "granite_draft")
                    row.update(
                        status="complete",
                        scores=[by_label[k].support for k in labels],
                        completeness=[by_label[k].assessable for k in labels],
                        jev=asdict(result),
                    )
                    journal.finish(c["id"], row)
                except BaseException as exc:
                    row.update(
                        status="failed",
                        error_type=type(exc).__name__,
                        usage_unknown=bool(budget.unresolved),
                    )
                    journal.finish(c["id"], row)
                    raise
                if (index + 1) % 12 == 0:
                    print(
                        json.dumps(
                            dict(
                                completed=index + 1,
                                planned=len(cases),
                                elapsed_seconds=round(time.monotonic() - started, 1),
                            )
                        ),
                        flush=True,
                    )
        after = weight_digest(model)
        if after != before:
            raise ValueError("Original weights changed")
        dump(
            output / "completion.json",
            dict(
                at=J["now"](),
                elapsed_seconds=time.monotonic() - started,
                before_sha256=before,
                after_sha256=after,
                unchanged_weights=True,
                successful_calls=len(budget.settled),
                unknown_calls=len(budget.unresolved),
                input_tokens=budget.charged_tokens,
                jev_estimate_usd=budget.charged_tokens * m["usd_per_million"] / 1e6,
            ),
        )
    summary = A["analyze"](list(journal.outputs.values()), planned=m["cases"])
    dump(output / "analysis.json", summary)
    print(json.dumps(summary, indent=2), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=("prepare", "run", "analyze"))
    p.add_argument("--freeze", type=Path, required=True)
    p.add_argument("--output", type=Path)
    p.add_argument("--device", choices=("mps", "cuda", "cpu"), default="mps")
    p.add_argument("--key-file", type=Path)
    a = p.parse_args()
    if a.command == "prepare":
        print(json.dumps(prepare(a.freeze), indent=2))
    elif a.output is None:
        p.error("--output required")
    elif a.command == "run":
        asyncio.run(execute(a.freeze, a.output, a.device, a.key_file))
    else:
        m = verify(a.freeze)
        print(
            json.dumps(
                A["analyze"](J["rows"](a.output / "outputs.jsonl"), planned=m["cases"]), indent=2
            )
        )


if __name__ == "__main__":
    main()
