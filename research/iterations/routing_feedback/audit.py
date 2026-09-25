"""Independent R28 integrity admission before benchmark scoring."""

import argparse
import json
import math
import runpy
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
C = runpy.run_path(str(HERE / "common.py"))
F = runpy.run_path(str(HERE / "feedback.py"))
A = runpy.run_path(str(HERE.parent / "selective_benchmarks/admission.py"))


def records(path):
    return [json.loads(s) for s in path.read_text().splitlines()] if path.exists() else []


def check_complete(completion, cases, outputs):
    if completion.get("cases") != cases or completion.get("expected_outputs") != outputs:
        raise ValueError("Incomplete study coverage")


def check_row(row, prefix, tokenizer, eos, limit, gate):
    tokens = row["generated_token_ids"]
    if (
        row["prompt_token_ids"] != prefix
        or not tokens
        or len(tokens) > limit
        or any(type(t) is not int or t < 0 for t in tokens)
        or any(t in eos for t in tokens[:-1])
        or row["gate"] != gate
    ):
        raise ValueError("Exact prefix, tokens or gate mismatch")
    ended = tokens[-1] in eos
    body = tokens[:-1] if ended else tokens
    if (
        tokenizer.decode(body, skip_special_tokens=False) != row["text"]
        or row["finish_reason"] != ("eos" if ended else "length")
        or (not ended and len(tokens) != limit)
    ):
        raise ValueError("Decode or stopping mismatch")
    work = row["work"]
    expected = dict(
        batch_size=1,
        forwards=len(tokens),
        processed_token_slots=len(prefix) + len(tokens) - 1,
        padded_prompt_tokens=len(prefix),
        generated_token_slots=len(tokens),
    )
    if (
        any(work.get(k) != v for k, v in expected.items())
        or not math.isfinite(work["seconds"])
        or work["seconds"] < 0
    ):
        raise ValueError("Generation work mismatch")
    events = row["events"]
    if gate is None:
        if events:
            raise ValueError("Unexpected native intervention")
        values = row["log_probabilities"]
        if len(values) != len(tokens) or any(not math.isfinite(p) or p > 0 for p in values):
            raise ValueError("Invalid likelihood record")
        values = values[:-1] if ended else values
        mean = sum(values) / len(values) if values else None
        if mean != row["mean_log_probability"]:
            raise ValueError("Confidence reconstruction failed")
    else:
        positions = [p for event in events for p in event["positions"]]
        if positions != list(range(len(prefix) - 1, len(prefix) + len(tokens) - 1)):
            raise ValueError("Wrong internal hook positions")
        if any(
            e["layer"] != 19
            or e["feedback"] != [gate, gate]
            or not math.isfinite(e["relative_delta"])
            or e["relative_delta"] < 0
            for e in events
        ):
            raise ValueError("Wrong internal feedback")


