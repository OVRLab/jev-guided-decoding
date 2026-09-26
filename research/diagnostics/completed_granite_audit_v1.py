"""Audit nine complete R27 systems without admitting or grading partial Qwen."""

import argparse
import importlib.util
import json
import math
import runpy
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
V = runpy.run_path(str(Path(__file__).with_name("benchmark_execution_v3_audit.py")))
R = runpy.run_path(str(ROOT / "research/iterations/benchmark_recovery_v2/state.py"))
REPORT = runpy.run_path(str(ROOT / "research/evaluation/tranche_report_v1.py"))
A, C, K = V["A"], V["C"], V["K"]
COMPLETE_MODELS = ("granite_4_0_1b", "granite_4_2_3b")
PARTIAL_MODEL = "qwen3_4b_instruct"
SYSTEMS = tuple(s for s in REPORT["SYSTEMS"] if s != PARTIAL_MODEL)
lines, unique = R["V1"]["lines"], V["unique"]


def check_scope(cases, rows, unfinished):
    if not cases:
        raise ValueError("Empty scope")
    unique(rows, lambda r: (r["model"], r["arm"], r["id"]))
    for row in rows:
        if (
            row["model"] not in (*COMPLETE_MODELS, PARTIAL_MODEL)
            or row["id"] not in cases
            or row["arm"] not in {*A["ARMS"], "native", "warmup", "serial_probe", "self_refine"}
            or (row["model"] != "granite_4_0_1b" and row["arm"] not in ("native", "warmup"))
        ):
            raise ValueError("Unregistered model, case or arm")
    for model, arm in [
        *((m, "native") for m in COMPLETE_MODELS),
        ("granite_4_0_1b", "self_refine"),
    ]:
        if {r["id"] for r in rows if r["model"] == model and r["arm"] == arm} != set(cases):
            raise ValueError("Incomplete required Granite coverage")
    if len(unfinished) > 1:
        raise ValueError("Multiple unfinished jobs")
    for job in unfinished:
        if (
            job["model"] != PARTIAL_MODEL
            or job["arm"] != "native"
            or len(job["ids"]) != 1
            or job["ids"][0] not in cases
            or any(
                r["model"] == PARTIAL_MODEL and r["arm"] == "native" and r["id"] in job["ids"]
                for r in rows
            )
        ):
            raise ValueError("Invalid unfinished job in completed-system scope")
    return {
        task: {
            "planned": sum(c["task"] == task for c in cases.values()),
            **{
                m: sum(
                    r["model"] == m and r["arm"] == "native" and cases[r["id"]]["task"] == task
                    for r in rows
                )
                for m in (*COMPLETE_MODELS, PARTIAL_MODEL)
            },
        }
        for task in sorted({c["task"] for c in cases.values()})
    }


def check_weights(profile, hardware, complete):
    if (
        hardware.get("profile") != profile
        or complete.get("weights_unchanged") is not True
        or not hardware.get("original_weights_sha256")
        or hardware["original_weights_sha256"] != complete.get("weights_sha256")
    ):
        raise ValueError("Completed model profile/weight evidence mismatch")


def check_evaluator(manifest, evaluator, requirements):
    expected = manifest["external_evaluation"]
    if (
        requirements is None
        or C["sha"](evaluator) != expected["ifbench_evaluator_sha256"]
        or C["sha"](requirements) != expected["ifbench_environment_sha256"]
        or expected["language_seed"] != 2701
    ):
        raise ValueError("IFBench evaluator/environment/seed mismatch")


def verify_sources(output):
    inventories = [json.loads((output / "recovery-sources.json").read_text())]
    inventories += [r["files"] for r in lines(output / "recovery-chain-sources.jsonl")]
    if len(inventories) != len(lines(output / "recovery-chain.jsonl")) + 1:
        raise ValueError("Missing continuation source envelope")
    for inventory in inventories:
        for name, digest in inventory.items():
            path = (ROOT / name).resolve()
            if not path.is_relative_to(ROOT.resolve()) or C["sha"](path) != digest:
                raise ValueError("Continuation source changed")
    for numerical in output.glob("*cache-admission.json"):
        V["check_numerical"](json.loads(numerical.read_text()))


