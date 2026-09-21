"""Prospective R15 transport recovery; immutable prefixes and no paid replay."""

import argparse
import asyncio
import json
import random
import runpy
import shutil
import time
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
S = runpy.run_path(str(ROOT / "research/iterations/evidence_v2/study.py"))
D, P, E = S["D"], S["P"], S["E"]
write, append, sha = S["write"], S["append"], S["sha"]
PRIOR = None
REGISTRATION = ROOT / "research/protocols/evidence-attention-v2/recovery.json"


def read_rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def recovery_metrics(rows, cases):
    index = {c["id"]: c for c in cases}
    complete = [r for r in rows if r["status"] == "complete"]
    result = dict(
        accuracy=sum(r.get("correct", False) for r in rows) / len(rows),
        mean_logprob=sum(r["reference_logprob"] for r in complete) / len(complete),
        complete=len(complete),
        failed=len(rows) - len(complete),
    )
    for name, keep in [
        ("answerable", lambda c: not c["missing"]),
        ("missing", lambda c: c["missing"]),
        ("clean", lambda c: c["condition"] == "clean"),
    ]:
        sub = [r for r in rows if keep(index[r["id"]])]
        result[name] = sum(r.get("correct", False) for r in sub) / len(sub)
    return result


def recoverable(info, incidents):
    transport = (
        info.get("status_code") is None
        and info.get("usage_unknown") is True
        and (info.get("message") == "Jev request failed or timed out; it was not replayed")
    )
    return incidents < 3 and (transport or info.get("status_code") in (429, 529))


def retain_charge(budget):
    for key in sorted(budget.unresolved):
        budget.acknowledge_max_charge(
            key,
            reason="R15 recovery: retain unknown attempt at full reservation",
            authorization="Owner-authorized full study; prospective recovery amendment; no replay",
        )