def audit(folder, output):
    from huggingface_hub import snapshot_download
    from transformers import AutoTokenizer

    m = json.loads((folder / "manifest.json").read_text())
    A["verify_bindings"](folder, m)
    if json.loads((output / "start.json").read_text())["manifest_sha256"] != C["sha"](
        folder / "manifest.json"
    ):
        raise ValueError("Different admitted manifest")
    cases = json.loads((folder / "cases.json").read_text())
    for case in cases:
        C["validate_case"](case)
    ids = {c["id"] for c in cases}
    if len(ids) != len(cases) or len(ids) != m["eligible_cases"]:
        raise ValueError("Different cohort")
    rows = records(output / "outputs.jsonl")
    native = {r["id"]: r for r in rows if r["arm"] == "native"}
    responses = records(output / "responses.jsonl")
    requests = records(output / "requests.jsonl")
    feedback = records(output / "feedback.jsonl")
    if (
        len(responses) != len(ids)
        or len(requests) != len(ids)
        or len(feedback) != len(ids)
        or records(output / "failures.jsonl")
        or any({r["id"] for r in rs} != ids for rs in [responses, requests, feedback])
    ):
        raise ValueError("Incomplete or failed API delivery")
    probabilities = {r["id"]: r["probability_correct"] for r in responses}
    request_map = {r["id"]: r for r in requests}
    response_map = {r["id"]: r for r in responses}
    f_map = {r["id"]: r for r in feedback}
    ledger = records(output / "budget.jsonl")
    if ledger[0] != dict(
        event="terms",
        max_usd=str(m["jev_cap"]),
        usd_per_million=str(m["usd_per_million"]),
        request_token_ceiling=65536,
    ):
        raise ValueError("Changed API budget terms")
    reserves = [r["id"] for r in ledger[1:] if r["event"] == "reserve"]
    settled = [r for r in ledger[1:] if r["event"] == "settle"]
    if (
        len(ledger) != 1 + 2 * len(ids)
        or len(set(reserves)) != len(ids)
        or set(reserves) != {r["reservation"] for r in responses}
        or len(settled) != len(ids)
        or {r["id"] for r in settled} != set(reserves)
    ):
        raise ValueError("API receipt/charge mismatch")
    settlement = {r["id"]: r["input_tokens"] for r in settled}
    for case in cases:
        ident = case["id"]
        req, res, fb = request_map[ident], response_map[ident], f_map[ident]
        expected = F["payload"](case, native[ident]["text"].strip() or "(empty response)")
        if (
            req["payload"] != expected
            or req["reservation"] != res["reservation"]
            or req["attempt"] != 1
            or res["attempt"] != 1
            or res["attempts"] != 1
            or res["model"] != m["jev"]
            or settlement[res["reservation"]] != res["input_tokens"]
            or fb["actual_probability_correct"] != res["probability_correct"]
            or fb["missing"]
            or fb["attempts"] != 1
        ):
            raise ValueError("Changed Jev input, judgment or usage")
        raw = res["raw"]
        if (
            raw["model"] != m["jev"]
            or raw["answers"]["correct"]["noul"] != res["probability_correct"]
            or raw["usage"]["input_tokens"] != res["input_tokens"]
        ):
            raise ValueError("Raw Jev response mismatch")
    plan = C["make_plan"](
        sorted(ids), probabilities, {i: r["mean_log_probability"] for i, r in native.items()}
    )
    saved = json.loads((output / "selection.json").read_text())
    if saved["plan"] != plan:
        raise ValueError("Changed selection or donor assignment")
    selected = C["select_outputs"](plan, rows)
    completion = json.loads((output / "completion.json").read_text())
    check_complete(completion, len(ids), len(rows))
    hardware = json.loads((output / "hardware.json").read_text())
    if (
        not completion["weights_unchanged"]
        or completion["weights_sha256"] != hardware["original_weights_sha256"]
        or hardware["profile"] != m["model"]
    ):
        raise ValueError("Weight/profile integrity failure")
    admission = json.loads((output / "admission.json").read_text())
    if (
        not admission["passed"]
        or not admission["numerical"]["passed"]
        or admission["plain"]["generated_token_ids"] != admission["observed"]["generated_token_ids"]
    ):
        raise ValueError("Failed numerical or observer admission")
    config = m["model"]
    local = Path(
        snapshot_download(
            config["id"], revision=config["revision"], allow_patterns=["*.json", "*.jinja", "*.txt"]
        )
    )
    for p in local.iterdir():
        if p.is_file() and p.suffix in (".json", ".jinja", ".txt"):
            if C["sha"](p) != hardware["files"][p.name]:
                raise ValueError("Tokenizer/config mismatch")
    tok = AutoTokenizer.from_pretrained(local, trust_remote_code=False)
    encoded = {
        c["id"]: tok.apply_chat_template(
            [dict(role="user", content=c["prompt"])], tokenize=True, add_generation_prompt=True
        )
        for c in cases
    }
    donors = {i: d for block in plan["blocks"] for i, d in block["donors"].items()}
    cases_by_id = {c["id"]: c for c in cases}
    for r in rows:
        ident, arm = r["id"], r["arm"]
        if r["prompt_sha256"] != C["digest"](cases_by_id[ident]["prompt"]):
            raise ValueError("Prompt binding mismatch")
        prefix = (
            encoded[ident]
            if arm == "native"
            else C["BASE"]["repair_prefix"](
                tok, encoded[ident], native[ident]["generated_token_ids"], "instruction"
            )
        )
        gate = (
            None
            if arm == "native"
            else (
                0.5
                if arm == "constant"
                else 1 - probabilities[ident if arm == "live" else donors[ident]]
            )
        )
        check_row(r, prefix, tok, hardware["eos_ids"], m["limit"], gate)
        if arm != "native" and r["at"] <= saved["at"]:
            raise ValueError("Repair preceded selection freeze")
    jobs = records(output / "jobs.jsonl")
    want = C["required_outputs"](plan)
    for event in ("start", "finish"):
        if Counter((r["id"], r["arm"]) for r in jobs if r["event"] == event) != Counter(
            dict.fromkeys(want, 1)
        ):
            raise ValueError("Job coverage mismatch")
    if len(jobs) != 2 * len(rows):
        raise ValueError("Unexpected job records")
    api = json.loads((output / "api-summary.json").read_text())
    total_tokens = sum(r["input_tokens"] for r in responses)
    if (
        api["charged_tokens"] != total_tokens
        or api["usd"] != total_tokens * m["usd_per_million"] / 1e6
        or api["calls"] != len(ids)
        or api["unresolved"]
        or api["max_charged"]
    ):
        raise ValueError("API total mismatch")
    return dict(
        passed=True,
        cases=len(ids),
        outputs=len(rows),
        policies=len(selected),
        generated_tokens=sum(len(r["generated_token_ids"]) for r in rows),
        jev=api,
        manifest_sha256=C["sha"](folder / "manifest.json"),
        artifact_hashes={p.name: C["sha"](p) for p in output.iterdir() if p.is_file()},
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--folder", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    args = p.parse_args()
    report = audit(args.folder, args.output)
    C["dump"](args.report, report)
    print(json.dumps({k: v for k, v in report.items() if k != "artifact_hashes"}))