def select_complete(cases, rows, decisions, feedback, donors):
    by_key = unique(rows, lambda r: (r["model"], r["arm"], r["id"]))
    expected = {}
    for task in {c["task"] for c in cases.values()}:
        ids = sorted(i for i, c in cases.items() if c["task"] == task)
        expected.update({i: ids[(n + 1) % len(ids)] for n, i in enumerate(ids)})
    if set(feedback) != set(cases) or donors != expected:
        raise ValueError("Feedback/donor coverage mismatch")
    if set(decisions) != {(arm, i) for arm in A["ARMS"] for i in cases}:
        raise ValueError("Selective decision coverage mismatch")
    native = {r["id"]: r for r in rows if r["model"] == "granite_4_0_1b" and r["arm"] == "native"}
    selected = {"original": native}
    for system, model, arm in [
        ("self_refine", "granite_4_0_1b", "self_refine"),
        ("granite_4_2_3b", "granite_4_2_3b", "native"),
    ]:
        selected[system] = {r["id"]: r for r in rows if r["model"] == model and r["arm"] == arm}
    for arm in A["ARMS"]:
        selected["guided" if arm == "live" else arm] = {}
    for (arm, ident), decision in decisions.items():
        if decision["donor_id"] != donors[ident]:
            raise ValueError("Donor binding mismatch")
        chosen = V["check_selection"](
            decision,
            native[ident],
            by_key.get(("granite_4_0_1b", arm, ident)),
            feedback[ident]["actual_probability_correct"],
            feedback[donors[ident]]["actual_probability_correct"],
        )
        selected["guided" if arm == "live" else arm][ident] = chosen
    if set(selected) != set(SYSTEMS) or any(set(x) != set(cases) for x in selected.values()):
        raise ValueError("Incomplete selected system")
    return selected


