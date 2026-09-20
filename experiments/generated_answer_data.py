"""Fresh task selection and independent grading of model-generated answers."""

import hashlib
import json
import random
import re
import runpy
from decimal import Decimal
from pathlib import Path

from jev_guided_decoding.generated_answer import final_body
from jev_guided_decoding.types import Request

ROOT = Path(__file__).resolve().parents[1]
PROOF = runpy.run_path(str(ROOT / "experiments/proofwriter_data.py"))
GSM_REVISION = "3101c7d5072418e28b9008a6636bde82a006892c"
GSM_HASHES = {
    "train": "17f347dc51477c50d4efb83959dbb7c56297aba886e5544ee2aaed3024813465",
    "test": "3730d312f6e3440559ace48831e51066acaca737f6eabec99bccb9e4b3c39d14",
}
NUMBER = re.compile(r"[+-]?(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d+)?")


def digest_text(text):
    return hashlib.sha256(text.encode()).hexdigest()


def normalize_answer(task, text, answer_format=None):
    text = text.strip()
    if task == "proofwriter":
        if answer_format == "boolean-v2":
            return {"TRUE": "ENTAILED", "FALSE": "CONTRADICTED", "UNKNOWN": "UNKNOWN"}.get(text)
        return text if text in PROOF["LABELS"] else None
    if task != "gsm8k":
        raise ValueError("Unknown task")
    if not NUMBER.fullmatch(text):
        return None
    number = Decimal(text.replace(",", ""))
    if number == 0:
        return "0"
    exact = format(number, "f")
    return exact.rstrip("0").rstrip(".") if "." in exact else exact


def request_for(case):
    return Request(case["question"], case["evidence"])


def grade(case, result):
    if result is None:
        return {"correct": False, "completed": False, "format_valid": False, "prediction": None}
    if result.get("output_source") != "granite_generated":
        raise ValueError("Final answer provenance is not model generation")
    complete = result.get("phase") == "complete"
    body = final_body(result.get("final_raw_text", ""), result.get("final_finish_reason", "frame"))
    if complete and (
        not result.get("final_token_ids") or body is None or body != result.get("text")
    ):
        raise ValueError("Final answer provenance does not match the generated final frame")
    predicted = (
        normalize_answer(case["task"], result.get("text", ""), case.get("answer_format"))
        if complete
        else None
    )
    return {
        "correct": predicted is not None and predicted == case["answer"],
        "completed": complete,
        "format_valid": predicted is not None,
        "prediction": predicted,
    }


def load_gsm(path, split):
    if split not in GSM_HASHES:
        raise ValueError("Unknown GSM split")
    rows = []
    for i, line in enumerate(path.read_text().splitlines()):
        raw = json.loads(line)
        if raw["answer"].count("####") != 1:
            raise ValueError("Invalid GSM reference format")
        answer = normalize_answer("gsm8k", raw["answer"].split("####")[1])
        if answer is None:
            raise ValueError("Invalid GSM numeric reference")
        evidence = raw["question"]
        rows.append(
            {
                "id": f"gsm8k/{split}/{i}",
                "source_id": str(i),
                "task": "gsm8k",
                "question": (
                    "Solve the word problem. Put only the final numeric answer, "
                    "without units or explanation, inside the final frame."
                ),
                "evidence": evidence,
                "evidence_sha256": digest_text(evidence),
                "answer": answer,
            }
        )
    return rows


def select_gsm(rows, count, excluded, seed=20260921):
    pool = sorted((r for r in rows if r["evidence_sha256"] not in excluded), key=lambda r: r["id"])
    random.Random(seed).shuffle(pool)
    selected, seen = [], set()
    for row in pool:
        if row["evidence_sha256"] in seen:
            continue
        seen.add(row["evidence_sha256"])
        selected.append(row)
        if len(selected) == count:
            return selected
    raise ValueError("Not enough distinct GSM questions")


def select_cases(archive, gsm_path, exclusions, *, pilot=False):
    split = "train" if pilot else "test"
    if hashlib.sha256(gsm_path.read_bytes()).hexdigest() != GSM_HASHES[split]:
        raise ValueError("GSM source checksum mismatch")
    excluded_ids = set(exclusions["theory_ids"])
    excluded_text = set(exclusions["evidence_sha256"])
    worlds = [
        w
        for w in PROOF["load_split"](archive, "dev" if pilot else "test")
        if w["id"] not in excluded_ids and digest_text(w["theory"]) not in excluded_text
    ]
    quotas = (
        {
            ("ENTAILED", 0): 1,
            ("ENTAILED", 2): 1,
            ("ENTAILED", 5): 1,
            ("CONTRADICTED", 0): 1,
            ("CONTRADICTED", 3): 1,
            ("CONTRADICTED", 5): 1,
            ("UNKNOWN", None): 2,
        }
        if pilot
        else PROOF["main_quotas"]()
    )
    selected = PROOF["select_cases"](worlds, quotas, seed=20260921)
    logic = []
    for case in selected:
        request = PROOF["request_for"](case)
        question = request.question.replace("ENTAILED", "TRUE").replace("CONTRADICTED", "FALSE")
        logic.append(
            {
                **case,
                "id": "proofwriter/" + case["id"],
                "source_id": case["id"],
                "task": "proofwriter",
                "question": question,
                "answer_format": "boolean-v2",
                "answer": case["label"],
                "evidence_sha256": digest_text(request.evidence),
            }
        )
    math = select_gsm(load_gsm(gsm_path, split), 8 if pilot else 200, excluded_text)
    result = [c for pair in zip(math, logic, strict=True) for c in pair]
    assert not ({c["evidence_sha256"] for c in result} & excluded_text)
    assert not ({c["theory_id"] for c in logic} & excluded_ids)
    return result
