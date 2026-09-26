"""Independent R26-A work/selection audit and descriptive full-task cost projection."""

import argparse
import json
import math
import runpy
from collections import defaultdict
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[2]
A = runpy.run_path(str(ROOT / "research/iterations/selective_benchmarks/admission.py"))
C = A["C"]


def lines(path):
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def unique(rows, key):
    result = {key(row): row for row in rows}
    if len(result) != len(rows):
        raise ValueError("Duplicate evidence")
    return result


def check_batch(batch, rows):
    n = len(rows)
    if not n:
        raise ValueError("Missing batch work")
    width = max(len(row["prompt_token_ids"]) for row in rows)
    steps = max(len(row["generated_token_ids"]) for row in rows)
    if (
        batch["batch_size"] != n
        or any(row["batch_id"] != batch["batch_id"] for row in rows)
        or batch["forwards"] != steps
        or batch["padded_prompt_tokens"] != n * width
        or batch["generated_token_slots"] != n * steps
        or batch["processed_token_slots"] != n * (width + steps - 1)
        or not math.isfinite(batch["seconds"])
        or batch["seconds"] < 0
    ):
        raise ValueError("Batch work mismatch")
    return dict(
        actual_prompt_tokens=sum(len(r["prompt_token_ids"]) for r in rows),
        actual_generated_tokens=sum(len(r["generated_token_ids"]) for r in rows),
        **{
            k: batch[k]
            for k in (
                "seconds",
                "padded_prompt_tokens",
                "processed_token_slots",
                "generated_token_slots",
                "forwards",
            )
        },
    )


def check_selection(row, native, repaired, probability, donor_probability):
    should_repair = probability is not None and probability < 0.5
    if probability is not None:
        C["probability"](probability)
    arm = row["arm"]
    gates = dict(
        live=None if probability is None else 1 - probability,
        blind=None,
        constant=0.5,
        live_constant=0.5,
        inverted=probability,
        shuffled=1 - (0.5 if donor_probability is None else donor_probability),
    )
    if arm not in gates:
        raise ValueError("Unknown selection arm")
    expected = repaired if should_repair else native
    if (
        row["probability_correct"] != probability
        or row["repair_executed"] != should_repair
        or (repaired is not None) != should_repair
        or row["selected_arm"] != (arm if should_repair else "native")
        or row["decision"] != ("repair" if should_repair else "retain_native")
        or row["gate"] != (gates[arm] if should_repair else None)
        or expected is None
        or native["arm"] != "native"
        or (should_repair and (repaired["arm"] != arm or repaired["gate"] != gates[arm]))
        or row["selected_tokens_sha256"] != C["digest"](json.dumps(expected["generated_token_ids"]))
    ):
        raise ValueError("Selection provenance mismatch")
    return expected


def project_cost(rows, counts, hourly_rate):
    groups = defaultdict(list)
    for row in rows:
        groups[row["task"]].append(row["seconds"])
    result = {}
    for task, count in counts.items():
        samples = groups[task]
        if not samples:
            result[task] = dict(measured=False, full_cases=count)
            continue
        central = mean(samples) * count
        upper = max(samples) * count
        result[task] = dict(
            measured=True,
            full_cases=count,
            profile_cases=len(samples),
            central_gpu_seconds=central,
            upper_observed_gpu_seconds=upper,
            central_gpu_usd=central / 3600 * hourly_rate,
            upper_observed_gpu_usd=upper / 3600 * hourly_rate,
            interpretation=(
                "Exposed-case extrapolation; neither a confidence bound nor an invoice; "
                "overhead/API excluded"
            ),
        )
    return result


def project_stratified_cost(rows, counts, hourly_rate):
    samples = defaultdict(list)
    for r in rows:
        samples[(r["task"], r["family"])].append(r["seconds"])
    result = {}
    for task, families in counts.items():
        if any(not samples[(task, family)] for family in families):
            result[task] = dict(measured=False, full_cases=sum(families.values()))
            continue
        seconds = sum(count * mean(samples[(task, family)]) for family, count in families.items())
        result[task] = dict(
            measured=True,
            full_cases=sum(families.values()),
            profile_cases=sum(len(samples[(task, f)]) for f in families),
            gpu_seconds=seconds,
            gpu_usd=seconds / 3600 * hourly_rate,
            strata={
                f: dict(
                    full_cases=count,
                    profile_cases=len(samples[(task, f)]),
                    mean_seconds=mean(samples[(task, f)]),
                )
                for f, count in families.items()
            },
            interpretation=(
                "Subject-weighted exposed-case extrapolation, not a full run or guaranteed quote; "
                "loading/API/evaluator/network/tax excluded"
            ),
        )
    return result


