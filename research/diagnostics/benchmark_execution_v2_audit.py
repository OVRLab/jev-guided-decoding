"""Independent R27 token/work/selection audit; no model-generated content is executed."""

import argparse
import copy
import importlib.util
import json
import math
import random
import runpy
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OLD = runpy.run_path(str(Path(__file__).with_name("selective_admission_audit.py")))
A, C = OLD["A"], OLD["C"]
K = runpy.run_path(str(ROOT / "research/iterations/benchmark_execution_v2/contract.py"))
G = runpy.run_path(str(ROOT / "research/evaluation/choice_readout_v2.py"))
lines, unique = OLD["lines"], OLD["unique"]
check_batch, check_selection = OLD["check_batch"], OLD["check_selection"]
check_delivery, check_numerical = OLD["check_delivery"], OLD["check_numerical"]
check_profile_order = OLD["check_profile_order"]
project_cost, project_stratified_cost = OLD["project_cost"], OLD["project_stratified_cost"]


def score_selected(cases, refs, selected, *, ifbench=None):
    grades, summaries = {}, {}
    for name, outputs in selected.items():
        if set(outputs) != set(cases) or set(refs) != set(cases):
            raise ValueError("Selected answer coverage mismatch")
        values = {}
        for ident, row in outputs.items():
            ref, case = refs[ident], cases[ident]
            if ref["kind"] == "ifbench":
                if ifbench is None:
                    raise ValueError("Independent IFBench evaluator required")
                from langdetect import DetectorFactory

                # Its default seed is None; fix stochastic language detection
                # before any R27 IFBench grading, including the exposed pilot.
                DetectorFactory.seed = 2701
                common = runpy.run_path(
                    str(ROOT / "research/iterations/benchmark_baseline/common.py")
                )

                def score(mode, ref=ref, case=case, row=row, common=common):
                    example = ifbench.InputExample(
                        key=ref["key"],
                        prompt=case["prompt"],
                        instruction_id_list=ref["instruction_id_list"],
                        kwargs=common["ifbench_kwargs"](copy.deepcopy(ref["kwargs"])),
                    )
                    result = getattr(ifbench, "test_instruction_following_" + mode)(
                        example, {case["prompt"]: row["final"]}
                    )
                    return bool(result.follow_all_instructions)

                grade = dict(
                    correct=score("strict"), loose=score("loose"), parseable=bool(row["final"])
                )
            else:
                grade = G["grade"](ref, row["final"])
            # No questions, options, reference answers or generated text in quality exports.
            values[ident] = {k: grade[k] for k in ("correct", "parseable", "loose") if k in grade}
        grades[name] = values
        summaries[name] = {}
        for task in sorted({c["task"] for c in cases.values()}):
            ids = [i for i, c in cases.items() if c["task"] == task]
            n, correct = len(ids), sum(values[i]["correct"] for i in ids)
            p, z = correct / n, 1.959963984540054
            center = (p + z * z / (2 * n)) / (1 + z * z / n)
            delta = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
            summaries[name][task] = dict(
                correct=correct,
                total=n,
                accuracy=correct / n,
                wilson_95=[center - delta, center + delta],
                unparseable=sum(not values[i]["parseable"] for i in ids),
                length_stops=sum(outputs[i].get("finish_reason") == "length" for i in ids),
                unfinished_thinking=sum(
                    outputs[i].get("status") == "unfinished_thinking" for i in ids
                ),
                **(
                    {"loose_correct": sum(values[i]["loose"] for i in ids)}
                    if task == "ifbench"
                    else {}
                ),
            )
    paired = {}
    for name in selected:
        for baseline in selected:
            if name == baseline or (baseline != "original" and name != "guided"):
                continue
            tasks = {}
            for task in summaries[name]:
                ids = [i for i, c in cases.items() if c["task"] == task]
                diffs = {
                    i: int(grades[name][i]["correct"]) - int(grades[baseline][i]["correct"])
                    for i in ids
                }
                clusters = defaultdict(list)
                for ident in ids:
                    clusters[cases[ident]["cluster"]].append(diffs[ident])
                units = [(sum(v), len(v)) for v in clusters.values()]
                rng = random.Random(2701)
                draws = []
                for _ in range(10000):
                    sample = rng.choices(units, k=len(units))
                    draws.append(sum(v[0] for v in sample) / sum(v[1] for v in sample))
                draws.sort()
                tasks[task] = dict(
                    difference=sum(diffs.values()) / len(ids),
                    wins=sum(v == 1 for v in diffs.values()),
                    losses=sum(v == -1 for v in diffs.values()),
                    pairs=len(ids),
                    clusters=len(units),
                    descriptive_paired_95=[draws[249], draws[9749]],
                    confirmatory_superiority=False,
                )
            paired[name + "-" + baseline] = tasks
    return dict(
        summaries=summaries,
        paired_differences=paired,
        grades=grades,
        interpretation="Frozen task-specific comparisons; no ten-task aggregate",
    )


