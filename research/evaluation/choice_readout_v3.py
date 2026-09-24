"""Prospective GPQA readout: preserve v2 except for complete multiline options."""

import re
import runpy
from pathlib import Path

V2 = runpy.run_path(str(Path(__file__).with_name("choice_readout_v2.py")))


def normalize(text):
    return " ".join(text.strip().strip("*").strip().rstrip(".").casefold().split())


def grade(reference, text):
    if reference["kind"] != "choice":
        return V2["grade"](reference, text)
    # Validate without accepting v2's line-only option fallback on multiline data.
    V2["grade"](reference, "")
    options = reference["options"]
    if not any("\n" in o or "\r" in o for o in options):
        return V2["grade"](reference, text)
    cleaned = text.replace("**", "").strip()
    found = list(
        re.finditer(
            r"(?im)(?:\bFinal|\bAnswer|\bThe answer is)\s*:?\s*\(?([A-Z])\)?[.!]?\s*$",
            cleaned,
        )
    )
    explicit = found[-1] if found else re.fullmatch(r"\(?([A-Z])\)?[.!]?", cleaned)
    answer = explicit.group(1) if explicit else None
    method = "explicit_label"
    if answer is not None and not 0 <= ord(answer) - 65 < len(options):
        answer = None
    invalid_final = any(
        re.match(r"^\s*(?:(?:Final|Answer)\s*:|The answer is\b)\s*\S", line, re.I)
        for line in cleaned.splitlines()
    )
    if answer is None and not invalid_final:
        body = re.sub(r"(?im)^\s*(?:Final|Answer)\s*:\s*$", "", cleaned).strip()
        headers = list(re.finditer(r"(?m)^[ \t]*\(?([A-Z])\)?[.)][ \t]+", body))
        if headers:
            # Earlier independent option headers are ambiguous; nested headers
            # inside an exactly matching complete option remain part of its text.
            first = headers[0]
            label = first.group(1)
            index = ord(label) - 65
            if 0 <= index < len(options) and normalize(body[first.end() :]) == normalize(
                options[index]
            ):
                answer = label
                method = "complete_multiline_option"
        else:
            matches = [
                chr(65 + i) for i, o in enumerate(options) if normalize(body) == normalize(o)
            ]
            if len(matches) == 1:
                answer = matches[0]
                method = "complete_option_text"
    return dict(
        answer=answer,
        parseable=answer is not None,
        correct=answer is not None and answer == reference["answer"],
        method=method if answer is not None else "unparseable",
    )