def check_output(case, row, tok, config, eos, native=None):
    if row["arm"] not in {*A["ARMS"], "native", "warmup", "serial_probe"}:
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
    if (
        any(t in eos for t in ids[:-1])
        or len(ids) > limit
        or row["finish_reason"] != ("eos" if stopped else "length")
        or (not stopped and len(ids) != limit)
    ):
        raise ValueError("EOS/limit mismatch")
    text = tok.decode(ids[:-1] if stopped else ids, skip_special_tokens=False)
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


def check_delivery(output, cases, native, m):
    from datetime import datetime
    from decimal import Decimal

    from jev_guided_decoding.jev import _probability

    req = unique(lines(output / "requests.jsonl"), lambda r: r["reservation"])
    res = unique(lines(output / "responses.jsonl"), lambda r: r["reservation"])
    fail = unique(lines(output / "failures.jsonl"), lambda r: r["reservation"])
    done = unique(lines(output / "feedback.jsonl"), lambda r: r["id"])
    if set(res) & set(fail) or set(req) != set(res) | set(fail) or set(done) != set(cases):
        raise ValueError("Incomplete delivery coverage")
    ledger = lines(output / "budget.jsonl")
    terms = [r for r in ledger if r["event"] == "terms"]
    reserves = unique([r for r in ledger if r["event"] == "reserve"], lambda r: r["id"])
    settled = unique([r for r in ledger if r["event"] == "settle"], lambda r: r["id"])
    maximum = unique([r for r in ledger if r["event"] == "charge_max_unknown"], lambda r: r["id"])
    if (
        len(terms) != 1
        or Decimal(terms[0]["max_usd"]) != Decimal(str(m["jev_cap"]))
        or Decimal(terms[0]["usd_per_million"]) != Decimal(str(m["usd_per_million"]))
        or terms[0]["request_token_ceiling"] != 65536
        or set(reserves) != set(req)
        or set(settled) != set(res)
        or set(maximum) != set(fail)
        or len(maximum) > 16
        or any(
            r["event"] not in ("terms", "reserve", "settle", "charge_max_unknown") for r in ledger
        )
    ):
        raise ValueError("Physical attempt charge mismatch")
    pending = set()
    charges = {}
    for event in ledger[1:]:
        key = event["id"]
        if event["event"] == "reserve":
            if key in charges:
                raise ValueError("Repeated reservation")
            charges[key] = 65536
            pending.add(key)
        else:
            if key not in pending:
                raise ValueError("Settlement without pending reservation")
            pending.remove(key)
            if event["event"] == "settle":
                n = event["input_tokens"]
                if type(n) is not int or not 0 <= n <= 65536:
                    raise ValueError("Invalid settled usage")
                charges[key] = n
        if Decimal(sum(charges.values())) * Decimal(str(m["usd_per_million"])) / 1000000 > Decimal(
            str(m["jev_cap"])
        ):
            raise ValueError("Historical API cap exceeded")
    if pending:
        raise ValueError("Unresolved attempt charge")
    groups = defaultdict(list)
    for key, r in req.items():
        ident = r["id"]
        if ident not in cases or r["payload"] != A["F"]["payload"](
            cases[ident], native[ident]["final"] or "(empty response)"
        ):
            raise ValueError("Request input binding mismatch")
        groups[ident].append(r)
        if key in res:
            receipt = res[key]
            if (
                receipt["id"] != ident
                or receipt["model"] != m["jev"]
                or receipt["raw"]["model"] != m["jev"]
                or receipt["attempts"] != 1
                or receipt["probability_correct"]
                != _probability(receipt["raw"]["answers"], "correct")
                or receipt["raw"]["usage"]
                != {
                    "input_tokens": receipt["input_tokens"],
                    "output_tokens": receipt["output_tokens"],
                }
                or settled[key]["input_tokens"] != receipt["input_tokens"]
            ):
                raise ValueError("Receipt probability or usage mismatch")
        elif fail[key]["id"] != ident or not fail[key]["usage_unknown"]:
            raise ValueError("Failure binding mismatch")
    if set(groups) != set(cases):
        raise ValueError("Request case coverage mismatch")
    previous = None
    for ident, group in groups.items():
        if (
            previous is not None
            and (datetime.fromisoformat(group[0]["at"]) - previous).total_seconds() + 0.01 < 2
        ):
            raise ValueError("Case pacing violation")
        if not 1 <= len(group) <= 4 or [r["attempt"] for r in group] != list(
            range(1, len(group) + 1)
        ):
            raise ValueError("Invalid attempt order/count")
        for index, r in enumerate(group):
            key = r["reservation"]
            terminal = index == len(group) - 1
            event = res.get(key, fail.get(key))
            if event["attempt"] != r["attempt"] or event["at"] < r["at"]:
                raise ValueError("Attempt receipt binding mismatch")
            if key in res:
                if not terminal:
                    raise ValueError("Successful request replayed")
                continue
            info = event["diagnostics"]
            explicit = info.get("status_code") in (429, 503, 529)
            transport = event["message"] == "Jev request failed or timed out; it was not replayed"
            delay = info.get("retry_after_seconds", 0)
            if (
                not event["admitted"]
                or not (explicit or transport)
                or type(delay) not in (int, float)
                or not math.isfinite(delay)
                or not 0 <= delay <= 300
            ):
                raise ValueError("Fatal failure in completed delivery")
            if not terminal:
                expected = max(30 * 2 ** (r["attempt"] - 1), delay)
                if not explicit or not event["retry"] or event["cooldown_seconds"] != expected:
                    raise ValueError("Unsupported paid retry")
                elapsed = (
                    datetime.fromisoformat(group[index + 1]["at"])
                    - datetime.fromisoformat(event["at"])
                ).total_seconds()
                if elapsed + 0.01 < expected:
                    raise ValueError("Retry before cooldown")
            elif (
                event["retry"]
                or event["cooldown_seconds"] is not None
                or (explicit and r["attempt"] != 4)
            ):
                raise ValueError("Incomplete retry sequence")
        last = group[-1]["reservation"]
        probability = res[last]["probability_correct"] if last in res else None
        completion = done[ident]
        if (
            completion["attempts"] != len(group)
            or completion["actual_probability_correct"] != probability
            or completion["missing"] != (probability is None)
            or completion["at"] < event["at"]
        ):
            raise ValueError("Feedback completion mismatch")
        previous = datetime.fromisoformat(completion["at"])
    missing = sum(r["missing"] for r in done.values())
    if missing > 4:
        raise ValueError("Missing feedback cap exceeded")
    known = sum(r["input_tokens"] for r in res.values())
    return dict(
        physical_attempts=len(req),
        known_input_tokens=known,
        unknown_attempts=len(maximum),
        missing_cases=missing,
        retries=len(req) - len(groups),
        usd=(known + 65536 * len(maximum)) * m["usd_per_million"] / 1e6,
    )