def check_output(case, row, tok, config, eos, native=None):
    if row["arm"] not in {*A["ARMS"], "native", "warmup", "serial_probe", "self_refine"}:
        raise ValueError("Unknown model arm")
    if row["id"] != case["id"] or row["prompt_sha256"] != C["digest"](case["prompt"]):
        raise ValueError("Output question binding mismatch")
    prompt = tok.apply_chat_template(
        [dict(role="user", content=case["prompt"])],
        tokenize=True,
        add_generation_prompt=True,
        **({"enable_thinking": True} if config["thinking"] else {}),
    )
    if native is not None:
        prompt = C["repair_prefix"](tok, prompt, native["generated_token_ids"], case["format"])
    ids = row["generated_token_ids"]
    if not ids or row["prompt_token_ids"] != prompt or any(type(t) is not int for t in ids):
        raise ValueError("Exact token prefix or output mismatch")
    stopped = ids[-1] in eos
    limit = (
        8 if row["arm"] == "warmup" else 2048 if native is not None else config["max_new_tokens"]
    )
    text = tok.decode(ids[:-1] if stopped else ids, skip_special_tokens=False)
    terminal = K["terminal_line"](text, case["format"], config["thinking"])
    reason = "eos" if stopped else "terminal_line" if terminal else "length"
    if (
        any(t in eos for t in ids[:-1])
        or len(ids) > limit
        or row["finish_reason"] != reason
        or (reason == "length" and len(ids) != limit)
        or (
            not stopped
            and len(ids) > 1
            and K["terminal_line"](
                tok.decode(ids[:-1], skip_special_tokens=False), case["format"], config["thinking"]
            )
        )
    ):
        raise ValueError("EOS/terminal/limit stop mismatch")
    final = (
        text.rsplit("</think>", 1)[1].strip()
        if config["thinking"] and "</think>" in text
        else ("" if config["thinking"] else text.strip())
    )
    status = (
        "unfinished_thinking"
        if config["thinking"] and "</think>" not in text
        else "complete"
        if final
        else "empty"
    )
    if row["text"] != text or row["final"] != final or row["status"] != status:
        raise ValueError("Decoded output mismatch")
    hooked = row["arm"] in set(A["ARMS"]) - {"blind"}
    events = row["events"]
    if hooked:
        if len(events) != len(ids):
            raise ValueError("Hook event count mismatch")
        for i, event in enumerate(events):
            if (
                event["layer"] != 19
                or event["positions"] != [len(prompt) - 1 + i]
                or event["feedback"] != [row["gate"], row["gate"]]
                or not math.isfinite(event["relative_delta"])
            ):
                raise ValueError("Hook position or strength mismatch")
    elif events or row["gate"] is not None:
        raise ValueError("Unexpected native/blind intervention")