class RecoveryRunner(S["Runner"]):
    def __init__(self, runtime, output, manifest):
        if PRIOR is not None:
            reg = json.loads(REGISTRATION.read_text())
            for name, expected in reg["prior_files"].items():
                path = PRIOR / name
                if sha(path) != expected["sha256"] or path.stat().st_size != expected["bytes"]:
                    raise ValueError("Prior result changed")
            for name in (
                "starts.jsonl",
                "inputs.jsonl",
                "development.jsonl",
                "development-scores.jsonl",
            ):
                shutil.copyfile(PRIOR / name, output / name)
            metadata = json.loads((output / "metadata.json").read_text())
            prior_completion = json.loads((PRIOR / "completion.json").read_text())
            if metadata["weights_before"] != prior_completion["weights_after"]:
                raise ValueError("Recovery weights changed")
            write(output / "recovery.json", reg)
        self.runtime, self.output, self.manifest = runtime, output, manifest
        self.started = time.monotonic()
        old_starts = read_rows(output / "starts.jsonl")
        self.jobs = {(r["kind"], r["stage"], r["id"], r["mode"]) for r in old_starts}
        if len(self.jobs) != len(old_starts):
            raise ValueError("Duplicate prior starts")
        self.input_keys = {
            (r["id"], r["prompt_digest"]) for r in read_rows(output / "inputs.jsonl")
        }
        self.starts = (output / "starts.jsonl").open("a")
        self.inputs = (output / "inputs.jsonl").open("a")
        scorepath = output / "development-scores.jsonl"
        self.incidents = (
            sum(r["status"] == "failed" for r in read_rows(scorepath)) if scorepath.exists() else 0
        )

    async def score(self, case, scorer, stage, stream):
        from jev_guided_decoding.types import ScorerError

        self.start("jev", stage, case["id"], "relevance")
        view = D["model_view"](case)
        try:
            evaluation = await scorer.score(view, timeout=90)
            append(
                stream,
                dict(
                    id=case["id"],
                    stage=stage,
                    status="complete",
                    payload=E["payload_for"](view, scorer.model),
                    evaluation=asdict(evaluation),
                ),
            )
            return evaluation, None, None
        except ScorerError as exc:
            info = S["OLD"]["failure_info"](exc)
            append(stream, dict(id=case["id"], stage=stage, status="failed", **info))
            if not recoverable(info, self.incidents):
                raise
            delay = max(60.0, float(info["retry_after"] or 60))
            if delay > 300:
                raise
            self.incidents += 1
            retain_charge(scorer.budget)
            return None, info, delay

    async def development(self, cases, scorer):
        grid, previous = self.manifest["grid"], self.manifest["previous_policy"]
        rows = read_rows(self.output / "development.jsonl")
        receipts = {r["id"]: r for r in read_rows(self.output / "development-scores.jsonl")}
        buckets = {p["id"]: [r for r in rows if r["mode"] == p["id"]] for p in grid}
        native_rows = [r for r in rows if r["mode"] == "native"]
        completed_ids = {r["id"] for r in native_rows}
        for ident in completed_ids:
            if any(sum(r["id"] == ident for r in bucket) != 1 for bucket in buckets.values()):
                raise ValueError("Recovery supports complete prior model blocks only")
        retain_charge(scorer.budget)
        equality = []
        with (
            (self.output / "development.jsonl").open("a") as stream,
            (self.output / "development-scores.jsonl").open("a") as receipt_stream,
        ):
            for ci, case in enumerate(cases):
                if case["id"] in completed_ids:
                    continue
                old = receipts.get(case["id"])
                if old is not None:
                    if old["status"] != "failed" or not recoverable(old, 0):
                        raise ValueError("Unsupported prior partial context")
                    scores, failure, delay = [], old, None
                else:
                    ev, failure, delay = await self.score(
                        case, scorer, "development", receipt_stream
                    )
                    scores = list(ev.scores) if ev else []
                check = not failure and len(equality) < 12
                encoded = self.encoded(case)
                native = self.forward(
                    "development",
                    case,
                    "native",
                    None,
                    None,
                    stream,
                    encoded=encoded,
                    full_logits=check,
                )
                if check:
                    native, logits = native
                    zero, zlogits = self.forward(
                        "development",
                        case,
                        "recovery_zero_check",
                        {**previous, "strength": 0.0},
                        scores,
                        stream,
                        encoded=encoded,
                        full_logits=True,
                    )
                    delta = float((logits - zlogits).abs().max())
                    equal = (
                        delta <= 1e-6
                        and native["generated_token_ids"] == zero["generated_token_ids"]
                    )
                    equality.append(dict(id=case["id"], max_logit_delta=delta, equal=equal))
                    write(self.output / "zero-equivalence.json", equality)
                    if not equal:
                        raise ValueError("Recovery zero hook equivalence failed")
                native_rows.append(native)
                order = list(grid)
                random.Random(f"r15/development/{ci}").shuffle(order)
                for policy in order:
                    if failure:
                        row = dict(
                            id=case["id"],
                            world_id=case["world_id"],
                            condition=case["condition"],
                            mode=policy["id"],
                            stage="development",
                            status="failed",
                            provider_failure=failure,
                            seconds=0,
                        )
                        append(stream, row)
                    else:
                        row = self.forward(
                            "development",
                            case,
                            policy["id"],
                            policy,
                            scores,
                            stream,
                            encoded=encoded,
                        )
                    buckets[policy["id"]].append(row)
                if delay:
                    await asyncio.sleep(delay)
                print(
                    json.dumps(
                        dict(
                            stage="development",
                            contexts_done=ci + 1,
                            planned=len(cases),
                            incidents=self.incidents,
                            elapsed=time.monotonic() - self.started,
                        )
                    ),
                    flush=True,
                )
        if len(equality) != 12:
            raise ValueError("Insufficient fresh full-vocabulary zero checks")
        outcomes = [dict(policy=p, **recovery_metrics(buckets[p["id"]], cases)) for p in grid]
        selected = P["select"](outcomes, previous["id"])
        selected.update(
            native=recovery_metrics(native_rows, cases),
            frozen_at=datetime.now(UTC).isoformat(),
            source_hashes=S["sources"](),
            recovery_registration_sha256=sha(REGISTRATION),
        )
        write(self.output / "selected-policy.json", selected)
        return selected["selected"]["policy"]


def main():
    global PRIOR
    parser = argparse.ArgumentParser()
    for name in ("manifest", "output", "ledger", "prior"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--local-files-only", action="store_true")
    args = parser.parse_args()
    PRIOR = args.prior
    reg = json.loads(REGISTRATION.read_text())
    if (
        sha(Path(__file__)) != reg["helper_sha256"]
        or sha(ROOT / reg["amendment_path"]) != reg["amendment_sha256"]
    ):
        raise ValueError("Unfrozen recovery helper or amendment")
    if any(
        (PRIOR / name).exists()
        for name in ("test.jsonl", "challenge.jsonl", "selected-policy.json")
    ):
        raise ValueError("Recovery must precede selection and held-out inference")

    class RecoveryScorer(E["EvidenceScorer"]):
        def __init__(self, *values, **kwargs):
            super().__init__(*values, request_timeout=90, **kwargs)

    S["run"].__globals__["E"] = {**E, "EvidenceScorer": RecoveryScorer}
    S["run"].__globals__["Runner"] = RecoveryRunner
    return asyncio.run(S["run"](args))


if __name__ == "__main__":
    raise SystemExit(main())