def check_profile_order(cases, rows, batch_size):
    native = [r for r in rows if r["arm"] == "native"]
    expected = sorted(native, key=lambda r: (len(r["prompt_token_ids"]), r["id"]))
    if [r["id"] for r in native] != [r["id"] for r in expected]:
        raise ValueError("Native batch order mismatch")
    if [r["id"] for r in rows if r["arm"] == "warmup"] != [expected[0]["id"]]:
        raise ValueError("Warmup order mismatch")
    serial = set(sorted(cases, key=lambda ident: C["digest"]("serial/" + ident))[:8])
    if [r["id"] for r in rows if r["arm"] == "serial_probe"] != [
        ident for ident in cases if ident in serial
    ]:
        raise ValueError("Serial probe order mismatch")
    batch_ids = []
    for offset in range(0, len(native), batch_size):
        group = native[offset : offset + batch_size]
        keys = {r["batch_id"] for r in group}
        if len(keys) != 1 or next(iter(keys)) in batch_ids:
            raise ValueError("Native batch grouping mismatch")
        batch_ids.extend(keys)


def check_numerical(value):
    initial = value["initial"]
    if (
        any(
            initial[k] is not True
            for k in ("passed", "zero_gate_exact", "zero_initial_exact", "base_gradients_absent")
        )
        or initial["precision"] != "float32"
        or initial["atol"] != 1e-4
        or initial["rtol"] != 1e-4
        or len(value["selected"]) != 3
    ):
        raise ValueError("Numerical admission failed")
    for c in [initial["comparison"], *value["selected"]]:
        if (
            c["allclose"] is not True
            or c["argmax_equal"] is not True
            or not math.isfinite(c["max_abs"])
            or c["max_abs"] < 0
        ):
            raise ValueError("Cache admission failed")


