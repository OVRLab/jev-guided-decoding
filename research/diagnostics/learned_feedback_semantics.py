"""Reference-independent, non-exhaustive recognition of complete color answers."""

import argparse
import json
import re
from pathlib import Path

COLOR = r"(?P<color>red|blue|green|yellow|orange|purple|black|white)"
PATTERNS = [
    COLOR,
    r"(?:a )?" + COLOR + r" badge",
    r"(?:it|the color|the badge|the badge color) is " + COLOR,
]


def extract_color(text):
    text = re.sub(r"\s+", " ", text.strip()).casefold().removesuffix(".")
    for left, right in (("**", "**"), ('"', '"'), ("'", "'")):
        if text.startswith(left) and text.endswith(right):
            text = text[len(left) : -len(right)]
            break
    for pattern in PATTERNS:
        match = re.fullmatch(pattern, text)
        if match:
            return match["color"]
    return None


def readout(cases, rows):
    references = {c["id"]: c["answer"] for c in cases}
    groups = {}
    for r in rows:
        arm = f"{r['mode']}/{r['seed']}"
        group = groups.setdefault(arm, dict(n=0, correct=0, resolved=0, unresolved=[]))
        value = extract_color(r["text"])
        group["n"] += 1
        group["resolved"] += value is not None
        group["correct"] += value == references[r["case_id"]]
        if value is None:
            group["unresolved"].append(r["case_id"])
    for group in groups.values():
        group["lower"] = group["correct"] / group["n"]
        group["upper"] = (group["correct"] + len(group["unresolved"])) / group["n"]
    return groups


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cases", type=Path, required=True)
    p.add_argument("--answers", type=Path, required=True)
    a = p.parse_args()
    cases = json.loads(a.cases.read_text())
    rows = [json.loads(line) for line in a.answers.read_text().splitlines()]
    print(json.dumps(readout(cases, rows), indent=2))


if __name__ == "__main__":
    main()
