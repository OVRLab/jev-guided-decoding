"""Apply a budget-bound state adapter to the unchanged v1 inference runner."""

import argparse
import asyncio
import json
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
STATE = runpy.run_path(str(HERE / "state.py"))
ADMISSION = ROOT / "reports/2026-09-24-full-benchmark-tranche/second-recovery-admission.json"
ADMISSION_SHA256 = "5228f72502df46685dbafa34671ef1dc130515c94f3a1ffaa3589b8745900cba"


async def run(folder, ancestors, output):
    if STATE["sha"](ADMISSION) != ADMISSION_SHA256:
        raise ValueError("Prospective admission file changed")
    admission = json.loads(ADMISSION.read_text())
    STATE["verify_chain"](ancestors)
    parent = ancestors[-1]
    runner = runpy.run_path(str(HERE.parent / "benchmark_recovery_v1/run.py"))
    namespace = dict(runner["S"])
    state = None

    def prepare(parent, output, *, manifest_sha256, max_seconds):
        nonlocal state
        if max_seconds != 39600:
            raise ValueError("Original worker contract changed")
        state = STATE["prepare"](
            parent, output, manifest_sha256=manifest_sha256, admission=admission
        )
        return state

    def dump(path, value):
        if path.name == "recovery-sources.json":
            extra = [
                HERE / "run.py",
                HERE / "state.py",
                HERE / "handoff.py",
                ROOT / "research/benchmark-interruption-recovery-v2.md",
                ADMISSION,
            ]
            files = {**value, **{str(p.relative_to(ROOT)): STATE["sha"](p) for p in extra}}
            STATE["append"](output / STATE["SOURCES"], dict(hop=state.hop, files=files))
        elif path.name == "recovery-cache-admission.json":
            STATE["dump"](output / f"recovery-chain-{state.hop}-cache-admission.json", value)
        else:
            STATE["dump"](path, value)

    namespace.update(prepare=prepare, dump=dump)
    runner["run"].__globals__["S"] = namespace
    await runner["run"](folder, parent, output)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--freeze", type=Path, required=True)
    p.add_argument("--ancestor", type=Path, action="append", required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    asyncio.run(run(a.freeze, a.ancestor, a.output))