def analyze(folder, output, *, tokenizers=None, ifbench=None):
    m = json.loads((folder / "manifest.json").read_text())
    A["verify_bindings"](folder, m)
    if m["protocol"] != "r27-benchmark-execution-v2" or m["batch_size"] != 1:
        raise ValueError("Wrong R27 protocol")
    if C["sha"](folder / "references.json") != m["references_sha256"]:
        raise ValueError("Reference hash mismatch")
    check_numerical(json.loads((output / "cache-admission.json").read_text()))
    if json.loads((output / "start.json").read_text())["manifest_sha256"] != C["sha"](
        folder / "manifest.json"
    ):
        raise ValueError("Run manifest mismatch")
    cases = unique(json.loads((folder / "cases.json").read_text()), lambda r: r["id"])
    refs = unique(json.loads((folder / "references.json").read_text()), lambda r: r["id"])
    if set(cases) != set(refs):
        raise ValueError("Reference coverage mismatch")
    for ident, c in cases.items():
        if refs[ident]["prompt_sha256"] != C["digest"](c["prompt"]):
            raise ValueError("Reference question binding mismatch")
    rows = lines(output / "outputs.jsonl")
    by_key = unique(rows, lambda r: (r["model"], r["arm"], r["id"]))
    batches = unique(lines(output / "batches.jsonl"), lambda r: r["batch_id"])
    grouped = defaultdict(list)
    for r in rows:
        if (
            r["model"] not in m["models"]
            or r["arm"] not in {*A["ARMS"], "native", "warmup", "serial_probe", "self_refine"}
            or (r["arm"] in {*A["ARMS"], "self_refine"} and r["model"] != "granite_4_0_1b")
        ):
            raise ValueError("Unregistered model arm")
        case = cases[r["id"]]
        if (
            r["seed"] != K["case_seed"](r["id"], m["seed"])
            or r["task"] != case["task"]
            or r["family"] != case["family"]
        ):
            raise ValueError("Task or request seed mismatch")
        grouped[r["batch_id"]].append(r)
    if set(grouped) != set(batches):
        raise ValueError("Batch coverage mismatch")
    work = {k: check_batch(b, grouped[k]) for k, b in batches.items()}
    if any(b["batch_size"] != 1 for b in batches.values()):
        raise ValueError("Nonserial work under serial protocol")
    jobs = lines(output / "jobs.jsonl")
    starts = unique([r for r in jobs if r["event"] == "start"], lambda r: r["batch_id"])
    ends = unique([r for r in jobs if r["event"] == "finish"], lambda r: r["batch_id"])
    if set(starts) != set(ends) or set(starts) != set(batches) or len(jobs) != 2 * len(batches):
        raise ValueError("Incomplete model job")
    for k, b in batches.items():
        a, z = starts[k], ends[k]
        if any(a[field] != z[field] for field in ("model", "arm", "ids")) or a["at"] > z["at"]:
            raise ValueError("Model job binding mismatch")
        if a["ids"] != [r["id"] for r in grouped[k]] or any(a[f] != b[f] for f in ("model", "arm")):
            raise ValueError("Model batch binding mismatch")
    models = {}
    for name, config in m["models"].items():
        native = {r["id"]: r for r in rows if r["model"] == name and r["arm"] == "native"}
        if set(native) != set(cases):
            raise ValueError("Incomplete primary model")
        check_profile_order(cases, [r for r in rows if r["model"] == name], m["batch_size"])
        hardware = json.loads((output / (name + "-hardware.json")).read_text())
        complete = json.loads((output / (name + "-complete.json")).read_text())
        if (
            hardware["profile"] != config
            or not complete["weights_unchanged"]
            or hardware["original_weights_sha256"] != complete["weights_sha256"]
        ):
            raise ValueError("Model profile/weight mismatch")
        if tokenizers:
            for r in rows:
                if r["model"] == name:
                    check_output(
                        cases[r["id"]],
                        r,
                        tokenizers[name],
                        config,
                        hardware["eos_ids"],
                        native[r["id"]] if r["arm"] in {*A["ARMS"], "self_refine"} else None,
                    )
        serial = {r["id"] for r in rows if r["model"] == name and r["arm"] == "serial_probe"}
        expected = (
            set(sorted(cases, key=lambda ident: C["digest"]("serial/" + ident))[:3])
            if name == "granite_4_0_1b"
            else set()
        )
        if (
            serial != expected
            or sum(r["model"] == name and r["arm"] == "warmup" for r in rows) != 1
        ):
            raise ValueError("Timing probe coverage mismatch")
        graded = [
            G["grade"](refs[i], r["final"])
            for i, r in native.items()
            if cases[i]["format"] != "instruction"
        ]
        models[name] = dict(
            native_cases=len(native),
            parseable=sum(r["parseable"] for r in graded),
            graded_cases=len(graded),
            correct=sum(r["correct"] for r in graded),
            cutoffs=sum(r["finish_reason"] == "length" for r in native.values()),
            unfinished=sum(r["status"] == "unfinished_thinking" for r in native.values()),
            greedy_repeat_exact_outputs=sum(
                r["generated_token_ids"] == native[r["id"]]["generated_token_ids"]
                for r in rows
                if r["model"] == name and r["arm"] == "serial_probe"
            ),
            parameters=hardware["parameters"],
            load_seconds=hardware["load_seconds"],
        )
        if name == "granite_4_0_1b" and models[name]["greedy_repeat_exact_outputs"] != 3:
            raise ValueError("Greedy repeat token mismatch")
    native = {r["id"]: r for r in rows if r["model"] == "granite_4_0_1b" and r["arm"] == "native"}
    feedback = unique(lines(output / "feedback.jsonl"), lambda r: r["id"])
    donors = json.loads((output / "donors.json").read_text())
    expected_donors = {}
    for task in {c["task"] for c in cases.values()}:
        ids = sorted(i for i, c in cases.items() if c["task"] == task)
        expected_donors.update({ident: ids[(i + 1) % len(ids)] for i, ident in enumerate(ids)})
    if set(feedback) != set(cases) or donors != expected_donors:
        raise ValueError("Feedback/donor coverage mismatch")
    decisions = unique(lines(output / "decisions.jsonl"), lambda r: (r["arm"], r["id"]))
    if set(decisions) != {(arm, i) for arm in A["ARMS"] for i in cases}:
        raise ValueError("Selective decision coverage mismatch")
    selected = {"original": native}
    selected["self_refine"] = {
        r["id"]: r for r in rows if r["model"] == "granite_4_0_1b" and r["arm"] == "self_refine"
    }
    for name in m["models"]:
        if name != "granite_4_0_1b":
            selected[name] = {
                r["id"]: r for r in rows if r["model"] == name and r["arm"] == "native"
            }
    for arm in A["ARMS"]:
        selected["guided" if arm == "live" else arm] = {}
    repairs = 0
    for (arm, ident), d in decisions.items():
        if d["donor_id"] != donors[ident]:
            raise ValueError("Donor binding mismatch")
        chosen = check_selection(
            d,
            native[ident],
            by_key.get(("granite_4_0_1b", arm, ident)),
            feedback[ident]["actual_probability_correct"],
            feedback[donors[ident]]["actual_probability_correct"],
        )
        selected["guided" if arm == "live" else arm][ident] = chosen
        repairs += d["repair_executed"]
    profiles = {}
    counts = dict(
        mmlu_pro=12032,
        musr=756,
        ifbench=300,
        aime2026=30,
        gpqa_diamond=198,
        longbench_v2=503,
        simpleqa_verified=1000,
        livecodebench=None,
        bfcl_v4=None,
        swe_bench=500,
    )
    for name in m["models"]:
        profile = []
        for r in rows:
            if r["model"] == name and r["arm"] == "native":
                profile.append(
                    dict(
                        task=r["task"],
                        seconds=batches[r["batch_id"]]["seconds"]
                        / batches[r["batch_id"]]["batch_size"],
                    )
                )
        profiles[name] = project_cost(profile, counts, 1.7545808219178083)
    inventory_path = ROOT / "reports/2026-09-24-selective-admission/source-inventory.json"
    inventory = json.loads(inventory_path.read_text())["primary"]
    strata = dict(
        mmlu_pro=inventory["mmlu-test.parquet"]["family_counts"],
        ifbench={"instruction_following": inventory["ifbench.jsonl"]["rows"]},
        musr={
            family: inventory["musr-" + family + ".csv"]["rows"]
            for family in ("murder_mystery", "object_placements", "team_allocation")
        },
    )
    stratified = {}
    for profile_name in [*m["models"], "granite_jev", "all_models_all_controls"]:
        samples = []
        for ident, c in cases.items():

            def seconds(name, arm, ident=ident):
                row = by_key.get((name, arm, ident))
                return (
                    batches[row["batch_id"]]["seconds"] / batches[row["batch_id"]]["batch_size"]
                    if row
                    else 0
                )

            if profile_name in m["models"]:
                value = seconds(profile_name, "native")
            elif profile_name == "granite_jev":
                value = seconds("granite_4_0_1b", "native") + seconds("granite_4_0_1b", "live")
            else:
                value = sum(seconds(n, "native") for n in m["models"]) + sum(
                    seconds("granite_4_0_1b", arm) for arm in (*A["ARMS"], "self_refine")
                )
            samples.append(dict(task=c["task"], family=c["family"], seconds=value))
        stratified[profile_name] = project_stratified_cost(samples, strata, 1.7545808219178083)
    completion = json.loads((output / "completion.json").read_text())
    if completion["cases"] != len(cases) or completion["fresh_test_cases"] != sum(
        c["split"] == "test" for c in cases.values()
    ):
        raise ValueError("Completion scope mismatch")
    delivery = check_delivery(output, cases, native, m)
    if max(r["at"] for r in selected["self_refine"].values()) >= min(
        r["at"] for r in lines(output / "requests.jsonl")
    ):
        raise ValueError("Jev-free baseline did not finish before provider requests")
    api = json.loads((output / "api-summary.json").read_text())
    if (
        api["usd"] != delivery["usd"]
        or api["unresolved"] != 0
        or api["max_charged"] != delivery["unknown_attempts"]
        or api["charged_tokens"]
        != delivery["known_input_tokens"] + 65536 * delivery["unknown_attempts"]
    ):
        raise ValueError("API summary mismatch")
    untouched = {i: c for i, c in cases.items() if c["split"] == "test"}
    return dict(
        audited_records=True,
        tokenizers_checked=bool(tokenizers),
        fresh_test_cases=completion["fresh_test_cases"],
        models=models,
        admitted=bool(tokenizers),
        quality=score_selected(cases, refs, selected, ifbench=ifbench),
        untouched_quality=(
            score_selected(
                untouched,
                {i: refs[i] for i in untouched},
                {name: {i: rows[i] for i in untouched} for name, rows in selected.items()},
                ifbench=ifbench,
            )
            if untouched and len(untouched) < len(cases)
            else None
        ),
        delivery=delivery,
        actual_repairs=repairs,
        actual_skipped_repairs=len(decisions) - repairs,
        outputs=len(rows),
        batches=len(batches),
        total_work={k: sum(w[k] for w in work.values()) for k in next(iter(work.values()))},
        native_cost_profiles=profiles,
        subject_weighted_cost_profiles=stratified,
        cost_inventory_sha256=C["sha"](inventory_path),
        seconds=completion["seconds"],
        profile_work={
            name + "/" + arm: {
                key: sum(
                    work[r["batch_id"]][key] for r in rows if r["model"] == name and r["arm"] == arm
                )
                for key in next(iter(work.values()))
            }
            for name, arm in sorted({(r["model"], r["arm"]) for r in rows})
        },
        source_sha256=C["sha"](Path(__file__)),
        input_files={p.name: C["sha"](p) for p in output.iterdir() if p.is_file()},
    )