def analyze(folder, output, ancestors, *, tokenizers, ifbench=None):
    m = json.loads((folder / "manifest.json").read_text())
    A["verify_bindings"](folder, m)
    if m["models"] != A["MODELS"] or set(tokenizers) != set(m["models"]):
        raise ValueError("Model/tokenizer scope mismatch")
    if m["protocol"] != "r27-benchmark-execution-v2" or m["batch_size"] != 1:
        raise ValueError("Wrong protocol")
    if not ancestors or Path(ancestors[-1]).resolve() != output.resolve():
        raise ValueError("Final ancestry/output mismatch")
    lineage = R["verify_chain"](ancestors)
    verify_sources(output)
    if C["sha"](folder / "references.json") != m["references_sha256"]:
        raise ValueError("Reference hash mismatch")
    if json.loads((output / "start.json").read_text())["manifest_sha256"] != C["sha"](
        folder / "manifest.json"
    ):
        raise ValueError("Run manifest mismatch")
    cases = unique(json.loads((folder / "cases.json").read_text()), lambda r: r["id"])
    refs = unique(json.loads((folder / "references.json").read_text()), lambda r: r["id"])
    if set(cases) != set(refs) or any(
        refs[i]["prompt_sha256"] != C["digest"](c["prompt"]) for i, c in cases.items()
    ):
        raise ValueError("Reference case binding mismatch")
    rows = lines(output / "outputs.jsonl")
    _, _, _, unfinished = R["V1"]["journal"](output)
    coverage = check_scope(cases, rows, unfinished)
    for task, counts in coverage.items():
        if task not in REPORT["COUNTS"] or counts["planned"] != REPORT["COUNTS"][task][0]:
            raise ValueError("Unexpected full-task denominator")
        if (
            sum(c["task"] == task and c["split"] == "test" for c in cases.values())
            != REPORT["COUNTS"][task][1]
        ):
            raise ValueError("Unexpected untouched denominator")
    if "ifbench" in coverage and ifbench is None:
        raise ValueError("Independent IFBench evaluator required")
    batches = unique(lines(output / "batches.jsonl"), lambda r: r["batch_id"])
    grouped = defaultdict(list)
    for row in rows:
        case = cases[row["id"]]
        if row["seed"] != K["case_seed"](row["id"], m["seed"]) or any(
            row[k] != case[k] for k in ("task", "family")
        ):
            raise ValueError("Task or seed mismatch")
        grouped[row["batch_id"]].append(row)
    work = {k: V["check_batch"](b, grouped[k]) for k, b in batches.items()}
    if any(b["batch_size"] != 1 for b in batches.values()):
        raise ValueError("Nonserial batch")
    models = {}
    for name, config in m["models"].items():
        model_rows = [r for r in rows if r["model"] == name]
        native = {r["id"]: r for r in model_rows if r["arm"] == "native"}
        expected = (
            set(sorted(cases, key=lambda i: C["digest"]("serial/" + i))[:3])
            if name == "granite_4_0_1b"
            else set()
        )
        V["check_profile_order"](cases, model_rows, 1, serial_ids=expected)
        hardware = json.loads((output / (name + "-hardware.json")).read_text())
        if hardware["profile"] != config:
            raise ValueError("Model profile mismatch")
        if name in COMPLETE_MODELS:
            check_weights(
                config, hardware, json.loads((output / (name + "-complete.json")).read_text())
            )
        for path in output.glob("*" + name + "-hardware.json"):
            resumed = json.loads(path.read_text())
            if any(
                resumed[k] != hardware[k] for k in ("profile", "original_weights_sha256", "eos_ids")
            ):
                raise ValueError("Recovery model binding mismatch")
        for row in model_rows:
            V["check_output"](
                cases[row["id"]],
                row,
                tokenizers[name],
                config,
                hardware["eos_ids"],
                native[row["id"]] if row["arm"] in {*A["ARMS"], "self_refine"} else None,
            )
        repeats = [r for r in model_rows if r["arm"] == "serial_probe"]
        if {r["id"] for r in repeats} != expected or sum(
            r["arm"] == "warmup" for r in model_rows
        ) != 1:
            raise ValueError("Probe coverage mismatch")
        if any(r["generated_token_ids"] != native[r["id"]]["generated_token_ids"] for r in repeats):
            raise ValueError("Greedy repeat token mismatch")
        models[name] = dict(
            native_cases=len(native),
            parameters=hardware["parameters"],
            complete=name in COMPLETE_MODELS,
        )
    feedback = unique(lines(output / "feedback.jsonl"), lambda r: r["id"])
    decisions = unique(lines(output / "decisions.jsonl"), lambda r: (r["arm"], r["id"]))
    selected = select_complete(
        cases, rows, decisions, feedback, json.loads((output / "donors.json").read_text())
    )
    delivery = V["check_delivery"](output, cases, selected["original"], m)
    api = json.loads((output / "api-summary.json").read_text())
    if (
        api["usd"] != delivery["usd"]
        or api["unresolved"] != 0
        or api["max_charged"] != delivery["unknown_attempts"]
        or api["charged_tokens"]
        != delivery["known_input_tokens"] + 65536 * delivery["unknown_attempts"]
    ):
        raise ValueError("API summary mismatch")
    if max(r["at"] for r in selected["self_refine"].values()) >= min(
        r["at"] for r in lines(output / "requests.jsonl")
    ):
        raise ValueError("Jev-free baseline ordering mismatch")
    # All integrity gates precede the first quality grade.
    untouched = {i: c for i, c in cases.items() if c["split"] == "test"}
    quality = V["score_selected"](cases, refs, selected, ifbench=ifbench)
    fresh = V["score_selected"](
        untouched,
        {i: refs[i] for i in untouched},
        {s: {i: r[i] for i in untouched} for s, r in selected.items()},
        ifbench=ifbench,
    )
    return dict(
        scope="nine-complete-granite-systems-v1",
        completed_scope_admitted=True,
        full_tranche_admitted=False,
        audited_records=True,
        tokenizers_checked=True,
        quality=quality,
        untouched_quality=fresh,
        coverage=coverage,
        models=models,
        lineage=lineage,
        unfinished_model_jobs=len(unfinished),
        delivery=delivery,
        total_work={k: sum(w[k] for w in work.values()) for k in next(iter(work.values()))},
        profile_work={
            name + "/" + arm: {
                k: sum(
                    work[r["batch_id"]][k] for r in rows if r["model"] == name and r["arm"] == arm
                )
                for k in next(iter(work.values()))
            }
            for name, arm in sorted({(r["model"], r["arm"]) for r in rows})
        },
        repair_cases=sum(d["repair_executed"] for d in decisions.values()) // len(A["ARMS"]),
        source_sha256=C["sha"](Path(__file__)),
        frozen_auditor_sha256=C["sha"](Path(__file__).with_name("benchmark_execution_v3_audit.py")),
        manifest_sha256=C["sha"](folder / "manifest.json"),
        input_files={p.name: C["sha"](p) for p in output.iterdir() if p.is_file()},
        token_work_is_lower_bound=True,
        interrupted_partial_work_unmeasured=True,
    )


