"""Versioned source binding; every data/feedback/analysis contract is inherited unchanged."""

import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = runpy.run_path(str(HERE.parent / "gated_repair/common.py"))
globals().update({k: v for k, v in BASE.items() if not k.startswith("__") and k != "sources"})


def sources():
    return BASE["sources"]() | {
        str(p.relative_to(BASE["ROOT"])): BASE["sha"](p)
        for p in sorted(
            [*HERE.glob("*.py"), BASE["ROOT"] / "research/gated-repair-fp32-amendment.md"]
        )
    }


def verify(folder):
    import json

    m = json.loads((folder / "manifest.json").read_text())
    if m["sources"] != sources():
        raise ValueError("V2 source freeze mismatch")
    BASE["C"]["verify_files"](folder, m["datasets"])
    if m["precision"] != "float32":
        raise ValueError("Full precision required")
    return m