if __name__ == "__main__":
    import argparse
    import importlib.util
    import sys

    p = argparse.ArgumentParser()
    p.add_argument("--freeze", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--write", type=Path, required=True)
    p.add_argument("--tokenizers", action="store_true")
    p.add_argument("--ifbench-evaluator", type=Path)
    p.add_argument("--ifbench-site-packages", type=Path)
    args = p.parse_args()
    tokenizers = None
    if args.tokenizers:
        from transformers import AutoTokenizer

        tokenizers = {
            name: AutoTokenizer.from_pretrained(
                c["id"], revision=c["revision"], trust_remote_code=False
            )
            for name, c in A["MODELS"].items()
        }
    evaluator = None
    if args.ifbench_evaluator:
        if args.ifbench_site_packages:
            sys.path.append(str(args.ifbench_site_packages))
        spec = importlib.util.spec_from_file_location(
            "r27_ifbench_evaluator", args.ifbench_evaluator
        )
        evaluator = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = evaluator
        spec.loader.exec_module(evaluator)
    result = analyze(args.freeze, args.output, tokenizers=tokenizers, ifbench=evaluator)
    result["ifbench_evaluator_sha256"] = (
        C["sha"](args.ifbench_evaluator) if args.ifbench_evaluator else None
    )
    C["dump"](args.write, result)
