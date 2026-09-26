"""V3 source binding and unchanged scientific contracts."""

import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = runpy.run_path(str(HERE.parent / "gated_repair/common.py"))
V2 = runpy.run_path(str(HERE.parent / "gated_repair_fp32/common.py"))
globals().update(
    {k: v for k, v in BASE.items() if not k.startswith("__") and k not in ("sources", "verify")}
)


def sources():
    return V2["sources"]() | {
        str(p.relative_to(BASE["ROOT"])): BASE["sha"](p)
        for p in sorted(
            [*HERE.glob("*.py"), BASE["ROOT"] / "research/gated-repair-continuation.md"]
        )
    }


def verify(folder):
    import json

    m = json.loads((folder / "manifest.json").read_text())
    if m["sources"] != sources() or m["precision"] != "float32" or m["max_incidents"] != 8:
        raise ValueError("Continuation source/settings mismatch")
    BASE["C"]["verify_files"](folder, m["datasets"])
    return m
