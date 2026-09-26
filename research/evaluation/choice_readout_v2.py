"""Prospective full-option readout fix; never retroactively replaces R26-A grading."""

import re
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
C = runpy.run_path(str(ROOT / "research/iterations/selective_benchmarks/common.py"))
R = runpy.run_path(str(ROOT / "research/diagnostics/public_baseline_readout.py"))


def grade(reference, text):
    if reference["kind"] != "choice":
        return C["grade"](reference, text) | {"method": "v1"}
    options = reference["options"]
    if (
        not isinstance(options, list)
        or not 1 <= len(options) <= 26
        or any(not isinstance(value, str) or not value.strip() for value in options)
        or reference["answer"] not in [chr(65 + i) for i in range(len(options))]
    ):
        raise ValueError("Invalid choice reference")
    primary = C["grade"](reference, text)
    if primary["parseable"]:
        return primary | {"method": "v1"}
    # A nonempty, invalid final answer cannot be replaced by an earlier option.
    for line in text.replace("**", "").splitlines():
        if re.match(r"^\s*(?:(?:Final|Answer)\s*:|The answer is\b)\s*\S", line, re.I):
            return primary | {"method": "unparseable"}
    # Build only the target's option list; demonstrations may reuse A/B/C labels.
    target_options = "\n".join(f"{chr(65 + i)}. {value}" for i, value in enumerate(options))
    answer = R["option_readout"](target_options, text)
    return dict(
        answer=answer,
        parseable=answer is not None,
        correct=answer is not None and answer == reference["answer"],
        method="full_option" if answer is not None else "unparseable",
    )
