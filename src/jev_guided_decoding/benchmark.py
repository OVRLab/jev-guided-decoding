from __future__ import annotations

import hashlib
import json
import re
import statistics
import string
from collections import Counter
from pathlib import Path
from typing import Any


def normalize(text: str) -> str:
    text = text.lower().translate(str.maketrans("", "", string.punctuation))
    return " ".join(re.sub(r"\b(a|an|the)\b", " ", text).split())


def answer_metrics(prediction: str, references: list[str]) -> dict[str, float]:
    """Deterministic lexical metrics; neither metric establishes factual correctness."""
    predicted = normalize(prediction)
    pred_tokens = predicted.split()
    exact, f1 = 0.0, 0.0
    for reference in references:
        expected = normalize(reference)
        ref_tokens = expected.split()
        exact = max(exact, float(predicted == expected))
        overlap = sum((Counter(pred_tokens) & Counter(ref_tokens)).values())
        if not pred_tokens or not ref_tokens:
            value = float(pred_tokens == ref_tokens)
        elif overlap:
            precision, recall = overlap / len(pred_tokens), overlap / len(ref_tokens)
            value = 2 * precision * recall / (precision + recall)
        else:
            value = 0.0
        f1 = max(f1, value)
    return {"exact_match": exact, "token_f1": f1}


def load_cases(path: Path) -> tuple[list[dict[str, Any]], str]:
    raw = path.read_bytes()
    cases = [json.loads(line) for line in raw.decode().splitlines() if line.strip()]
    ids: set[str] = set()
    for case in cases:
        if not isinstance(case.get("id"), str) or case["id"] in ids:
            raise ValueError("Every benchmark case needs a unique string id")
        ids.add(case["id"])
        for name in ("question", "evidence"):
            if not isinstance(case.get(name), str) or not case[name].strip():
                raise ValueError(f"Case {case['id']} needs a nonempty {name}")
        if (
            not isinstance(case.get("answers"), list)
            or not case["answers"]
            or not all(isinstance(s, str) and s.strip() for s in case["answers"])
        ):
            raise ValueError(f"Case {case['id']} needs nonempty reference answers")
    if not cases:
        raise ValueError("Benchmark dataset is empty")
    return cases, hashlib.sha256(raw).hexdigest()


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    summary = {}
    for mode in sorted({r["result"]["mode"] for r in records}):
        rows = [r for r in records if r["result"]["mode"] == mode]
        outcomes = [r["result"] for r in rows]
        elapsed = sum(r["elapsed_seconds"] for r in outcomes)
        summary[mode] = {
            "runs": len(rows),
            "mean_exact_match": statistics.mean(r["metrics"]["exact_match"] for r in rows),
            "mean_token_f1": statistics.mean(r["metrics"]["token_f1"] for r in rows),
            "mean_elapsed_seconds": elapsed / len(rows),
            "accepted_tokens_per_second": sum(len(r["token_ids"]) for r in outcomes) / elapsed
            if elapsed
            else None,
            "generated_tokens": sum(r["generated_tokens"] for r in outcomes),
            "decode_token_slots": sum(r["decode_token_slots"] for r in outcomes),
            "prefill_tokens": sum(r["prefill_tokens"] for r in outcomes),
            "api_calls": sum(r["api_calls"] for r in outcomes),
            "jev_input_tokens": sum(r["jev_input_tokens"] for r in outcomes),
            "estimated_jev_input_cost_usd": (
                sum(r["estimated_jev_input_cost_usd"] for r in rows)
                if all(r["estimated_jev_input_cost_usd"] is not None for r in rows)
                else None
            ),
            "usage_unknown": any(r["usage_unknown"] for r in outcomes),
            "stop_reasons": dict(Counter(r["stop_reason"] for r in outcomes)),
        }
    return summary
