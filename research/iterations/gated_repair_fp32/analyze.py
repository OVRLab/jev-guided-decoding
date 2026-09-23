"""The unchanged R25 outcome auditor bound to the v2 source manifest."""

import argparse
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
C = runpy.run_path(str(HERE / "common.py"))
BASE = runpy.run_path(str(HERE.parent / "gated_repair/analyze.py"))
analyze = BASE["analyze"]
analyze.__globals__["C"] = C

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--freeze", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--save", type=Path, required=True)
    p.add_argument("--tokenizer", action="store_true")
    a = p.parse_args()
    tok = None
    if a.tokenizer:
        from transformers import AutoTokenizer

        m = C["verify"](a.freeze)
        tok = AutoTokenizer.from_pretrained(
            m["model"], revision=m["revision"], trust_remote_code=False
        )
    C["dump"](a.save, analyze(a.freeze, a.output, tok))