def public_quality(audit, *, tasks):
    if not all(
        audit.get(k) is True
        for k in ("completed_scope_admitted", "audited_records", "tokenizers_checked")
    ):
        raise ValueError("Independent completed-system audit required")
    if not tasks or len(set(tasks)) != len(tasks) or set(tasks) - REPORT["COUNTS"].keys():
        raise ValueError("Unsupported task scope")
    count, number, interval = REPORT["count"], REPORT["number"], REPORT["interval"]

    def extract(quality, index):
        if set(quality["summaries"]) != set(SYSTEMS):
            raise ValueError("Wrong completed systems")
        summaries = {}
        for system, values in quality["summaries"].items():
            if set(values) != set(tasks):
                raise ValueError("Task coverage mismatch")
            summaries[system] = {}
            for task, row in values.items():
                n = REPORT["COUNTS"][task][index]
                if type(row["total"]) is not int or row["total"] != n:
                    raise ValueError("Incomplete task denominator")
                correct, accuracy = count(row["correct"], n), number(row["accuracy"], 0, 1)
                if not math.isclose(accuracy, correct / n, rel_tol=0, abs_tol=1e-12):
                    raise ValueError("Score/count mismatch")
                summaries[system][task] = dict(
                    correct=correct,
                    total=n,
                    accuracy=accuracy,
                    wilson_95=interval(row["wilson_95"], 0, 1),
                    **{
                        k: count(row[k], n)
                        for k in ("unparseable", "length_stops", "unfinished_thinking")
                    },
                    **(
                        {"loose_correct": count(row["loose_correct"], n)}
                        if task == "ifbench"
                        else {}
                    ),
                )
        pairs = {}
        for name, values in quality["paired_differences"].items():
            if name not in {f"{a}-{b}" for a in SYSTEMS for b in SYSTEMS if a != b} or set(
                values
            ) != set(tasks):
                raise ValueError("Invalid paired scope")
            pairs[name] = {}
            for task, row in values.items():
                n = REPORT["COUNTS"][task][index]
                wins, losses = count(row["wins"], n), count(row["losses"], n)
                if (
                    row["pairs"] != n
                    or row["confirmatory_superiority"] is not False
                    or wins + losses > n
                    or not math.isclose(row["difference"], (wins - losses) / n, abs_tol=1e-12)
                ):
                    raise ValueError("Invalid paired counts")
                pairs[name][task] = dict(
                    pairs=n,
                    clusters=count(row["clusters"], n),
                    wins=wins,
                    losses=losses,
                    difference=number(row["difference"], -1, 1),
                    descriptive_paired_95=interval(row["descriptive_paired_95"], -1, 1),
                    confirmatory_superiority=False,
                )
        return dict(summaries=summaries, paired_differences=pairs)

    return dict(
        full=extract(audit["quality"], 0),
        untouched=extract(audit["untouched_quality"], 1),
        full_tranche_admitted=False,
        ten_task_mean=None,
        superiority_established=False,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ancestor", type=Path, action="append", required=True)
    parser.add_argument("--write", type=Path, required=True)
    parser.add_argument("--ifbench-evaluator", type=Path)
    parser.add_argument("--ifbench-site-packages", type=Path)
    parser.add_argument("--ifbench-requirements", type=Path)
    args = parser.parse_args()
    if args.write.exists():
        raise ValueError("Refuse to overwrite an existing audit")
    from transformers import AutoTokenizer

    toks = {
        name: AutoTokenizer.from_pretrained(
            c["id"], revision=c["revision"], trust_remote_code=False, local_files_only=True
        )
        for name, c in A["MODELS"].items()
    }
    evaluator = None
    if args.ifbench_evaluator:
        manifest = json.loads((args.freeze / "manifest.json").read_text())
        check_evaluator(manifest, args.ifbench_evaluator, args.ifbench_requirements)
        if args.ifbench_site_packages:
            sys.path.append(str(args.ifbench_site_packages))
        spec = importlib.util.spec_from_file_location(
            "r27_ifbench_evaluator", args.ifbench_evaluator
        )
        evaluator = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = evaluator
        spec.loader.exec_module(evaluator)
    result = analyze(args.freeze, args.output, args.ancestor, tokenizers=toks, ifbench=evaluator)
    result["ifbench_evaluator_sha256"] = (
        C["sha"](args.ifbench_evaluator) if args.ifbench_evaluator else None
    )
    C["dump"](args.write, result)
    args.write.chmod(0o600)
