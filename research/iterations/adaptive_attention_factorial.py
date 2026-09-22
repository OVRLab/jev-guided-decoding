"""Post-selection exploratory factorial controls; receipt replay only, no API client."""

import argparse
import asyncio
import hashlib
import json
import math
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent / "adaptive_attention"
P = runpy.run_path(str(HERE / "policies.py"))
D = runpy.run_path(str(HERE / "data.py"))
J = runpy.run_path(str(HERE / "journal.py"))
S = runpy.run_path(str(HERE / "scorer.py"))


def factorial_policies():
    result = {}
    for strength in (0, 1):
        for head in (0, 1):
            for threshold in (0, 1):
                weights = [5.0 if strength else math.log(16)] * 12
                if head:
                    weights[6] = 0.0
                result[f"s{strength}-h{head}-t{threshold}"] = P["changed"](
                    P["r15"](), weights=weights, threshold=0.65 if threshold else 0.5
                )
    return result


def new_policies():
    return {k: v for k, v in factorial_policies().items() if k not in ("s0-h0-t0", "s1-h1-t1")}


class Replay:
    """An unknown payload fails closed; constructing a network client is impossible here."""

    def __init__(self, path):
        self.receipts = {r["key"]: r for r in J["rows"](path) if r["status"] != "started"}
        self.new_failure = None

    async def get(self, view, reasoning=""):
        payload = S["payload_for"](view, "jev-1.13.0", reasoning)
        key = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        if key not in self.receipts or self.receipts[key]["payload"] != payload:
            raise ValueError("Receipt replay rejects an unseen payload")
        return self.receipts[key]


async def execute(args):
    import torch

    from jev_guided_decoding.backends.transformers import TransformersBackend

    R = runpy.run_path(str(HERE / "runtime.py"))
    STUDY = runpy.run_path(str(ROOT / "research/iterations/adaptive_attention_fp32.py"))
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    manifest = json.loads((args.manifest / "manifest.json").read_text())
    if manifest["sources"] != STUDY["source_hashes"]():
        raise ValueError("Original FP32 source mismatch")
    complete = json.loads((args.main / "completion.json").read_text())
    if not complete["completed_schedule"]:
        raise ValueError("Main study incomplete")
    selected = json.loads((args.main / "selected.json").read_text())["selected"]["policy"]
    if selected != factorial_policies()["s1-h1-t1"]:
        raise ValueError("The preregistered factorial does not match selected policy")
    freeze = dict(
        source_sha256=D["sha"](Path(__file__).resolve()),
        protocol_sha256=D["sha"](ROOT / "research/adaptive-attention-factorial.md"),
        main_manifest_sha256=D["sha"](args.manifest / "manifest.json"),
        main_completion_sha256=D["sha"](args.main / "completion.json"),
        main_outputs_sha256=D["sha"](args.main / "outputs.jsonl"),
        main_receipts_sha256=D["sha"](args.main / "receipts.jsonl"),
        policies=new_policies(),
        max_seconds=1200,
        paid_calls=0,
    )
    cases = json.loads((args.manifest / "test.json").read_text())
    if D["sha"](args.manifest / "test.json") != manifest["datasets"]["test.json"]:
        raise ValueError("Test cohort changed")
    with J["Journal"](args.output, freeze) as log:
        base = TransformersBackend.load(
            STUDY["MODEL"],
            revision=STUDY["REVISION"],
            device=args.device,
            dtype="float32",
            local_files_only=True,
        )
        before = STUDY["weight_hash"](base)
        if before != complete["weights_after"]:
            raise ValueError("Checkpoint state differs from main study")
        runner = STUDY["Runner"](
            R["Runtime"](base), log, Replay(args.main / "receipts.jsonl"), {"max_seconds": 1200}
        )
        # No new dispatch is possible: failed saved receipts remain failed outcomes.
        runner.incidents = runner.consecutive = 0
        count = 0
        for case in cases:
            for name, policy in new_policies().items():
                await runner.job(case, "constrained", name, policy, stage="factorial")
                count += 1
            if count % 120 == 0:
                print(json.dumps({"factorial_done": count, "planned": 3600}), flush=True)
        after = STUDY["weight_hash"](base)
        if before != after:
            raise ValueError("Weights changed during supplement")
        D["dump"](
            args.output / "completion.json",
            dict(
                at=J["now"](),
                planned=3600,
                outputs=len(log.outputs),
                paid_calls=0,
                weights_before=before,
                weights_after=after,
            ),
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--main", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", default="cuda")
    asyncio.run(execute(parser.parse_args()))


if __name__ == "__main__":
    main()
