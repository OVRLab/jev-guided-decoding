"""R15 finite development search and fresh primary/challenge comparisons."""

import argparse
import asyncio
import json
import math
import random
import runpy
import subprocess
import time
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
D = runpy.run_path(str(HERE / "data.py"))
P = runpy.run_path(str(HERE / "policies.py"))
R = runpy.run_path(str(HERE / "runtime.py"))
OLD = runpy.run_path(str(ROOT / "research/experiments/evidence_study.py"))
E = runpy.run_path(str(ROOT / "research/experiments/evidence_scorer.py"))
ARMS = P["ARMS"]
write, append, sha = OLD["write"], OLD["append"], OLD["sha"]


def sources():
    result = OLD["sources"]()
    for path in sorted(HERE.glob("*.py")):
        result[str(path.relative_to(ROOT))] = sha(path)
    for name in ("head-ranking.json", "selected-policy.json"):
        path = ROOT / "reports/2026-09-21-evidence-attention/artifacts" / name
        result[str(path.relative_to(ROOT))] = sha(path)
    return result


def prepare(output):
    output.mkdir(parents=True, exist_ok=False)
    used = D["exposed_aliases"]()
    for split, count in [("development", 96), ("test", 600), ("challenge", 120)]:
        write(output / f"{split}.json", D["worlds"](split, count, used))
    ranking = json.loads(
        (ROOT / "reports/2026-09-21-evidence-attention/artifacts/head-ranking.json").read_text()
    )
    prior = json.loads(
        (ROOT / "reports/2026-09-21-evidence-attention/artifacts/selected-policy.json").read_text()
    )
    previous = P["r14"](ranking)
    if previous["heads"] != prior["heads"] or previous["strength"] != prior["strength"]:
        raise ValueError("R14 lineage mismatch")
    write(
        output / "manifest.json",
        dict(
            schema="evidence-attention-v2",
            at=datetime.now(UTC).isoformat(),
            source_revision=subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            source_hashes=sources(),
            protocol_sha256=sha(ROOT / "research/evidence-attention-v2-protocol.md"),
            dataset_hashes={
                s: sha(output / f"{s}.json") for s in ("development", "test", "challenge")
            },
            seeds=D["SEEDS"],
            grid=P["grid"](ranking),
            previous_policy=previous,
            model="ibm-granite/granite-4.0-1b",
            revision="6a7381ba1f54d684ff508d991aeb7dc580157103",
            jev_model="jev-1.13.0",
            max_seconds=5400,
            bootstrap_draws=10000,
            api_cap_usd=1,
            cloud_allowance_usd=5,
            prior_cumulative_usd=9.272902379,
            cumulative_cap_usd=50,
            arms=ARMS,
            primary_controls=["native", "r14"],
        ),
    )


def paired(differences, draws, alpha):
    result = dict(
        difference=sum(differences) / len(differences),
        world_wins=sum(d > 0 for d in differences),
        world_losses=sum(d < 0 for d in differences),
        world_ties=sum(d == 0 for d in differences),
        worlds=len(differences),
    )
    if draws:
        rng = random.Random(150922071)
        boot = sorted(
            sum(rng.choices(differences, k=len(differences))) / len(differences)
            for _ in range(draws)
        )
        result.update(
            interval=[
                boot[int(draws * alpha / 2)],
                boot[min(draws - 1, int(draws * (1 - alpha / 2)))],
            ],
            interval_level=1 - alpha,
        )
    return result


