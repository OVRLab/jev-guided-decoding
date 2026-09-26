"""R14 prospective head profiling, calibration and controlled evidence-attention test."""

import argparse
import asyncio
import hashlib
import json
import math
import os
import random
import runpy
import subprocess
import time
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).parent
D = runpy.run_path(str(HERE / "evidence_data.py"))
ARMS = ("native", "zero", "oracle", "jev", "shuffled", "lexical", "random_heads", "prompt")
DEPENDENT = {"jev", "shuffled", "random_heads", "prompt"}
CONTROLS = ("native", "shuffled", "lexical", "prompt")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sources():
    paths = list((ROOT / "src").rglob("*.py")) + list(HERE.glob("*.py")) + [ROOT / "uv.lock"]
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted(paths)}


def write(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def append(stream, value):
    stream.write(json.dumps(value, allow_nan=False) + "\n")
    stream.flush()
    os.fsync(stream.fileno())


def prepare(output):
    output.mkdir(parents=True, exist_ok=False)
    for split, count in (("profile", 24), ("calibration", 72), ("test", 360)):
        write(output / f"{split}.json", D["worlds"](split, count))
    write(
        output / "manifest.json",
        dict(
            schema="evidence-attention-v1",
            created_at=datetime.now(UTC).isoformat(),
            model="ibm-granite/granite-4.0-1b",
            revision="6a7381ba1f54d684ff508d991aeb7dc580157103",
            jev_model="jev-1.13.0",
            source_hashes=sources(),
            dataset_hashes={
                s: sha(output / f"{s}.json") for s in ("profile", "calibration", "test")
            },
            protocol_sha256=sha(ROOT / "research/evidence-attention-protocol.md"),
            source_revision=subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            arms=ARMS,
            primary_controls=CONTROLS,
            profile_strength=math.log(4),
            head_counts=[1, 2, 4, 8],
            strengths=[math.log(2), math.log(4), math.log(8)],
            max_seconds=5 * 3600,
            api_cap_usd=3,
            prior_usd=8.488813983,
            bootstrap_draws=10000,
            bootstrap_seed=140920261,
        ),
    )


def select_policy(outcomes, native_accuracy, native_clean):
    if not outcomes:
        raise ValueError("No calibration policies")
    chosen = sorted(
        outcomes, key=lambda x: (-x["accuracy"], -x["mean_logprob"], x["count"], x["strength"])
    )[0]
    delta = chosen["accuracy"] - native_accuracy
    clean_delta = chosen["clean_accuracy"] - native_clean
    return dict(
        **chosen,
        improvement=delta,
        clean_change=clean_delta,
        admitted=delta >= 0.03 - 1e-12 and clean_delta >= -0.03 - 1e-12,
    )


def failure_info(exc):
    diagnostics = exc.diagnostics or {}
    return dict(
        error_type=type(exc).__name__,
        message=str(exc),
        status_code=diagnostics.get("status_code"),
        retry_after=diagnostics.get("retry_after_seconds"),
        usage_unknown=exc.usage_unknown,
        diagnostics=diagnostics,
    )


def summarize(rows, cases, *, arms=ARMS, controls=CONTROLS, draws=10000):
    expected = {(c["id"], m) for c in cases for m in arms}
    index = {}
    for row in rows:
        key = (row["id"], row["mode"])
        if key not in expected or key in index:
            raise ValueError("Duplicate or unplanned output")
        index[key] = row
    grouped = {}
    for c in cases:
        grouped.setdefault(c["world_id"], []).append(c)

    def correct(c, mode):
        row = index.get((c["id"], mode), {})
        return int(row.get("status") == "complete" and row.get("label") == c["reference"])

    result = {
        "planned": len(expected),
        "recorded": len(index),
        "worlds": len(grouped),
        "arms": {},
        "comparisons": {},
    }
    for mode in arms:
        subset = [r for r in rows if r["mode"] == mode]
        result["arms"][mode] = dict(
            planned=len(cases),
            recorded=len(subset),
            missing=len(cases) - len(subset),
            complete=sum(r["status"] == "complete" for r in subset),
            correct=sum(correct(c, mode) for c in cases),
            accuracy=sum(correct(c, mode) for c in cases) / len(cases),
            seconds=sum(r.get("seconds", 0) for r in subset),
            by_condition={
                condition: sum(correct(c, mode) for c in cases if c["condition"] == condition)
                / sum(c["condition"] == condition for c in cases)
                for condition in sorted({c["condition"] for c in cases})
            },
        )
    for mode in controls:
        differences = [
            sum(correct(c, "jev") - correct(c, mode) for c in group) / len(group)
            for group in grouped.values()
        ]
        comparison = dict(
            difference=sum(differences) / len(differences),
            wins=sum(d > 0 for d in differences),
            losses=sum(d < 0 for d in differences),
            ties=sum(d == 0 for d in differences),
        )
        if draws:
            rng = random.Random(140920261)
            samples = sorted(
                sum(rng.choices(differences, k=len(differences))) / len(differences)
                for _ in range(draws)
            )
            comparison.update(
                interval=[
                    samples[int(draws * 0.00625)],
                    samples[min(draws - 1, int(draws * 0.99375))],
                ],
                interval_level=0.9875,
            )
        result["comparisons"][mode] = comparison
    result["useful_gain"] = bool(
        draws
        and "native" in result["comparisons"]
        and result["comparisons"]["native"]["difference"] >= 0.03
        and all(c["interval"][0] > 0 for c in result["comparisons"].values())
    )
    return result


class Runner:
    def __init__(self, runtime, output, manifest):
        self.runtime, self.output, self.manifest = runtime, output, manifest
        self.started = time.monotonic()
        self.starts = (output / "starts.jsonl").open("x")
        self.inputs = (output / "inputs.jsonl").open("x")
        self.input_keys, self.job_keys = set(), set()

    def close(self):
        self.starts.close()
        self.inputs.close()

    def deadline(self):
        if time.monotonic() - self.started >= self.manifest["max_seconds"]:
            raise TimeoutError("Frozen study wall-time limit")

    def encoded(self, case, highlights=None):
        encoded = self.runtime.encode(D["model_view"](case), highlights=highlights)
        key = (case["id"], encoded["prompt_digest"])
        if key not in self.input_keys:
            append(self.inputs, {"id": case["id"], **encoded})
            self.input_keys.add(key)
        return encoded

    def forward(self, case, encoded, mode, stream, **kwargs):
        self.deadline()
        key = (case["id"], mode)
        if key in self.job_keys:
            raise ValueError("Started model job cannot be replayed")
        self.job_keys.add(key)
        append(
            self.starts,
            {"kind": "model", "id": case["id"], "mode": mode, "at": datetime.now(UTC).isoformat()},
        )
        try:
            result = self.runtime.forward(encoded, **kwargs)
            row = result[0] if isinstance(result, tuple) else result
            row.update(
                id=case["id"],
                world_id=case["world_id"],
                condition=case["condition"],
                mode=mode.removeprefix("pilot_"),
                operation=mode,
            )
            row["reference_logprob"] = math.log(
                row["label_probabilities"][encoded["labels"].index(case["reference"])]
            )
            row["correct"] = row["label"] == case["reference"]
            append(stream, row)
            return result
        except BaseException as exc:
            append(
                stream,
                {
                    "id": case["id"],
                    "mode": mode,
                    "status": "failed",
                    "error_type": type(exc).__name__,
                },
            )
            raise

    def development(self, profile_worlds, calibration_worlds):
        totals = {
            (layer, h): 0.0
            for layer, module in self.runtime.attention.modules.items()
            for h in range(module.num_heads)
        }
        if len(totals) != 640:
            raise ValueError("Pinned Granite does not expose 640 attention query heads")
        equivalence = []
        with (self.output / "profile.jsonl").open("x") as stream:
            for wi, world in enumerate(profile_worlds):
                c = D["context"](world, "distracted")
                encoded = self.encoded(c)
                native, native_logits = self.forward(c, encoded, "native", stream, full_logits=True)
                zero, zero_logits = self.forward(
                    c,
                    encoded,
                    "zero",
                    stream,
                    heads=[(0, 0)],
                    scores=c["oracle_scores"],
                    strength=0,
                    full_logits=True,
                )
                delta = float((native_logits - zero_logits).abs().max())
                identity = (
                    native["generated_token_ids"] == zero["generated_token_ids"] and delta <= 1e-6
                )
                equivalence.append({"id": c["id"], "max_logit_delta": delta, "identity": identity})
                if not identity:
                    raise ValueError("Zero intervention differs from native")
                for head in totals:
                    row = self.forward(
                        c,
                        encoded,
                        f"head_{head[0]}_{head[1]}",
                        stream,
                        heads=[head],
                        scores=c["oracle_scores"],
                        strength=self.manifest["profile_strength"],
                    )
                    totals[head] += row["reference_logprob"] - native["reference_logprob"]
                print(
                    json.dumps(
                        {
                            "stage": "profile",
                            "worlds_done": wi + 1,
                            "worlds_planned": len(profile_worlds),
                            "elapsed": time.monotonic() - self.started,
                        }
                    ),
                    flush=True,
                )
        ranking = sorted(totals, key=lambda h: (-totals[h], h))
        write(
            self.output / "head-ranking.json",
            [{"head": h, "mean_logprob_change": totals[h] / len(profile_worlds)} for h in ranking],
        )
        write(self.output / "zero-equivalence.json", equivalence)
        conditions = [
            (n, s) for n in self.manifest["head_counts"] for s in self.manifest["strengths"]
        ]
        buckets = {k: [] for k in conditions}
        native_rows = []
        with (self.output / "calibration.jsonl").open("x") as stream:
            for wi, world in enumerate(calibration_worlds):
                for condition in ("clean", "distracted"):
                    c = D["context"](world, condition)
                    encoded = self.encoded(c)
                    native_rows.append(self.forward(c, encoded, "native", stream))
                    for n, strength in conditions:
                        row = self.forward(
                            c,
                            encoded,
                            f"oracle_{n}_{strength:.6f}",
                            stream,
                            heads=ranking[:n],
                            scores=c["oracle_scores"],
                            strength=strength,
                        )
                        buckets[n, strength].append(row)
                if (wi + 1) % 6 == 0:
                    print(
                        json.dumps(
                            {
                                "stage": "calibration",
                                "worlds_done": wi + 1,
                                "elapsed": time.monotonic() - self.started,
                            }
                        ),
                        flush=True,
                    )

        def metrics(rows):
            return dict(
                accuracy=sum(r["correct"] for r in rows) / len(rows),
                clean_accuracy=sum(r["correct"] for r in rows if r["condition"] == "clean")
                / sum(r["condition"] == "clean" for r in rows),
                mean_logprob=sum(r["reference_logprob"] for r in rows) / len(rows),
            )

        outcomes = [dict(count=n, strength=s, **metrics(rows)) for (n, s), rows in buckets.items()]
        native = metrics(native_rows)
        selected = select_policy(outcomes, native["accuracy"], native["clean_accuracy"])
        selected.update(
            heads=ranking[: selected["count"]],
            native=native,
            all_configurations=outcomes,
            frozen_at=datetime.now(UTC).isoformat(),
            source_hashes=sources(),
        )
        others = [h for h in ranking if h not in ranking[: selected["count"]]]
        selected["random_heads"] = random.Random(14092026).sample(sorted(others), selected["count"])
        write(self.output / "selected-policy.json", selected)
        return selected

    async def evaluate(self, cases, selected, scorer, *, name):
        from jev_guided_decoding.types import ScorerError

        E = runpy.run_path(str(HERE / "evidence_scorer.py"))
        rows, incidents = [], 0
        with (
            (self.output / f"{name}.jsonl").open("x") as stream,
            (self.output / f"{name}-scores.jsonl").open("x") as scores_file,
        ):
            for ci, case in enumerate(cases):
                self.deadline()
                view = D["model_view"](case)
                encoded = self.encoded(case)
                append(
                    self.starts,
                    {
                        "kind": "jev",
                        "id": case["id"],
                        "stage": name,
                        "at": datetime.now(UTC).isoformat(),
                    },
                )
                failure, evaluation, recovery_delay = None, None, None
                try:
                    evaluation = await scorer.score(view)
                    append(
                        scores_file,
                        {
                            "id": case["id"],
                            "status": "complete",
                            "payload": E["payload_for"](view, scorer.model),
                            "evaluation": asdict(evaluation),
                        },
                    )
                except ScorerError as exc:
                    failure = failure_info(exc)
                    append(scores_file, {"id": case["id"], "status": "failed", **failure})
                    if name != "test" or failure["status_code"] not in (429, 529) or incidents >= 3:
                        raise
                    incidents += 1
                    recovery_delay = max(60.0, float(failure["retry_after"] or 60))
                    if recovery_delay > 300:
                        raise
                    for key in sorted(scorer.budget.unresolved):
                        scorer.budget.acknowledge_max_charge(
                            key,
                            reason="Explicit rate/overload response without usage",
                            authorization="R14 protocol v1: retain failed context, maximum charge, "
                            "continue never-started contexts",
                        )
                scores = list(evaluation.scores) if evaluation else []
                shuffled = scores.copy()
                random.Random(14000 + ci).shuffle(shuffled)
                order = list(ARMS)
                random.Random(24000 + ci).shuffle(order)
                for mode in order:
                    if mode in DEPENDENT and failure:
                        row = dict(
                            id=case["id"],
                            mode=mode,
                            status="failed",
                            provider_failure=failure,
                            seconds=0,
                        )
                        append(stream, row)
                    else:
                        call_input = encoded
                        kwargs = {}
                        if mode == "prompt":
                            call_input = self.encoded(
                                case,
                                highlights=[
                                    s["id"]
                                    for s, r in zip(view["sources"], scores, strict=True)
                                    if r > 0.5
                                ],
                            )
                        elif mode != "native":
                            map_scores = (
                                [0.0] * len(view["sources"])
                                if mode == "zero"
                                else case["oracle_scores"]
                            )
                            if mode in ("jev", "random_heads"):
                                map_scores = scores
                            elif mode == "shuffled":
                                map_scores = shuffled
                            elif mode == "lexical":
                                map_scores = D["lexical_scores"](view)
                            kwargs = dict(
                                heads=selected["random_heads"]
                                if mode == "random_heads"
                                else selected["heads"],
                                scores=map_scores,
                                strength=0 if mode == "zero" else selected["strength"],
                            )
                        row = self.forward(
                            case,
                            call_input,
                            mode if name == "test" else "pilot_" + mode,
                            stream,
                            **kwargs,
                        )
                        # Pilot operation names avoid replaying earlier calibration-native jobs.
                        if name != "test":
                            row = {**row, "mode": mode}
                    rows.append(row)
                if recovery_delay:
                    await asyncio.sleep(recovery_delay)
                print(
                    json.dumps(
                        {
                            "stage": name,
                            "contexts_done": ci + 1,
                            "planned": len(cases),
                            "elapsed": time.monotonic() - self.started,
                        }
                    ),
                    flush=True,
                )
        result = summarize(
            rows, cases, draws=self.manifest["bootstrap_draws"] if name == "test" else 0
        )
        result["provider_incidents"] = incidents
        write(self.output / f"{name}-summary.json", result)
        return result


async def run(args):
    manifest = json.loads((args.manifest / "manifest.json").read_text())
    if manifest["source_hashes"] != sources():
        raise ValueError("Frozen source changed")
    for split, digest in manifest["dataset_hashes"].items():
        if sha(args.manifest / f"{split}.json") != digest:
            raise ValueError("Frozen dataset changed")
    args.output.mkdir(parents=True, exist_ok=False)
    import torch

    from jev_guided_decoding.backends.transformers import TransformersBackend
    from jev_guided_decoding.experiment_budget import InputTokenBudget
    from jev_guided_decoding.jev import load_api_key

    torch.set_num_threads(2)
    R = runpy.run_path(str(HERE / "evidence_runtime.py"))
    E = runpy.run_path(str(HERE / "evidence_scorer.py"))
    weight_digest = runpy.run_path(str(HERE / "logit_mechanism.py"))["weight_digest"]
    started = time.monotonic()
    base = TransformersBackend.load(
        manifest["model"],
        revision=manifest["revision"],
        device=args.device,
        top_p=1,
        temperature=1,
        local_files_only=args.local_files_only,
    )
    runtime = R["EvidenceRuntime"](base)
    before = weight_digest(base)
    write(
        args.output / "metadata.json",
        dict(
            started_at=datetime.now(UTC).isoformat(),
            source_hashes=sources(),
            model=base.metadata(),
            weights_before=before,
            loading_seconds=time.monotonic() - started,
            manifest_sha256=sha(args.manifest / "manifest.json"),
            source_revision=subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            git_status=subprocess.check_output(
                ["git", "status", "--porcelain"], cwd=ROOT, text=True
            ),
        ),
    )
    runner = Runner(runtime, args.output, manifest)
    completion = {}
    try:
        development = {
            s: json.loads((args.manifest / f"{s}.json").read_text())
            for s in ("profile", "calibration")
        }
        selected = runner.development(development["profile"], development["calibration"])
        completion["oracle_admitted"] = selected["admitted"]
        if selected["admitted"]:
            with InputTokenBudget(args.ledger, max_usd=manifest["api_cap_usd"]) as budget:
                async with E["EvidenceScorer"](
                    load_api_key(), budget=budget, model=manifest["jev_model"]
                ) as scorer:
                    pilot_cases = [
                        D["context"](w, c)
                        for w in development["calibration"][:6]
                        for c in ("clean", "distracted")
                    ]
                    pilot = await runner.evaluate(pilot_cases, selected, scorer, name="pilot")
                    if any(r["complete"] != len(pilot_cases) for r in pilot["arms"].values()):
                        raise ValueError("Incomplete relevance pilot")
                    # Reading held-out cases occurs only after policy and pilot are frozen.
                    cases = [
                        D["context"](w, c)
                        for w in json.loads((args.manifest / "test.json").read_text())
                        for c in ("clean", "distracted")
                    ]
                    write(
                        args.output / "test-freeze.json",
                        dict(
                            at=datetime.now(UTC).isoformat(),
                            selected_policy_sha256=sha(args.output / "selected-policy.json"),
                            source_hashes=sources(),
                            test_data_sha256=sha(args.manifest / "test.json"),
                            planned_contexts=len(cases),
                            arms=ARMS,
                        ),
                    )
                    result = await runner.evaluate(cases, selected, scorer, name="test")
                    completion.update(
                        test_complete=result["recorded"] == result["planned"],
                        useful_gain=result["useful_gain"],
                    )
                completion["ledger"] = dict(
                    charged_input_tokens=budget.charged_tokens, unresolved=len(budget.unresolved)
                )
        else:
            completion["stopped_reason"] = "oracle_headroom_gate_failed"
    except BaseException as exc:
        completion.update(failed=True, error_type=type(exc).__name__, error=str(exc))
        raise
    finally:
        runner.close()
        completion.update(
            weights_before=before,
            weights_after=weight_digest(base),
            elapsed_seconds=time.monotonic() - started,
            finished_at=datetime.now(UTC).isoformat(),
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
