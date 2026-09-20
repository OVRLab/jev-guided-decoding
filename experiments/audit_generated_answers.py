"""Reconstruct final-token ownership and enforce the development gate offline."""

import argparse
import hashlib
import json
import math
import runpy
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from jev_guided_decoding.framing import parse_frame

ROOT = Path(__file__).resolve().parents[1]
STUDY = runpy.run_path(str(ROOT / "experiments/generated_answer_study.py"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def audit_row(row, decode):
    r = row["result"]
    require(r["output_source"] == "granite_generated", "Wrong output owner")
    accepted, generated, final, steps = (), (), (), []
    final_raw = ""
    sums = Counter()
    diagnostics = Counter()
    for event in r["trace"]:
        if event["event"] not in ("proposal", "cancelled_generation"):
            continue
        proposal = event["proposal"]
        for name in ("generated_tokens", "decode_token_slots", "prefill_tokens"):
            sums[name] += proposal[name]
        sums["generation_seconds"] += proposal["seconds"]
        if event["event"] == "cancelled_generation":
            continue
        kind = event["phase"]
        require(kind in ("step", "final"), "Unexpected phase")
        expected_control = ("\n" if accepted else "") + f"<{kind}>"
        controls = tuple(event["control_token_ids"])
        require(
            decode(controls) == expected_control, "Controller inserted content beyond delimiters"
        )
        require(tuple(event["accepted_before"]) == accepted, "Selected path changed")
        prefix = accepted + controls
        require(tuple(event["prefix_token_ids"]) == prefix, "Rejected tokens entered continuation")
        prefix_text = decode(prefix)
        for candidate in proposal["candidates"]:
            full = decode(prefix + tuple(candidate["token_ids"]))
            expected = (
                full[len(prefix_text) :]
                if full.startswith(prefix_text)
                else decode(tuple(candidate["token_ids"]))
            )
            require(
                candidate["text"] == expected and candidate["full_text"] == full,
                "Model text/token mismatch",
            )
        if kind == "final":
            require("evaluation" not in event, "Jev scored the final answer")
            require(event["count"] == 1 and event["greedy"], "Final generation policy changed")
            diagnostics["final_generations"] += 1
        if "evaluation" in event:
            require(kind == "step" and r["mode"] == "jev", "Scoring outside intermediate Jev arm")
            evaluation = event["evaluation"]
            require(
                evaluation["model"] == "jev-1.13.0" and evaluation["attempts"] == 1,
                "Provider contract changed",
            )
            require(
                len(evaluation["judgments"]) == len(event["valid_indices"]),
                "Judgment alignment mismatch",
            )
            for index in event["valid_indices"]:
                frame = parse_frame("<step>" + proposal["candidates"][index]["text"])
                require(frame is not None and frame.kind == "step", "A non-step was scored")
            sums["api_calls"] += evaluation["attempts"]
            sums["jev_input_tokens"] += evaluation["input_tokens"]
            sums["jev_output_tokens"] += evaluation["output_tokens"]
        selected = event.get("selected_index")
        if selected is None:
            continue
        candidate = proposal["candidates"][selected]
        generated += tuple(candidate["token_ids"])
        accepted = prefix + tuple(candidate["token_ids"])
        frame = parse_frame(f"<{kind}>" + candidate["text"])
        if kind == "step":
            require(frame is not None and frame.kind == "step", "Accepted an invalid step")
            steps.append(frame.body)
            diagnostics["accepted_steps"] += 1
        else:
            final = tuple(candidate["token_ids"])
            final_raw = candidate["text"]
    require(diagnostics["final_generations"] <= 1, "More than one final generation")
    require(tuple(r["token_ids"]) == accepted, "Final continuation mismatch")
    require(tuple(r["generated_token_ids"]) == generated, "Generated token provenance mismatch")
    require(
        tuple(r["final_token_ids"]) == final and r["final_raw_text"] == final_raw,
        "Final IDs mismatch",
    )
    require(r["steps"] == steps, "Accepted reasoning text mismatch")
    if r["phase"] == "complete":
        frame = parse_frame("<final>" + final_raw)
        require(
            bool(final) and frame is not None and frame.body == r["text"],
            "Final answer was replaced",
        )
    for field, value in sums.items():
        require(
            math.isclose(r.get(field, 0), value, abs_tol=1e-6),
            "Resource accounting mismatch: " + field,
        )
    if r["mode"] != "jev":
        require(r["api_calls"] == 0, "Baseline called Jev")
    return dict(diagnostics)


def audit(output):
    protocol = json.loads((output / "protocol.json").read_text())
    cases = STUDY["read_lines"](output / "cases.jsonl")
    rows = STUDY["read_lines"](output / "runs.jsonl")
    events = STUDY["read_lines"](output / "journal.jsonl")
    require(protocol["source_hashes"] == STUDY["source_hashes"](), "Source changed")
    require(
        hashlib.sha256((output / "cases.jsonl").read_bytes()).hexdigest()
        == protocol["dataset_sha256"],
        "Dataset changed",
    )
    require(
        Counter(e["key"] for e in events if e["event"] == "started")
        == Counter(r["key"] for r in rows),
        "Start journal mismatch",
    )
    require(
        Counter(e["key"] for e in events if e["event"] == "finished")
        == Counter(r["key"] for r in rows),
        "Finish journal mismatch",
    )
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        protocol["config"]["model"]["model_id"],
        revision=protocol["config"]["model"]["revision"],
        local_files_only=True,
        trust_remote_code=False,
    )

    def decode(ids):
        return tokenizer.decode(
            list(ids), skip_special_tokens=True, clean_up_tokenization_spaces=False
        )

    diagnostics = Counter()
    config = protocol["config"]["generation"]
    for row in rows:
        diagnostics.update(audit_row(row, decode))
        r = row["result"]
        require(r["decode_token_slots"] <= config["max_decode_tokens"], "Decode ceiling exceeded")
        require(r["prefill_tokens"] <= config["max_prefill_tokens"], "Prefill ceiling exceeded")
        require(len(r["token_ids"]) <= config["max_path_tokens"], "Path ceiling exceeded")
        require(r["api_calls"] <= config["max_api_calls"], "API ceiling exceeded")
        require(r["elapsed_seconds"] < config["max_seconds"], "Time ceiling exceeded")
    result = STUDY["analyze"](cases, protocol["seeds"], rows)
    totals = {mode: Counter() for mode in protocol["modes"]}
    for task in result["tasks"].values():
        for mode, counts in task["modes"].items():
            totals[mode].update({k: counts[k] for k in ("planned", "completed", "format_valid")})
    no_errors = not any(
        r["result"]["stop_reason"] in STUDY["ERRORS"] or r["result"]["usage_unknown"] for r in rows
    )
    completion = {
        mode: {
            "frame_completion": c["completed"] / c["planned"],
            "answer_format_valid": c["format_valid"] / c["planned"],
        }
        for mode, c in totals.items()
    }
    changed = result["resources"]["jev"]["intermediate_choices_different_from_likelihood"]
    passed = (
        result["study_complete"]
        and no_errors
        and changed > 0
        and all(
            c["frame_completion"] >= 0.9 and c["answer_format_valid"] >= 0.9
            for c in completion.values()
        )
    )
    return {
        "provenance_audit_passed": True,
        "jobs_audited": len(rows),
        **diagnostics,
        "completion": completion,
        "jev_changed_intermediate_choices": changed,
        "development_gate_passed": passed if protocol["purpose"] == "pilot" else None,
        "analysis": result,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.output)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    STUDY["write_json"](args.output / f"audit-{stamp}.json", result)
    print(json.dumps({k: v for k, v in result.items() if k != "analysis"}, indent=2))
    return 0 if result["development_gate_passed"] is not False else 4


if __name__ == "__main__":
    raise SystemExit(main())
