"""R27 prompt and terminal contracts; reference-free and no inference dependencies."""

import hashlib
import re

KINDS = {"choice", "number", "instruction", "code", "free", "tool"}
SUFFIX = {
    "choice": (
        "Solve the problem. Finish with a separate line starting Final: followed by "
        "one selected letter, then stop."
    ),
    "number": (
        "Solve the problem. Finish with a separate line starting #### followed by "
        "your numeric answer, then stop."
    ),
}


def task_prompt(body, kind):
    if not isinstance(body, str) or not body.strip() or kind not in KINDS:
        raise ValueError("Invalid task prompt")
    return body + "\n\n" + SUFFIX[kind] if kind in SUFFIX else body


def terminal_line(text, kind, thinking):
    """Only a complete requested line can terminate generation, never hidden thought."""
    if thinking:
        if "</think>" not in text:
            return False
        text = text.rsplit("</think>", 1)[1]
    if kind == "choice":
        pattern = r"(?m)^[ \t]*Final:[ \t]*[A-Z][ \t]*\r?\n"
    elif kind == "number":
        pattern = r"(?m)^[ \t]*####[ \t]*[-+]?\d[\d,]*(?:\.\d+)?[ \t]*\r?\n"
    else:
        return False
    return re.search(pattern, text) is not None


def case_seed(ident, seed):
    if not isinstance(ident, str) or not ident or type(seed) is not int or seed < 0:
        raise ValueError("Invalid request seed")
    return int.from_bytes(hashlib.sha256(f"{seed}/{ident}".encode()).digest()[:4], "big")