def summarize(rows, cases, *, draws=10000, confirmatory=True):
    expected = {(c["id"], arm) for c in cases for arm in ARMS}
    index = {}
    for row in rows:
        key = (row["id"], row["mode"])
        if key not in expected or key in index:
            raise ValueError("Unplanned or duplicate output")
        index[key] = row

    def correct(case, arm):
        row = index.get((case["id"], arm), {})
        return int(row.get("status") == "complete" and row.get("label") == case["reference"])

    groups = {}
    for c in cases:
        groups.setdefault(c["world_id"], []).append(c)
    result = dict(
        planned=len(expected),
        recorded=len(index),
        worlds=len(groups),
        arms={},
        primary={},
        secondary={},
    )
    for arm in ARMS:
        sub = [r for r in rows if r["mode"] == arm]
        result["arms"][arm] = dict(
            planned=len(cases),
            recorded=len(sub),
            missing=len(cases) - len(sub),
            complete=sum(r["status"] == "complete" for r in sub),
            failed=sum(r["status"] != "complete" for r in sub),
            correct=sum(correct(c, arm) for c in cases),
            accuracy=sum(correct(c, arm) for c in cases) / len(cases),
            model_seconds=sum(r.get("seconds", 0) for r in sub),
            by_condition={
                v: sum(correct(c, arm) for c in cases if c["condition"] == v)
                / sum(c["condition"] == v for c in cases)
                for v in ("clean", "distracted")
            },
        )
    for arm in ARMS:
        if arm == "r15":
            continue
        diffs = [
            sum(correct(c, "r15") - correct(c, arm) for c in group) / len(group)
            for group in groups.values()
        ]
        primary = arm in ("native", "r14")
        result["primary" if primary else "secondary"][arm] = paired(
            diffs, draws, 0.025 if primary and confirmatory else 0.05
        )
    result["advancement"] = bool(
        draws
        and result["primary"]["r14"]["difference"] >= 0.02 - 1e-12
        and all(c["interval"][0] > 0 for c in result["primary"].values())
    )
    result["confirmatory"] = confirmatory
    if not confirmatory:
        result["advancement"] = None
    return result


def metrics(rows, cases):
    index = {c["id"]: c for c in cases}
    result = dict(
        accuracy=sum(r["correct"] for r in rows) / len(rows),
        mean_logprob=sum(r["reference_logprob"] for r in rows) / len(rows),
    )
    for name, keep in [
        ("answerable", lambda c: not c["missing"]),
        ("missing", lambda c: c["missing"]),
        ("clean", lambda c: c["condition"] == "clean"),
    ]:
        sub = [r for r in rows if keep(index[r["id"]])]
        result[name] = sum(r["correct"] for r in sub) / len(sub)
    return result


