"""R26 explicit selective execution and independent answer contracts."""

import hashlib
import json
import math
import re
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FORMATS = {"choice", "number", "instruction", "code", "free", "tool"}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def dump(path, value):
    with Path(path).open("x") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")


def validate_case(case):
    keys = {"id", "task", "family", "prompt", "format", "origin_id", "cluster", "split"}
    if (
        set(case) != keys
        or any(not isinstance(v, str) or not v.strip() for v in case.values())
        or case["format"] not in FORMATS
        or case["split"] not in {"development", "test"}
    ):
        raise ValueError("Invalid case or reference leakage")


def probability(value):
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError("Invalid probability")
    return value


def select(native, p_correct, repair):
    if p_correct is not None:
        probability(p_correct)
    if p_correct is None or p_correct >= 0.5:
        return dict(
            output=native,
            decision="retain_native",
            repair_executed=False,
            probability_correct=p_correct,
            gate=None,
        )
    gate = 1 - p_correct
    output = repair(gate)
    return dict(
        output=output,
        decision="repair",
        repair_executed=True,
        probability_correct=p_correct,
        gate=gate,
    )


def instruction(kind):
    if kind not in FORMATS:
        raise ValueError("Unknown output format")
    ending = {
        "choice": "Finish with a separate line starting Final: followed by the selected letter.",
        "number": "Finish with a separate line starting #### followed by your numeric answer.",
        "instruction": "Return only the requested response, following all original instructions.",
        "code": "Return the complete corrected Python solution in one Python code block.",
        "free": "Return a concise direct answer to the original question.",
        "tool": "Return only the requested function-call representation.",
    }[kind]
    return (
        "Check your previous answer carefully against the original problem. "
        "Correct any errors; preserve the conclusion if it is already correct. " + ending
    )


def repair_prefix(tokenizer, prompt, draft, kind):
    if not prompt or not draft:
        raise ValueError("Empty prompt/draft")
    end = tokenizer.convert_tokens_to_ids("<|end_of_text|>")
    framing = [] if draft[-1] == end else [end]
    suffix = (
        "\n<|start_of_role|>user<|end_of_role|>"
        + instruction(kind)
        + "<|end_of_text|>\n<|start_of_role|>assistant<|end_of_role|>"
    )
    return list(prompt) + list(draft) + framing + tokenizer.encode(suffix, add_special_tokens=False)


def grade(ref, text):
    """Generated-answer readout: no random fallback and no gold-driven extraction."""
    cleaned = text.replace("**", "").strip()
    if ref["kind"] == "choice":
        found = list(
            re.finditer(
                r"(?im)(?:\bFinal|\bAnswer|\bThe answer is)\s*:?\s*\(?([A-Z])\)?[.!]?\s*$",
                cleaned,
            )
        )
        match = found[-1] if found else re.fullmatch(r"\(?([A-Z])\)?[.!]?", cleaned)
        answer = match.group(1) if match else None
        options = ref["options"]
        if answer is None:
            lines = [
                line.strip().rstrip(".").casefold() for line in cleaned.splitlines() if line.strip()
            ]
            matches = [
                chr(65 + i)
                for i, opt in enumerate(options)
                if lines and lines[-1] == opt.strip().rstrip(".").casefold()
            ]
            answer = matches[0] if len(matches) == 1 else None
        if answer is not None and not 0 <= ord(answer) - 65 < len(options):
            answer = None
        correct = answer == ref["answer"]
    elif ref["kind"] == "number":
        number = r"([-+]?\d[\d,]*(?:\.\d+)?)"
        found = [
            m
            for pattern in (
                r"####\s*" + number + r"\s*[.!]?\s*$",
                r"\\boxed\{\s*" + number + r"\s*\}",
                r"(?im)^\s*(?:Final|Answer):\s*" + number + r"\s*[.!]?\s*$",
            )
            for m in re.finditer(pattern, cleaned)
        ]
        match = max(found, key=lambda m: m.start()) if found else re.fullmatch(number, cleaned)
        answer = match.group(1).replace(",", "") if match else None
        correct = answer is not None and Decimal(answer) == Decimal(ref["answer"])
    else:
        raise ValueError("Independent evaluator required for " + ref["kind"])
    return dict(answer=answer, parseable=answer is not None, correct=correct)
