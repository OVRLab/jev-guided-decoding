"""Describe R16 answer forms and token-budget endings without changing its grading."""

import argparse
import hashlib
import json
import re
import runpy
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = runpy.run_path(str(ROOT / "research/iterations/adaptive_attention/data.py"))


def describe(rows):
    groups = {}
    for row in rows:
        if row["stage"] != "test":
            continue
        key = "/".join(row[k] for k in ("family", "contract", "arm"))
        if key not in groups:
            groups[key] = dict(
                outcomes=0,
                complete=0,
                failed=0,
                recognized_abstentions=0,
                bare_unknown_answers=0,
                other_recognized_abstentions=0,
                correct_abstentions=0,
                abstentions_on_answerable_cases=0,
                unparsed_complete_answers=0,
                correct_at_final_token_limit=0,
                final_endings=Counter(),
                reasoning_endings=Counter(),
            )
        group = groups[key]
        group["outcomes"] += 1
        complete = row["status"] == "complete"
        group["complete"] += int(complete)
        group["failed"] += int(not complete)
        for phase in row.get("phases", []):
            final = phase["phase"] == "final"
            group["final_endings" if final else "reasoning_endings"][phase["finish_reason"]] += 1
            if final and complete and phase["finish_reason"] == "token_limit":
                group["correct_at_final_token_limit"] += row["grade"]["correct"]
        if not complete or row["family"] == "hotpot":
            continue
        parsed = (
            row["text"].strip()
            if row["contract"] == "constrained"
            else DATA["parse_synthetic"](row["text"])
        )
        if parsed != row["grade"]["parsed"]:
            raise ValueError("Frozen parser no longer matches recorded grade")
        group["unparsed_complete_answers"] += int(parsed is None)
        if parsed == "UNKNOWN":
            bare = re.fullmatch(r"unknown[.!?]?", row["text"].strip(), re.IGNORECASE) is not None
            group["recognized_abstentions"] += 1
            group["bare_unknown_answers"] += int(bare)
            group["other_recognized_abstentions"] += int(not bare)
            group["correct_abstentions"] += row["grade"]["correct"]
            group["abstentions_on_answerable_cases"] += 1 - row["grade"]["correct"]
    return groups


def analyze(output_path, audit):
    raw = output_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if not audit.get("audit_passed") or digest != audit["artifact_hashes"]["outputs.jsonl"]:
        raise ValueError("Input does not match the completed audited output")
    rows = [json.loads(line) for line in raw.splitlines() if line]
    return dict(
        artifact_binding_passed=True,
        output_sha256=digest,
        diagnostic_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        parser_source_sha256=hashlib.sha256(
            (ROOT / "research/iterations/adaptive_attention/data.py").read_bytes()
        ).hexdigest(),
        scope="Descriptive reuse of completed R16 test outcomes; no regrading or inference.",
        groups=describe(rows),
    )


def main():
    parser = argparse.ArgumentParser()
    for key in ("outputs", "audit", "output"):
        parser.add_argument("--" + key, type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.outputs, json.loads(args.audit.read_text()))
    with args.output.open("x") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"artifact_binding_passed": True, "groups": len(result["groups"])}))


if __name__ == "__main__":
    main()
