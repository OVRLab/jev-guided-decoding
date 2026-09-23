"""Post-hoc R23 full-option readout; preserves frozen primary scores."""

import argparse
import hashlib
import json
import re
import runpy
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
C = runpy.run_path(str(ROOT / "research/iterations/benchmark_baseline/common.py"))


def normalize(text):
    return " ".join(text.strip().strip("*").strip().rstrip(".").casefold().split())


def option_readout(prompt, text):
    pattern = re.compile(r"^\(?([A-Z])\)?[.)]\s+(.+)$")
    options = {}
    for line in prompt.splitlines():
        match = pattern.fullmatch(line.strip())
        if match:
            key, value = match.groups()
            if key in options:
                return None
            options[key] = normalize(value)
    choices, matched = set(), set()
    for line in text.splitlines():
        match = pattern.fullmatch(line.strip().strip("*").strip())
        if match:
            key, value = match.groups()
            choices.add(key)
            if key in options and normalize(value) == options[key]:
                matched.add(key)
    return next(iter(matched)) if len(matched) == 1 and choices == matched else None


def readout(prompt, text, reference):
    original = C["grade"](reference, text)
    if original["parseable"] or reference["kind"] != "choice":
        return {**original, "method": "primary"}
    answer = option_readout(prompt, text)
    return {
        "answer": answer,
        "parseable": answer is not None,
        "correct": answer == reference["answer"],
        "method": "full_option" if answer is not None else "unparseable",
    }


def analyze(folder, output, primary_path):
    m = json.loads((folder / "manifest.json").read_text())
    C["verify_files"](folder, m["datasets"])
    cases = {r["id"]: r for r in json.loads((folder / "cases.json").read_text())}
    refs = {r["id"]: r for r in json.loads((folder / "references.json").read_text())}
    primary = json.loads(primary_path.read_text())
    if primary["input_files"]["outputs.jsonl"] != C["sha"](output / "outputs.jsonl"):
        raise ValueError("Primary output binding mismatch")
    grades = {(r["model"], r["id"]): r for r in primary["grades"]}
    values, seen = [], set()
    for row in [json.loads(x) for x in (output / "outputs.jsonl").read_text().splitlines()]:
        key = row["model"], row["id"]
        if key in seen or key not in grades:
            raise ValueError("Duplicate or unexpected output")
        seen.add(key)
        case, ref = cases[row["id"]], refs[row["id"]]
        C["bind"](case, ref)
        C["verify_readout"](case, row, thinking=m["models"][row["model"]]["thinking"])
        if ref["kind"] != "choice":
            continue
        secondary = readout(case["prompt"], row.get("final", ""), ref)
        values.append(
            {
                "id": row["id"],
                "model": row["model"],
                "task": row["task"],
                "status": row["status"],
                "primary_correct": grades[key]["correct"],
                "primary_parseable": grades[key]["parseable"],
                **secondary,
            }
        )
    if seen != set(grades):
        raise ValueError("Missing outputs")
    return {
        "at": datetime.now(UTC).isoformat(),
        "post_hoc": True,
        "primary_unchanged": True,
        "grades": values,
        "summaries": {
            name: C["summarize"](
                [c for c in cases.values() if refs[c["id"]]["kind"] == "choice"],
                [r for r in values if r["model"] == name],
            )
            for name in m["models"]
        },
        "input_sha256": C["sha"](output / "outputs.jsonl"),
        "primary_sha256": C["sha"](primary_path),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "note": (
            "Additional full-option extraction on public development outputs; "
            "not an official benchmark or independently annotated semantic score."
        ),
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--freeze", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--primary", type=Path, required=True)
    p.add_argument("--save", type=Path, required=True)
    a = p.parse_args()
    C["dump"](a.save, analyze(a.freeze, a.output, a.primary))
