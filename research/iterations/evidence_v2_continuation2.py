"""R15 held-out service continuation; preserve selection, failures and started jobs."""

import argparse
import asyncio
import json
import random
import runpy
import shutil
import time
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
S = runpy.run_path(str(ROOT / "research/iterations/evidence_v2/study.py"))
D, P, E = S["D"], S["P"], S["E"]
write, append, sha = S["write"], S["append"], S["sha"]
PRIOR = None
REGISTRATION = ROOT / "research/protocols/evidence-attention-v2/continuation2.json"


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
    return incidents < 30 and (transport or info.get("status_code") in (429, 502, 503, 504, 529))


def retain_charge(budget):
    for key in sorted(budget.unresolved):
        budget.acknowledge_max_charge(
            key,
            reason="R15 recovery: retain unknown attempt at full reservation",
            authorization="Owner-authorized full study; prospective recovery amendment; no replay",
        )


class ContinuationRunner(S["Runner"]):
    def __init__(self, runtime, output, manifest):
        if PRIOR is not None:
            reg = json.loads(REGISTRATION.read_text())
            for name, expected in reg["prior_files"].items():
                path = PRIOR / name
                if sha(path) != expected["sha256"] or path.stat().st_size != expected["bytes"]:
                    raise ValueError("Prior result changed")
            for path in sorted(PRIOR.iterdir()):
                if path.suffix == ".jsonl" or path.name in (
                    "selected-policy.json",
                    "test-freeze.json",
                    "zero-equivalence.json",
                    "recovery.json",
                ):
                    shutil.copyfile(path, output / path.name)
            metadata = json.loads((output / "metadata.json").read_text())
            prior_completion = json.loads((PRIOR / "completion.json").read_text())
            if metadata["weights_before"] != prior_completion["weights_after"]:
                raise ValueError("Recovery weights changed")
            write(output / "continuation.json", reg)
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
        self.incidents = sum(
            r["status"] == "failed" for p in output.glob("*-scores.jsonl") for r in read_rows(p)
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
        selected = json.loads((self.output / "selected-policy.json").read_text())
        freeze = json.loads((self.output / "test-freeze.json").read_text())
        if freeze["selected_policy_sha256"] != sha(self.output / "selected-policy.json"):
            raise ValueError("Frozen selection changed")
        return selected["selected"]["policy"]

    async def evaluate(self, cases, previous, selected, scorer, *, stage):
        configurations = P["arms"](previous, selected)
        rows = (
            read_rows(self.output / f"{stage}.jsonl")
            if (self.output / f"{stage}.jsonl").exists()
            else []
        )
        index = {(r["id"], r["mode"]): r for r in rows}
        receipt_path = self.output / f"{stage}-scores.jsonl"
        prior_receipts = (
            {r["id"]: r for r in read_rows(receipt_path)} if receipt_path.exists() else {}
        )
        retain_charge(scorer.budget)
        with (
            (self.output / f"{stage}.jsonl").open("a") as stream,
            (self.output / f"{stage}-scores.jsonl").open("a") as receipts,
        ):
            for ci, case in enumerate(cases):
                if all((case["id"], arm) in index for arm in P["ARMS"]):
                    continue
                old = prior_receipts.get(case["id"])
                if old is not None:
                    if old["status"] == "complete":
                        scores, failure, delay = old["evaluation"]["scores"], None, None
                    elif recoverable(old, 0):
                        scores = []
                        failure = {
                            k: v for k, v in old.items() if k not in ("id", "stage", "status")
                        }
                        delay = None
                    else:
                        raise ValueError("Unsupported prior scorer failure")
                else:
                    evaluation, failure, delay = await self.score(case, scorer, stage, receipts)
                    scores = list(evaluation.scores) if evaluation else []
                shuffled = scores.copy()
                random.Random(f"r15/{stage}/{ci}/shuffle").shuffle(shuffled)
                order = list(P["ARMS"])
                random.Random(f"r15/{stage}/{ci}/arms").shuffle(order)
                encoded = self.encoded(case)
                for arm in order:
                    if (case["id"], arm) in index:
                        continue
                    if failure and arm in P["DEPENDENT"]:
                        row = dict(
                            id=case["id"],
                            world_id=case["world_id"],
                            stage=stage,
                            mode=arm,
                            status="failed",
                            provider_failure=failure,
                            seconds=0,
                        )
                        append(stream, row)
                    else:
                        raw, call_input = None, encoded
                        if arm == "prompt":
                            call_input = self.encoded(
                                case,
                                [
                                    s["id"]
                                    for s, r in zip(case["sources"], scores, strict=True)
                                    if r > 0.5
                                ],
                            )
                        elif arm == "zero":
                            raw = [0.0] * len(case["sources"])
                        elif arm == "oracle":
                            raw = case["oracle_scores"]
                        elif arm == "lexical":
                            raw = D["lexical_scores"](D["model_view"](case))
                        elif arm == "shuffled":
                            raw = shuffled
                        elif arm in P["DEPENDENT"]:
                            raw = scores
                        row = self.forward(
                            stage, case, arm, configurations[arm], raw, stream, encoded=call_input
                        )
                    rows.append(row)
                if delay:
                    await asyncio.sleep(delay)
                print(
                    json.dumps(
                        dict(
                            stage=stage,
                            contexts_done=ci + 1,
                            planned=len(cases),
                            elapsed=time.monotonic() - self.started,
                        )
                    ),
                    flush=True,
                )
        result = S["summarize"](
            rows, cases, draws=self.manifest["bootstrap_draws"], confirmatory=stage == "test"
        )
        result["provider_incidents_cumulative"] = self.incidents
        result["interpretation"] = (
            "confirmatory primary cohort"
            if stage == "test"
            else "exploratory longer-chain challenge; no new confirmatory claim"
        )
        write(self.output / f"{stage}-summary.json", result)
        return result


def freeze_matches(old, value):
    return {k: v for k, v in old.items() if k != "at"} == json.loads(
        json.dumps({k: v for k, v in value.items() if k != "at"}, allow_nan=False)
    )


def preserve_freeze(path, value):
    if path.name == "test-freeze.json" and path.exists():
        old = json.loads(path.read_text())
        if not freeze_matches(old, value):
            raise ValueError("Attempted change to held-out freeze")
        return
    write(path, value)


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
    if not all(
        (PRIOR / name).exists()
        for name in ("test.jsonl", "selected-policy.json", "test-freeze.json")
    ):
        raise ValueError("Continuation needs the original frozen selection and started test")

    S["run"].__globals__["write"] = preserve_freeze

    class RecoveryScorer(E["EvidenceScorer"]):
        def __init__(self, *values, **kwargs):
            super().__init__(*values, request_timeout=90, **kwargs)

    S["run"].__globals__["E"] = {**E, "EvidenceScorer": RecoveryScorer}
    S["run"].__globals__["Runner"] = ContinuationRunner
    return asyncio.run(S["run"](args))


if __name__ == "__main__":
    raise SystemExit(main())
