"""Independent raw-record reconstruction; full-study admission is separate."""

import hashlib
import json
import math
import re
import runpy
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
S = runpy.run_path(str(HERE / "single.py"))
F = runpy.run_path(str(HERE / "feedback.py"))
P = runpy.run_path(str(HERE / "pipeline.py"))
D = runpy.run_path(str(HERE.parent / "contextual_memory/provenance.py"))
K = runpy.run_path(str(HERE.parent / "contextual_memory/checks.py"))


def lines(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def nonnegative(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def receipts(cases, natives, output, manifest):
    requests, responses, ledger = (
        lines(output / name) for name in ("requests.jsonl", "responses.jsonl", "budget.jsonl")
    )
    ids = {c["id"] for c in cases}
    req, res = {r["id"]: r for r in requests}, {r["id"]: r for r in responses}
    if (
        len(requests) != len(ids)
        or len(responses) != len(ids)
        or set(req) != ids
        or set(res) != ids
    ):
        raise ValueError("Missing or duplicate transfer feedback")
    terms = dict(
        event="terms",
        max_usd=str(manifest["api_cap_usd"]),
        usd_per_million=str(manifest["usd_per_million"]),
        request_token_ceiling=65536,
    )
    if not ledger or ledger[0] != terms or len(ledger) != 1 + 2 * len(ids):
        raise ValueError("Changed or incomplete transfer budget")
    reserves, settles = {}, {}
    cap, rate = Decimal(str(manifest["api_cap_usd"])), Decimal(str(manifest["usd_per_million"]))
    if not cap.is_finite() or not rate.is_finite() or cap <= 0 or rate <= 0:
        raise ValueError("Invalid transfer cap")
    ceiling = int(cap * 1000000 / rate)
    charged = 0
    for row in ledger[1:]:
        ident = row["id"]
        if row["event"] == "reserve" and ident not in reserves:
            charged += 65536
            if charged > ceiling:
                raise ValueError("Transfer reservation exceeded cap before dispatch")
            reserves[ident] = True
        elif (
            row["event"] == "settle"
            and ident in reserves
            and ident not in settles
            and type(row["input_tokens"]) is int
            and 0 <= row["input_tokens"] <= 65536
        ):
            settles[ident] = row["input_tokens"]
            charged += row["input_tokens"] - 65536
        else:
            raise ValueError("Invalid or unresolved transfer charge")
    if (
        set(reserves) != set(settles)
        or set(settles) != {r["reservation"] for r in responses}
        or len(settles) != len(ids)
    ):
        raise ValueError("Missing, duplicate or unknown provider charge")
    for case in cases:
        ident = case["id"]
        request, response, native = req[ident], res[ident], natives[ident]
        raw = response["raw"]
        if (
            request["payload"] != F["payload"](case, native["text"])
            or response["model"] != "jev-1.13.0"
            or raw["model"] != response["model"]
            or set(raw) != {"model", "answers", "usage"}
            or set(raw["answers"]) != {"correct"}
            or F["_probability"](raw["answers"], "correct") != response["probability"]
            or response["attempts"] != 1
            or type(response["attempts"]) is not int
            or request["reservation"] != response["reservation"]
            or any(
                type(response[k]) is not int or response[k] < 0 or response[k] != raw["usage"][k]
                for k in ("input_tokens", "output_tokens")
            )
            or settles[response["reservation"]] != response["input_tokens"]
            or not native["at"] <= request["at"] <= response["at"]
            or not nonnegative(response["seconds"])
        ):
            raise ValueError("Unbound provider payload, feedback, usage or timing")
    total = sum(settles.values())
    if total * manifest["usd_per_million"] / 1e6 > manifest["api_cap_usd"]:
        raise ValueError("Transfer API cap exceeded")
    return res, total


def generation(
    row, prompt, probabilities, tok, *, limit, eos, layer, context, vocab, sampling=None
):
    ids = row["generated_token_ids"]
    if row["prompt_token_ids"] != prompt or len(prompt) + limit > context:
        raise ValueError("Wrong exact prompt or generation envelope")
    if (
        not ids
        or len(ids) > limit
        or any(type(i) is not int or not 0 <= i < vocab for i in ids)
        or eos in ids[:-1]
    ):
        raise ValueError("Invalid generated tokens")
    body = ids[:-1] if ids[-1] == eos else ids
    if (
        tok.decode(body, skip_special_tokens=False, clean_up_tokenization_spaces=False)
        != row["text"]
        or row["finish_reason"] != ("eos" if ids[-1] == eos else "length")
        or (ids[-1] != eos and len(ids) != limit)
        or row["probabilities"] != probabilities
        or row["sampling"] != sampling
        or row["processed_tokens"] != len(prompt) + len(ids) - 1
        or not nonnegative(row["seconds"])
    ):
        raise ValueError("Changed generation, feedback or work record")
    events = row["events"]
    if probabilities is None:
        if events:
            raise ValueError("Unexpected native/blind intervention")
    elif (
        len(events) != len(ids)
        or [p for event in events for p in event["positions"]]
        != list(range(len(prompt) - 1, len(prompt) + len(ids) - 1))
        or any(
            event["layer"] != layer
            or event["feedback"] != probabilities
            or not nonnegative(event["relative_delta"])
            for event in events
        )
    ):
        raise ValueError("Unbound intervention positions or probabilities")


def check_run(cases, groups, output, tok, manifest, adapter_digests, *, width=2048, vocab=100352):
    import torch
    from safetensors.torch import load_file

    if any((output / name).exists() for name in ("failed.json", "failures.jsonl")):
        raise ValueError("Incomplete or failed transfer attempt")
    pairing = P["donors"](cases, groups)
    if json.loads((output / "donors.json").read_text()) != pairing:
        raise ValueError("Changed scenario donor mapping")
    ids = {c["id"] for c in cases}
    arms = ["native", "blind", "text"] + [
        f"{control}/{name}"
        for name in adapter_digests
        for control in (
            ("constant",)
            if name.partition("/")[0].endswith("-constant")
            else ("live", "constant", "donor")
        )
    ]
    rows = lines(output / "outputs.jsonl")
    table = {(r["id"], r["arm"]): r for r in rows}
    if len(table) != len(rows) or set(table) != {(i, arm) for i in ids for arm in arms}:
        raise ValueError("Incomplete or duplicate transfer output coverage")
    native = {i: table[i, "native"] for i in ids}
    response, input_tokens = receipts(cases, native, output, manifest)
    memories = lines(output / "memory-records.jsonl")
    memory_rows = {r["id"]: r for r in memories}
    if len(memories) != len(ids) or set(memory_rows) != ids:
        raise ValueError("Incomplete or duplicate transfer memory")
    tensors, paths = {}, set()
    eos = tok.convert_tokens_to_ids("<|end_of_text|>")
    for case in cases:
        ident, row = case["id"], memory_rows[case["id"]]
        aligned = S["positions_for"](
            tok, case, native[ident], eos=eos, limit=manifest["context_limit"]
        )
        name = "memories/" + hashlib.sha256(ident.encode()).hexdigest() + ".safetensors"
        path = output / name
        if (
            row["input_token_ids"] != aligned["ids"]
            or row["positions"] != aligned["positions"]
            or row["file"] != name
            or path.is_symlink()
            or not path.is_file()
            or hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]
            or row["shape"] != [width]
            or row["layer"] != manifest["layer"]
            or row["processed_tokens"] != len(aligned["ids"])
            or not nonnegative(row["seconds"])
            or row["at"] < response[ident]["at"]
        ):
            raise ValueError("Changed memory input, positions, file or work")
        values = load_file(str(path), device="cpu")
        if set(values) != {"contextual", "embedding"} or any(
            v.shape != (width,) or v.dtype != torch.float32 or not torch.isfinite(v).all()
            for v in values.values()
        ):
            raise ValueError("Invalid saved transfer memory")
        tensors[ident] = values
        paths.add(path)
    if paths != set((output / "memories").iterdir()):
        raise ValueError("Unexpected memory artifact inventory")
    expected = {}
    by_id = {c["id"]: c for c in cases}
    for row in rows:
        ident, arm = row["id"], row["arm"]
        case = by_id[ident]
        prompt = tok.apply_chat_template(
            [dict(role="user", content=S["prompt_for"](case))],
            tokenize=True,
            add_generation_prompt=True,
        )
        values = digest = adapter = None
        if arm != "native":
            prompt = S["repair_prefix"](
                tok,
                prompt,
                native[ident]["generated_token_ids"],
                feedback=response[ident]["probability"] if arm == "text" else None,
            )
            if row["at"] < memory_rows[ident]["at"]:
                raise ValueError("Repair precedes memory extraction")
        if arm not in ("native", "blind", "text"):
            control, name, seed = arm.split("/")
            p = (
                0.5
                if control == "constant"
                else response[pairing[ident] if control == "donor" else ident]["probability"]
            )
            values = [float(p)] * 3
            digest = D["tensor_digest"](tensors[ident][name.split("-")[0]].repeat(3, 1))
            adapter = adapter_digests[f"{name}/{seed}"]
        if row["task"] != case["task"] or row["split"] != case["split"]:
            raise ValueError("Changed case metadata")
        generation(
            row,
            prompt,
            values,
            tok,
            limit=manifest["native_limit" if arm == "native" else "repair_limit"],
            eos=eos,
            layer=manifest["layer"],
            context=manifest["context_limit"],
            vocab=vocab,
        )
        expected[ident, arm] = dict(
            memory_digest=digest, adapter_digest=adapter, probabilities=values
        )
    binding_seconds = K["check_bindings"](
        rows, lines(output / "generation-bindings.jsonl"), expected
    )
    jobs = lines(output / "jobs.jsonl")
    if len(jobs) != 2 * len(rows):
        raise ValueError("Incomplete transfer jobs")
    for i, row in enumerate(rows):
        start, finish = jobs[2 * i : 2 * i + 2]
        if (
            any(j["id"] != row["id"] or j["arm"] != row["arm"] for j in (start, finish))
            or start["event"] != "start"
            or finish["event"] != "finish"
            or not start["at"] <= row["at"] <= finish["at"]
            or (i and jobs[2 * i - 1]["at"] > start["at"])
        ):
            raise ValueError("Changed or overlapping transfer job")
    return dict(
        passed=True,
        scope="Single-question raw-record integrity, not full-study admission or quality",
        outputs=len(rows),
        requests=len(response),
        input_tokens=input_tokens,
        memory_extractions=len(memories),
        memory_processed_tokens=sum(r["processed_tokens"] for r in memories),
        memory_seconds=sum(r["seconds"] for r in memories),
        generated_tokens=sum(len(r["generated_token_ids"]) for r in rows),
        generation_processed_tokens=sum(r["processed_tokens"] for r in rows),
        generation_seconds=sum(r["seconds"] for r in rows),
        binding_seconds=binding_seconds,
    )


def check_comparator(cases, profiles, output, tok, *, eos=100257, vocab=100352):
    comparator = runpy.run_path(str(HERE / "comparator.py"))
    expected_files = {"outputs.jsonl", "jobs.jsonl", "mechanical-admission.json", "complete.json"}
    if {p.name for p in output.iterdir()} != expected_files or any(
        p.is_symlink() or not p.is_file() for p in output.iterdir()
    ):
        raise ValueError("Incomplete or unexpected larger-model artifacts")
    table = {c["id"]: c for c in cases}
    if len(table) != len(cases) or not cases or not profiles or len(set(profiles)) != len(profiles):
        raise ValueError("Invalid larger-model case/profile coverage")
    for case in cases:
        S["validate_case"](case)
    rows, jobs = lines(output / "outputs.jsonl"), lines(output / "jobs.jsonl")
    order = [(c["id"], p) for c in cases for p in profiles]
    if [(r["id"], r["arm"]) for r in rows] != order or len(jobs) != 2 * len(rows):
        raise ValueError("Incomplete or reordered larger-model coverage")
    for i, row in enumerate(rows):
        case = table[row["id"]]
        settings = comparator["profile"](row["arm"], row["id"])
        prompt = tok.apply_chat_template(
            [dict(role="user", content=S["prompt_for"](case))],
            tokenize=True,
            add_generation_prompt=True,
            thinking=settings["thinking"],
        )
        if row["task"] != case["task"] or row["split"] != case["split"]:
            raise ValueError("Changed larger-model metadata")
        generation(
            row,
            prompt,
            None,
            tok,
            limit=settings["limit"],
            eos=eos,
            layer=19,
            context=settings["context_limit"],
            vocab=vocab,
            sampling=settings["sampling"] | {"top_k": 50},
        )
        start, finish = jobs[2 * i : 2 * i + 2]
        if (
            any(j["id"] != row["id"] or j["arm"] != row["arm"] for j in (start, finish))
            or start["event"] != "start"
            or finish["event"] != "finish"
            or not start["at"] <= row["at"] <= finish["at"]
            or (i and jobs[2 * i - 1]["at"] > start["at"])
        ):
            raise ValueError("Changed or overlapping larger-model jobs")
    complete = json.loads((output / "complete.json").read_text())
    admission = json.loads((output / "mechanical-admission.json").read_text())
    tolerance = 0.25 if admission["dtype"] == "torch.bfloat16" else 0.001
    if (
        complete["outputs"] != len(rows)
        or not re.fullmatch(r"[a-f0-9]{64}", complete["backbone_before"])
        or complete["backbone_after"] != complete["backbone_before"]
        or not nonnegative(complete["seconds"])
        or complete["at"] < jobs[-1]["at"]
        or admission["passed"] is not True
        or admission["cache_argmax_equal"] is not True
        or not nonnegative(admission["cache_max_logit_error"])
        or admission["cache_absolute_tolerance"] != tolerance
        or admission["cache_max_logit_error"] > tolerance
        or not nonnegative(admission["seconds"])
        or admission["prompt_tokens"] != len(rows[0]["prompt_token_ids"])
    ):
        raise ValueError("Invalid larger-model completion or mechanics")
    return dict(
        passed=True,
        outputs=len(rows),
        generated_tokens=sum(len(r["generated_token_ids"]) for r in rows),
        generation_processed_tokens=sum(r["processed_tokens"] for r in rows),
        generation_seconds=sum(r["seconds"] for r in rows),
    )
