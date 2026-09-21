"""Frozen R13 pilot/full-study runner, independent grades and clustered comparisons."""

import argparse
import asyncio
import hashlib
import json
import os
import random
import runpy
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

from jev_guided_decoding.experiment_budget import InputTokenBudget
from jev_guided_decoding.framing import parse_frame
from jev_guided_decoding.jev import load_api_key
from jev_guided_decoding.local_claims import LocalClaimScorer

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).parent
DATA = runpy.run_path(str(HERE / "structured_data.py"))
CONTROL = runpy.run_path(str(HERE / "structured_controller.py"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def append(stream, value):
    stream.write(json.dumps(value) + "\n")
    stream.flush()
    os.fsync(stream.fileno())


def sources():
    paths = list((ROOT / "src").rglob("*.py")) + list(HERE.glob("*.py")) + [ROOT / "uv.lock"]
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted(paths)}


def prepare(output):
    output.mkdir(parents=True, exist_ok=False)
    for split, count in (("development", 24), ("test", 300)):
        write(output / f"{split}.json", DATA["worlds"](split, count))
    write(
        output / "manifest.json",
        dict(
            schema="structured-study-v2",
            final_grammar=True,
            revision_reason="V1 pilot: 168 jobs complete; 121 valid final formats. "
            "V2 applies all-three-label final syntax equally to every arm. Test remains unseen.",
            created_at=datetime.now(UTC).isoformat(),
            source_revision=subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            source_hashes=sources(),
            dataset_hashes={s: sha(output / f"{s}.json") for s in ("development", "test")},
            model="ibm-granite/granite-4.0-1b",
            revision="6a7381ba1f54d684ff508d991aeb7dc580157103",
            jev_model="jev-1.13.0",
            arms=CONTROL["ARMS"],
            limits=CONTROL["LIMITS"],
            seeds={"development": [41719], "test": [51719, 61719, 71719]},
            temperature=1.0,
            top_p=1.0,
            system=CONTROL["SYSTEM"],
            max_stage_seconds={"development": 1800, "test": 54000},
            budget=dict(
                total_authorized_usd=50,
                prior_estimate_usd=3.2913,
                shared_jev_cap_usd=3,
                new_cloud_cap_usd=30,
                planning_cloud_rate_usd_hour=1.57,
                max_cloud_hours=18,
            ),
            admission=dict(
                all_jobs_complete=True,
                per_arm_format=0.9,
                overall_format=0.95,
                grading_coverage=0.99,
                exact_provenance=True,
                zero_identity=True,
                min_checkpoint_coverage=0.8,
                positive_accuracy_required=False,
            ),
            statistics=dict(
                unit="world, averaging three seeds",
                bootstrap_draws=5000,
                bootstrap_seed=198271,
                primary_controls=["native", "staged", "likelihood"],
                individual_interval_level=1 - 0.05 / 3,
                minimum_worthwhile_difference=0.05,
            ),
            scope="Authored finite unary rule worlds; longer test chains and a different renderer. "
            "Exploratory comparison after an unpassed R12 critic gate, not general math evidence.",
            stopping="Stop on service/backend/integrity errors. Missing/failed jobs are incorrect. "
            "No repeated quality trials; no accuracy-based early stopping.",
        ),
    )


def summarize(rows, cases, seeds, arms, *, bootstrap=0):
    expected = {(c["id"], s, m) for c in cases for s in seeds for m in arms}
    by_key = {}
    for r in rows:
        key = (r["id"], r["seed"], r["mode"])
        if key in by_key:
            raise ValueError("Duplicate study job")
        if key not in expected:
            raise ValueError("Unexpected study job")
        by_key[key] = r

    def correct(case, seed, arm):
        r = by_key.get((case["id"], seed, arm), {})
        return int(r.get("status") == "complete" and r.get("label") == case["reference_label"])

    stats = {}
    for arm in arms:
        subset = [r for r in rows if r["mode"] == arm]
        planned = len(cases) * len(seeds)
        stats[arm] = dict(
            planned=planned,
            recorded=len(subset),
            complete=sum(r["status"] == "complete" for r in subset),
            correct=sum(correct(c, s, arm) for c in cases for s in seeds),
            valid_format=sum(r.get("label") in {"TRUE", "FALSE", "UNKNOWN"} for r in subset),
            seconds=sum(r.get("seconds", 0) for r in subset),
        )
        stats[arm]["accuracy"] = stats[arm]["correct"] / planned
    pairs = matched = 0
    for c in cases:
        for s in seeds:
            a, b = (by_key.get((c["id"], s, m)) for m in ("staged", "zero"))
            if a and b:
                pairs += 1
                matched += int(
                    a.get("status") == b.get("status") == "complete"
                    and a["accepted_ids"] == b["accepted_ids"]
                    and a["final"]["candidate"]["token_ids"] == b["final"]["candidate"]["token_ids"]
                )
    claims = graded = checkpoints = possible = 0
    provider_calls = input_tokens = output_tokens = 0
    max_kl = biased = 0
    for r in rows:
        if r["mode"] in CONTROL["PAID"] or r["mode"] == "likelihood":
            possible += CONTROL["LIMITS"]["steps"]
        for step in r.get("steps", []):
            cp = step.get("checkpoint")
            if not cp:
                continue
            checkpoints += 1
            for b in cp["branches"]:
                claims += 1
                graded += b.get("oracle") is not None
            evaluation = cp.get("evaluation")
            if evaluation:
                provider_calls += evaluation["attempts"]
                input_tokens += evaluation["input_tokens"]
                output_tokens += evaluation["output_tokens"]
            plan = cp.get("selection", {}).get("plan", {})
            max_kl = max(max_kl, plan.get("kl", 0))
            biased += bool(plan.get("bias"))
    audits = sum(
        all(r.get("audit", {}).get(k, False) for k in ("final_tokens", "accepted_tokens", "prompt"))
        for r in rows
    )
    complete = sum(s["complete"] for s in stats.values())
    valid = sum(s["valid_format"] for s in stats.values())
    gates = dict(
        all_complete=complete == len(expected),
        per_arm_format=all(s["valid_format"] / s["planned"] >= 0.9 for s in stats.values()),
        overall_format=valid / len(expected) >= 0.95,
        provenance=audits == len(expected),
        zero_identity=(pairs == len(cases) * len(seeds) and matched == pairs)
        if {"zero", "staged"} <= set(arms)
        else True,
        grading=(graded / claims >= 0.99) if claims else False,
        checkpoints=(checkpoints / possible >= 0.8) if possible else True,
    )
    result = dict(
        planned=len(expected),
        recorded=len(rows),
        missing=len(expected) - len(rows),
        arms=stats,
        zero_identity=dict(matched=matched, pairs=pairs),
        claim_grades=dict(graded=graded, total=claims),
        checkpoints=dict(observed=checkpoints, possible=possible),
        audits=audits,
        gates=gates,
        admitted=all(gates.values()),
        jev=dict(
            calls=provider_calls,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            receipt_cost_usd=input_tokens * 0.042 / 1e6,
        ),
        biased_checkpoints=biased,
        max_kl=max_kl,
        contrasts={},
    )
    if bootstrap and "jev" in arms:
        for arm in ("native", "staged", "likelihood"):
            if arm not in arms:
                continue
            differences = [
                sum(correct(c, s, "jev") - correct(c, s, arm) for s in seeds) / len(seeds)
                for c in cases
            ]
            rng = random.Random(198271)
            draws = sorted(
                sum(rng.choices(differences, k=len(cases))) / len(cases) for _ in range(bootstrap)
            )
            lo, hi = (
                draws[int(bootstrap * 0.05 / 6)],
                draws[min(bootstrap - 1, int(bootstrap * (1 - 0.05 / 6)))],
            )
            difference = sum(differences) / len(differences)
            result["contrasts"]["jev_minus_" + arm] = dict(
                difference=difference,
                interval=[lo, hi],
                level=1 - 0.05 / 3,
                clusters=len(cases),
                draws=bootstrap,
                superiority=difference >= 0.05 and lo > 0,
            )
    return result


def audit(row, view, base):
    accepted = []
    accepted_ok = True
    for step in row["steps"]:
        if step.get("finish_reason") != "frame":
            continue
        ids = list(step["opening_ids"])
        for trace in step["trace"]:
            ids.extend(trace.get("committed_ids", []))
        accepted_ok &= ids == step["token_ids"] and step["before_ids"] == accepted
        accepted.extend(ids)
        for trace in step["trace"]:
            if trace.get("committed_ids") is None:
                accepted_ok = False
    final = row["final"]
    final_ids = tuple(final["candidate"]["token_ids"])
    return dict(
        accepted_tokens=bool(accepted_ok and accepted == row["accepted_ids"]),
        final_tokens=final["prefix_ids"] == accepted + final["opening_ids"]
        and base.decode(tuple(final["prefix_ids"]) + final_ids) == final["candidate"]["full_text"]
        and base.decode(final_ids) == final["decoded_tokens"],
        prompt=list(base.encode(CONTROL["request_for"](view))) == row["prompt_ids"],
    )


async def run_stage(args, manifest, split, base, runtime, scorer):
    cases = json.loads((args.manifest / f"{split}.json").read_text())
    seeds = manifest["seeds"][split]
    folder = args.output / split
    folder.mkdir(exist_ok=False)
    rows = []
    started = time.monotonic()
    failure = None
    with (
        (folder / "runs.jsonl").open("x") as stream,
        (folder / "job-starts.jsonl").open("x") as starts,
    ):
        for case in cases:
            for seed in seeds:
                arms = list(manifest["arms"])
                random.Random(seed + case["index"] * 817).shuffle(arms)
                for mode in arms:
                    if time.monotonic() - started >= manifest["max_stage_seconds"][split]:
                        failure = "stage_time_limit"
                        break
                    record = dict(id=case["id"], seed=seed, mode=mode, status="started")
                    append(starts, {**record, "at": datetime.now(UTC).isoformat()})
                    try:
                        view = DATA["model_view"](case)
                        await CONTROL["run_job"](
                            view,
                            runtime,
                            mode=mode,
                            seed=seed,
                            scorer=scorer,
                            record=record,
                            limits=manifest["limits"],
                            final_grammar=manifest.get("final_grammar", False),
                        )
                        record["audit"] = audit(record, view, base)
                        if not all(record["audit"].values()):
                            raise ValueError("Token/prompt audit failed")
                    except BaseException as exc:
                        failure = type(exc).__name__
                        record.update(status="failed", stage_error=failure)
                    # Oracle runs only after generation, outside the model/scorer input path.
                    for step in record.get("steps", []):
                        for branch in step.get("checkpoint", {}).get("branches", []):
                            branch["oracle"] = (
                                DATA["grade_claim"](case, branch["body"])
                                if "body" in branch
                                else None
                            )
                        if step.get("text"):
                            frame = parse_frame(step["text"])
                            step["oracle"] = (
                                DATA["grade_claim"](case, frame.body) if frame else None
                            )
                    record.update(
                        reference_label=case["reference_label"],
                        motif=case["motif"],
                        depth=case["depth"],
                    )
                    append(stream, record)
                    rows.append(record)
                    print(
                        json.dumps(
                            dict(
                                split=split,
                                done=len(rows),
                                planned=len(cases) * len(seeds) * len(arms),
                                status=record["status"],
                                seconds=round(time.monotonic() - started, 2),
                            )
                        ),
                        flush=True,
                    )
                    if failure:
                        break
                if failure:
                    break
            if failure:
                break
    summary = summarize(
        rows, cases, seeds, manifest["arms"], bootstrap=5000 if split == "test" else 0
    )
    summary.update(elapsed_seconds=time.monotonic() - started, stopped_reason=failure)
    write(folder / "summary.json", summary)
    return summary


async def run(args):
    manifest = json.loads((args.manifest / "manifest.json").read_text())
    if manifest["source_hashes"] != sources():
        raise ValueError("Frozen source changed")
    for split, digest in manifest["dataset_hashes"].items():
        if sha(args.manifest / f"{split}.json") != digest:
            raise ValueError("Frozen data changed")
    args.output.mkdir(parents=True, exist_ok=False)
    import torch

    from jev_guided_decoding.backends.transformers import TransformersBackend

    torch.set_num_threads(2)
    runtime_class = runpy.run_path(str(HERE / "structured_runtime.py"))["StructuredRuntime"]
    weight_digest = runpy.run_path(str(HERE / "logit_mechanism.py"))["weight_digest"]
    load_started = time.monotonic()
    base = TransformersBackend.load(
        manifest["model"],
        revision=manifest["revision"],
        device=args.device,
        temperature=manifest["temperature"],
        top_p=manifest["top_p"],
        local_files_only=args.local_files_only,
    )
    runtime = runtime_class(base)
    before = weight_digest(base)
    case = DATA["model_view"](DATA["worlds"]("development", 1)[0])
    grammar, opening = runtime.make_grammar(case["entities"], case["properties"])
    runtime.inspect(
        base.encode(CONTROL["request_for"](case)), opening, allowed=grammar.allowed(opening)
    )
    write(
        args.output / "metadata.json",
        dict(
            started_at=datetime.now(UTC).isoformat(),
            loading_seconds=time.monotonic() - load_started,
            manifest_sha256=sha(args.manifest / "manifest.json"),
            source_hashes=sources(),
            model=base.metadata(),
            weights_before=before,
            git_status=subprocess.check_output(
                ["git", "status", "--porcelain"], cwd=ROOT, text=True
            ),
        ),
    )
    result = {}
    with InputTokenBudget(args.ledger, max_usd=3) as budget:
        async with LocalClaimScorer(
            load_api_key(), model=manifest["jev_model"], budget=budget
        ) as scorer:
            pilot = await run_stage(args, manifest, "development", base, runtime, scorer)
            result["pilot_admitted"] = pilot["admitted"]
            estimated = pilot["elapsed_seconds"] * 6300 / 168 * 1.5 + 1800
            result["conservative_main_seconds"] = estimated
            result["projected_new_cloud_usd"] = (
                (estimated + pilot["elapsed_seconds"] + 1800) / 3600 * 1.57
            )
            if (
                pilot["admitted"]
                and estimated < manifest["max_stage_seconds"]["test"]
                and result["projected_new_cloud_usd"] < 30
            ):
                if not args.pilot_only:
                    main = await run_stage(args, manifest, "test", base, runtime, scorer)
                    result["main_complete"] = (
                        main["missing"] == 0 and main["stopped_reason"] is None
                    )
            result["ledger"] = dict(
                charged_input_tokens=budget.charged_tokens, unresolved=len(budget.unresolved)
            )
    result.update(weights_after=weight_digest(base), weights_before=before)
    result["weights_unchanged"] = result["weights_after"] == before
    write(args.output / "completion.json", result)
    print(json.dumps(result), flush=True)
    return 0 if result.get("main_complete") and result["weights_unchanged"] else 2


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
    p.add_argument("--pilot-only", action="store_true")
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.output)
        return 0
    return asyncio.run(run(args))


if __name__ == "__main__":
    raise SystemExit(main())