class Runner:
    def __init__(self, runtime, output, manifest):
        self.runtime, self.output, self.manifest = runtime, output, manifest
        self.started = time.monotonic()
        self.starts = (output / "starts.jsonl").open("x")
        self.inputs = (output / "inputs.jsonl").open("x")
        self.jobs, self.input_keys = set(), set()
        self.incidents = 0

    def close(self):
        self.starts.close()
        self.inputs.close()

    def start(self, kind, stage, ident, mode):
        if time.monotonic() - self.started >= self.manifest["max_seconds"]:
            raise TimeoutError("Frozen R15 time ceiling")
        key = kind, stage, ident, mode
        if key in self.jobs:
            raise ValueError("Started operation cannot be replayed")
        self.jobs.add(key)
        append(
            self.starts,
            dict(kind=kind, stage=stage, id=ident, mode=mode, at=datetime.now(UTC).isoformat()),
        )

    def encoded(self, case, highlights=None):
        encoded = self.runtime.encode(D["model_view"](case), highlights=highlights)
        key = case["id"], encoded["prompt_digest"]
        if key not in self.input_keys:
            append(self.inputs, dict(id=case["id"], **encoded))
            self.input_keys.add(key)
        return encoded

    def forward(
        self, stage, case, mode, policy, scores, stream, *, encoded=None, full_logits=False
    ):
        self.start("model", stage, case["id"], mode)
        try:
            result = R["forward"](
                self.runtime, encoded or self.encoded(case), policy, scores, full_logits=full_logits
            )
            row = result[0] if isinstance(result, tuple) else result
            row.update(
                id=case["id"],
                world_id=case["world_id"],
                condition=case["condition"],
                mode=mode,
                stage=stage,
                correct=row["label"] == case["reference"],
            )
            row["reference_logprob"] = math.log(
                row["label_probabilities"][D["D"]["LABELS"].index(case["reference"])]
            )
            append(stream, row)
            return result
        except BaseException as exc:
            append(
                stream,
                dict(
                    id=case["id"],
                    stage=stage,
                    mode=mode,
                    status="failed",
                    error_type=type(exc).__name__,
                ),
            )
            raise

    async def score(self, case, scorer, stage, stream):
        from jev_guided_decoding.types import ScorerError

        self.start("jev", stage, case["id"], "relevance")
        view = D["model_view"](case)
        try:
            evaluation = await scorer.score(view)
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
            info = OLD["failure_info"](exc)
            append(stream, dict(id=case["id"], stage=stage, status="failed", **info))
            if (
                stage == "development"
                or info["status_code"] not in (429, 529)
                or self.incidents >= 3
            ):
                raise
            delay = max(60.0, float(info["retry_after"] or 60))
            if delay > 300:
                raise
            self.incidents += 1
            for key in sorted(scorer.budget.unresolved):
                scorer.budget.acknowledge_max_charge(
                    key,
                    reason="R15 explicit overload without receipt",
                    authorization="R15 v1: retain failed dependent outcomes; new contexts only",
                )
            return None, info, delay

    async def development(self, cases, scorer):
        grid, previous = self.manifest["grid"], self.manifest["previous_policy"]
        buckets, native_rows, equality = {p["id"]: [] for p in grid}, [], []
        with (
            (self.output / "development.jsonl").open("x") as stream,
            (self.output / "development-scores.jsonl").open("x") as receipts,
        ):
            for ci, case in enumerate(cases):
                evaluation, _, _ = await self.score(case, scorer, "development", receipts)
                scores, encoded = list(evaluation.scores), self.encoded(case)
                native = self.forward(
                    "development",
                    case,
                    "native",
                    None,
                    None,
                    stream,
                    encoded=encoded,
                    full_logits=ci < 12,
                )
                if ci < 12:
                    native, logits = native
                    zero_policy = {**previous, "strength": 0.0}
                    zero, zero_logits = self.forward(
                        "development",
                        case,
                        "zero_check",
                        zero_policy,
                        scores,
                        stream,
                        encoded=encoded,
                        full_logits=True,
                    )
                    delta = float((logits - zero_logits).abs().max())
                    equal = (
                        delta <= 1e-6
                        and native["generated_token_ids"] == zero["generated_token_ids"]
                    )
                    equality.append(dict(id=case["id"], max_logit_delta=delta, equal=equal))
                    if not equal:
                        raise ValueError("Zero hook equivalence failed")
                native_rows.append(native)
                order = list(grid)
                random.Random(f"r15/development/{ci}").shuffle(order)
                for policy in order:
                    buckets[policy["id"]].append(
                        self.forward(
                            "development",
                            case,
                            policy["id"],
                            policy,
                            scores,
                            stream,
                            encoded=encoded,
                        )
                    )
                print(
                    json.dumps(
                        dict(
                            stage="development",
                            contexts_done=ci + 1,
                            planned=len(cases),
                            elapsed=time.monotonic() - self.started,
                        )
                    ),
                    flush=True,
                )
        outcomes = [dict(policy=p, **metrics(buckets[p["id"]], cases)) for p in grid]
        selected = P["select"](outcomes, previous["id"])
        selected.update(
            native=metrics(native_rows, cases),
            frozen_at=datetime.now(UTC).isoformat(),
            source_hashes=sources(),
        )
        write(self.output / "zero-equivalence.json", equality)
        write(self.output / "selected-policy.json", selected)
        return selected["selected"]["policy"]

    async def evaluate(self, cases, previous, selected, scorer, *, stage):
        configurations = P["arms"](previous, selected)
        rows = []
        with (
            (self.output / f"{stage}.jsonl").open("x") as stream,
            (self.output / f"{stage}-scores.jsonl").open("x") as receipts,
        ):
            for ci, case in enumerate(cases):
                evaluation, failure, delay = await self.score(case, scorer, stage, receipts)
                scores = list(evaluation.scores) if evaluation else []
                shuffled = scores.copy()
                random.Random(f"r15/{stage}/{ci}/shuffle").shuffle(shuffled)
                order = list(ARMS)
                random.Random(f"r15/{stage}/{ci}/arms").shuffle(order)
                encoded = self.encoded(case)
                for arm in order:
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
        result = summarize(
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


async def run(args):
    manifest = json.loads((args.manifest / "manifest.json").read_text())
    if (
        sources() != manifest["source_hashes"]
        or sha(ROOT / "research/evidence-attention-v2-protocol.md") != manifest["protocol_sha256"]
    ):
        raise ValueError("Frozen inference or protocol changed")
    for split, digest in manifest["dataset_hashes"].items():
        if sha(args.manifest / f"{split}.json") != digest:
            raise ValueError("Frozen data changed")
    args.output.mkdir(parents=True, exist_ok=False)
    import torch

    from jev_guided_decoding.backends.transformers import TransformersBackend
    from jev_guided_decoding.experiment_budget import InputTokenBudget
    from jev_guided_decoding.jev import load_api_key

    torch.set_num_threads(2)
    runtime_class = runpy.run_path(str(ROOT / "research/experiments/evidence_runtime.py"))[
        "EvidenceRuntime"
    ]
    weight_digest = runpy.run_path(str(ROOT / "research/experiments/logit_mechanism.py"))[
        "weight_digest"
    ]
    started = time.monotonic()
    base = TransformersBackend.load(
        manifest["model"],
        revision=manifest["revision"],
        device=args.device,
        temperature=1,
        top_p=1,
        local_files_only=args.local_files_only,
    )
    runtime, before = runtime_class(base), weight_digest(base)
    write(
        args.output / "metadata.json",
        dict(
            at=datetime.now(UTC).isoformat(),
            source_hashes=sources(),
            source_revision=subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            git_status=subprocess.check_output(
                ["git", "status", "--porcelain"], cwd=ROOT, text=True
            ),
            manifest_sha256=sha(args.manifest / "manifest.json"),
            model=base.metadata(),
            weights_before=before,
            initial_setup_seconds=time.monotonic() - started,
        ),
    )
    runner, completion = Runner(runtime, args.output, manifest), {}
    try:
        with InputTokenBudget(args.ledger, max_usd=manifest["api_cap_usd"]) as budget:
            async with E["EvidenceScorer"](
                load_api_key(), budget=budget, model=manifest["jev_model"]
            ) as scorer:
                development = [
                    D["context"](w, c)
                    for w in json.loads((args.manifest / "development.json").read_text())
                    for c in ("clean", "distracted")
                ]
                selected = await runner.development(development, scorer)
                write(
                    args.output / "test-freeze.json",
                    dict(
                        at=datetime.now(UTC).isoformat(),
                        selected_policy_sha256=sha(args.output / "selected-policy.json"),
                        source_hashes=sources(),
                        dataset_hashes=manifest["dataset_hashes"],
                        arms=ARMS,
                    ),
                )
                for stage in ("test", "challenge"):
                    cases = [
                        D["context"](w, c)
                        for w in json.loads((args.manifest / f"{stage}.json").read_text())
                        for c in ("clean", "distracted")
                    ]
                    result = await runner.evaluate(
                        cases, manifest["previous_policy"], selected, scorer, stage=stage
                    )
                    completion[stage] = dict(
                        planned=result["planned"],
                        recorded=result["recorded"],
                        complete=sum(a["complete"] for a in result["arms"].values()),
                    )
                    if stage == "test":
                        completion["advancement"] = result["advancement"]
            completion["ledger"] = dict(
                charged_input_tokens=budget.charged_tokens, unresolved=len(budget.unresolved)
            )
    except BaseException as exc:
        completion.update(failed=True, error_type=type(exc).__name__)
        raise
    finally:
        runner.close()
        completion.update(
            weights_before=before,
            weights_after=weight_digest(base),
            elapsed_seconds=time.monotonic() - started,
            at=datetime.now(UTC).isoformat(),
        )
        completion["weights_unchanged"] = (
            completion["weights_before"] == completion["weights_after"]
        )
        write(args.output / "completion.json", completion)
        print(json.dumps(completion), flush=True)
    return 0 if completion["weights_unchanged"] else 2


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("output", type=Path)
    p = sub.add_parser("run")
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--ledger", type=Path, required=True)
    p.add_argument("--device", default="cuda")
    p.add_argument("--local-files-only", action="store_true")
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.output)
        return 0
    return asyncio.run(run(args))


if __name__ == "__main__":
    raise SystemExit(main())