def analyze(folder, output, *, tokenizers=None):
    m = json.loads((folder / "manifest.json").read_text())
    A["verify_bindings"](folder, m)
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
            or r["arm"] not in {*A["ARMS"], "native", "warmup", "serial_probe"}
            or (r["arm"] in A["ARMS"] and r["model"] != "granite_4_0_1b")
        ):
            raise ValueError("Unregistered model arm")
        grouped[r["batch_id"]].append(r)
    if set(grouped) != set(batches):
        raise ValueError("Batch coverage mismatch")
    work = {k: check_batch(b, grouped[k]) for k, b in batches.items()}
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
                        native[r["id"]] if r["arm"] in A["ARMS"] else None,
                    )
        serial = {r["id"] for r in rows if r["model"] == name and r["arm"] == "serial_probe"}
        expected = set(sorted(cases, key=lambda ident: C["digest"]("serial/" + ident))[:8])
        if (
            serial != expected
            or sum(r["model"] == name and r["arm"] == "warmup" for r in rows) != 1
        ):
            raise ValueError("Timing probe coverage mismatch")
        graded = [
            C["grade"](refs[i], r["final"])
            for i, r in native.items()
            if cases[i]["format"] != "instruction"
        ]
        models[name] = dict(
            native_cases=len(native),
            parseable=sum(r["parseable"] for r in graded),
            graded_cases=len(graded),
            correct=sum(r["correct"] for r in graded),
            admission=sum(r["parseable"] for r in graded) >= 38,
            cutoffs=sum(r["finish_reason"] == "length" for r in native.values()),
            unfinished=sum(r["status"] == "unfinished_thinking" for r in native.values()),
            serial_vs_batch_exact_outputs=sum(
                r["generated_token_ids"] == native[r["id"]]["generated_token_ids"]
                for r in rows
                if r["model"] == name and r["arm"] == "serial_probe"
            ),
            parameters=hardware["parameters"],
            load_seconds=hardware["load_seconds"],
        )
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
    repairs = 0
    for (arm, ident), d in decisions.items():
        if d["donor_id"] != donors[ident]:
            raise ValueError("Donor binding mismatch")
        check_selection(
            d,
            native[ident],
            by_key.get(("granite_4_0_1b", arm, ident)),
            feedback[ident]["actual_probability_correct"],
            feedback[donors[ident]]["actual_probability_correct"],
        )
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
                    seconds("granite_4_0_1b", arm) for arm in A["ARMS"]
                )
            samples.append(dict(task=c["task"], family=c["family"], seconds=value))
        stratified[profile_name] = project_stratified_cost(samples, strata, 1.7545808219178083)
    completion = json.loads((output / "completion.json").read_text())
    if completion["cases"] != len(cases) or completion["fresh_test_cases"] != 0:
        raise ValueError("Completion scope mismatch")
    delivery = check_delivery(output, cases, native, m)
    api = json.loads((output / "api-summary.json").read_text())
    if (
        api["usd"] != delivery["usd"]
        or api["unresolved"] != 0
        or api["max_charged"] != delivery["unknown_attempts"]
        or api["charged_tokens"]
        != delivery["known_input_tokens"] + 65536 * delivery["unknown_attempts"]
    ):
        raise ValueError("API summary mismatch")
    return dict(
        audited_records=True,
        tokenizers_checked=bool(tokenizers),
        fresh_test_cases=0,
        models=models,
        admitted=all(r["admission"] for r in models.values()),
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
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--freeze", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--write", type=Path, required=True)
    p.add_argument("--tokenizers", action="store_true")
    a = p.parse_args()
    tokenizers = None
    if a.tokenizers:
        from transformers import AutoTokenizer

        tokenizers = {
            name: AutoTokenizer.from_pretrained(
                c["id"], revision=c["revision"], trust_remote_code=False
            )
            for name, c in A["MODELS"].items()
        }
    C["dump"](a.write, analyze(a.freeze, a.output, tokenizers=tokenizers))
