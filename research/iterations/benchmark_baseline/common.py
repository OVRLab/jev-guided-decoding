"""Dependency-free contracts for R23; reference data never enter generation."""

import hashlib
import json
import re
from collections import Counter
from decimal import Decimal
from pathlib import Path


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def digest_text(text):
    return hashlib.sha256(text.encode()).hexdigest()


def dump(path, value):
    with Path(path).open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def verify_files(root, files):
    for name, digest in files.items():
        p = Path(root) / name
        if Path(name).is_absolute() or ".." in Path(name).parts or sha(p) != digest:
            raise ValueError("File binding mismatch: " + name)


def validate_case(case):
    required = {"id", "task", "family", "prompt", "origin_id"}
    if set(case) != required or any(not isinstance(v, str) or not v for v in case.values()):
        raise ValueError("Invalid generation case or reference leakage")


def bind(case, row):
    if row["id"] != case["id"] or row["prompt_sha256"] != digest_text(case["prompt"]):
        raise ValueError("Question/record binding mismatch")


def final_text(text, *, thinking):
    if thinking:
        if "</think>" not in text:
            return "", "unfinished_thinking"
        text = text.rsplit("</think>", 1)[1]
    return text.strip(), "complete" if text.strip() else "empty"


def grade(reference, text):
    kind = reference["kind"]
    if kind == "choice":
        patterns = [
            r"(?im)\bFinal:\s*\(?([A-Z])\)?(?:\*\*)?\.?\s*$",
            r"(?im)^\s*The answer is\s*\(?([A-Z])\)?\.?\s*$",
        ]
        found = [x for p in patterns for x in re.finditer(p, text)]
        match = (
            max(found, key=lambda x: x.start())
            if found
            else re.fullmatch(r"\s*\(?([A-Z])\)?\.?\s*", text)
        )
        answer = match.group(1) if match else None
        if answer is not None and not 0 <= ord(answer) - ord("A") < reference["choices"]:
            answer = None
        return {
            "answer": answer,
            "parseable": answer is not None,
            "correct": answer == reference["answer"],
        }
    if kind == "number":
        matches = re.findall(r"(?im)^\s*(?:####|Final:)\s*([-+]?\d[\d,]*(?:\.\d+)?)\s*$", text)
        answer = matches[-1].replace(",", "") if matches else None
        return {
            "answer": answer,
            "parseable": answer is not None,
            "correct": answer is not None and Decimal(answer) == Decimal(reference["answer"]),
        }
    raise ValueError("Evaluator not available: " + kind)


def trim_ids(ids, eos):
    for i, value in enumerate(ids):
        if value in eos:
            return ids[: i + 1], "eos"
    return ids, "length"


def summarize(cases, rows):
    indexed = {r["id"]: r for r in rows}
    ids = {c["id"] for c in cases}
    if len(indexed) != len(rows) or len(ids) != len(cases) or not set(indexed) <= ids:
        raise ValueError("Duplicate or unexpected case")
    result = {}
    for task in sorted({c["task"] for c in cases}):
        planned = [c for c in cases if c["task"] == task]
        actual = [indexed[c["id"]] for c in planned if c["id"] in indexed]
        correct = sum(r["correct"] is True for r in actual)
        result[task] = {
            "planned": len(planned),
            "received": len(actual),
            "missing": len(planned) - len(actual),
            "correct": correct,
            "accuracy": correct / len(planned),
            "status": dict(Counter(r["status"] for r in actual)),
        }
    return result


def verify_readout(case, row, *, thinking):
    bind(case, row)
    if "raw" in row:
        text, status = final_text(row["raw"], thinking=thinking)
        if row.get("final") != text or row["status"] != status:
            raise ValueError("Final readout mismatch")
    elif row["status"] not in ("input_limit", "generation_error"):
        raise ValueError("Missing raw generation")
