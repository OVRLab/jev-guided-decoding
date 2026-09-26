"""R25 continuation audit: real receipts and missing neutral values stay distinct."""

import argparse
import hashlib
import json
import runpy
from pathlib import Path

from jev_guided_decoding.jev import _probability

C = runpy.run_path(str(Path(__file__).resolve().with_name("common.py")))


def lines(path):
    return [json.loads(x) for x in path.read_text().splitlines()]


def unique(rows, key):
    found = {}
    for row in rows:
        k = key(row)
        if k in found:
            raise ValueError("Duplicate record")
        found[k] = row
    return found


def analyze(folder, output, tokenizer=None):
    m = C["verify"](folder)
    cases = json.loads((folder / "cases.json").read_text())
    by_id = unique(cases, lambda r: r["id"])
    refs = unique(
        [
            r
            for part in ("train", "development", "test")
            for r in json.loads((folder / f"{part}-references.json").read_text())
        ],
        lambda r: r["id"],
    )
    rows = lines(output / "outputs.jsonl")
    indexed = unique(rows, lambda r: (r["id"], r["arm"]))
    planned = {(c["id"], "native") for c in cases}
    arms = ["blind", "text"] + [
        f"{arm}/{seed}"
        for seed in m["seeds"]
        for arm in ("constant", "live", "shuffled", "inverted")
    ]
    for c in cases:
        if c["split"] == "development":
            planned.update(
                (c["id"], f"dev/{mode}/{seed}/{epoch}")
                for mode in ("constant", "live")
                for seed in m["seeds"]
                for epoch in (1, 2)
            )
        if c["split"] == "test":
            planned.update((c["id"], arm) for arm in arms)
    if set(indexed) != planned:
        raise ValueError("Missing or unexpected planned generation")
    jobs = lines(output / "jobs.jsonl")
    for event in ("start", "finish"):
        events = [(r["id"], r["arm"]) for r in jobs if r["event"] == event]
        if len(events) != len(planned) or set(events) != planned:
            raise ValueError("Job coverage mismatch")
    hardware = json.loads((output / "hardware.json").read_text())
    done = json.loads((output / "completion.json").read_text())
    if (
        done["original_weights_sha256"] != hardware["original_weights_sha256"]
        or not done["original_weights_unchanged"]
        or done["reserved_unknown_calls"]
    ):
        raise ValueError("Weight or API completion mismatch")
    if json.loads((output / "start.json").read_text())["manifest_sha256"] != C["sha"](
        folder / "manifest.json"
    ):
        raise ValueError("Run manifest mismatch")
    prior = output.parent / "prior-v2"
    C["C"]["verify_files"](prior, {n: v["sha256"] for n, v in m["prior_files"].items()})
    for name in (
        "outputs.jsonl",
        "jobs.jsonl",
        "api-requests.jsonl",
        "api-responses.jsonl",
        "api-failures.jsonl",
        "budget.jsonl",
    ):
        binding = m["prior_files"][name]
        prefix = (output / name).read_bytes()[: binding["bytes"]]
        if hashlib.sha256(prefix).hexdigest() != binding["sha256"]:
            raise ValueError("Predecessor prefix changed")
    requests = unique(lines(output / "api-requests.jsonl"), lambda r: r["id"])
    responses = unique(lines(output / "api-responses.jsonl"), lambda r: r["id"])
    failures = unique(lines(output / "api-failures.jsonl"), lambda r: r["id"])
    feedback = unique(lines(output / "feedback-availability.jsonl"), lambda r: r["id"])
    if (
        set(requests) != set(by_id)
        or set(feedback) != set(by_id)
        or set(responses) & set(failures)
        or set(responses) | set(failures) != set(by_id)
        or len(failures) > 8
    ):
        raise ValueError("Provider/availability coverage mismatch")
    ledger = lines(output / "budget.jsonl")
    reservations = unique([r for r in ledger if r["event"] == "reserve"], lambda r: r["id"])
    settled = unique([r for r in ledger if r["event"] == "settle"], lambda r: r["id"])
    maximum = unique([r for r in ledger if r["event"] == "charge_max_unknown"], lambda r: r["id"])
    if (
        set(settled) & set(maximum)
        or set(reservations) != set(settled) | set(maximum)
        or len(reservations) != len(cases)
        or any(
            r["event"] not in ("terms", "reserve", "settle", "charge_max_unknown") for r in ledger
        )
    ):
        raise ValueError("Budget ledger mismatch")
    for c in cases:
        ident = c["id"]
        native = indexed[ident, "native"]
        req = requests[ident]
        f = feedback[ident]
        if req["payload"] != C["feedback_payload"](c, native["text"] or "(empty response)"):
            raise ValueError("Feedback input mismatch")
        if ident in responses:
            r = responses[ident]
            if (
                req["reservation"] != r["reservation"]
                or r["model"] != m["jev"]
                or r["raw"]["model"] != m["jev"]
                or r["attempts"] != 1
                or r["probability_correct"] != _probability(r["raw"]["answers"], "correct")
            ):
                raise ValueError("Provider receipt mismatch")
            if (
                r["raw"]["usage"]
                != {"input_tokens": r["input_tokens"], "output_tokens": r["output_tokens"]}
                or settled[r["reservation"]]["input_tokens"] != r["input_tokens"]
            ):
                raise ValueError("Usage mismatch")
            if (
                f["actual_probability_correct"] != r["probability_correct"]
                or f["effective_probability_correct"] != r["probability_correct"]
                or f["source"] != "jev"
            ):
                raise ValueError("Available feedback mismatch")
        else:
            failure = failures[ident]
            historical = ident == "gsm8k/train/2355" and "admitted" not in failure
            transport = (
                failure.get("message") == "Jev request failed or timed out; it was not replayed"
                and failure["usage_unknown"]
            )
            if not historical and (
                not failure.get("admitted")
                or not (
                    transport or failure.get("diagnostics", {}).get("status_code") in (429, 529)
                )
                or not 60 <= failure["cooldown_seconds"] <= 300
            ):
                raise ValueError("Unadmitted failure")
            if (
                failure["reservation"] != req["reservation"]
                or failure["reservation"] not in maximum
                or f["actual_probability_correct"] is not None
                or f["effective_probability_correct"] != 0.5
                or f["source"] != "missing_neutral"
            ):
                raise ValueError("Missing feedback or charge mismatch")
    charged = sum(r["input_tokens"] for r in responses.values()) + 65536 * len(failures)
    if (
        done["known_input_tokens"] != sum(r["input_tokens"] for r in responses.values())
        or done["unknown_max_charged_calls"] != len(failures)
        or abs(done["usd"] - charged * m["usd_per_million"] / 1e6) > 1e-12
    ):
        raise ValueError("Completion charge mismatch")
    selection = json.loads((output / "selection.json").read_text())
    epochs = lines(output / "epochs.jsonl")
    for name, v in selection["models"].items():
        mode, seed = name.split("/")
        scores = []
        for epoch in (1, 2):
            dev = [c for c in cases if c["split"] == "development"]
            score = sum(
                C["R"]["readout"](
                    c["prompt"],
                    indexed[c["id"], f"dev/{mode}/{seed}/{epoch}"]["text"],
                    refs[c["id"]],
                )["correct"]
                for c in dev
            ) / len(dev)
            scores.append(score)
            record = [
                r for r in epochs if (r["mode"], r["seed"], r["epoch"]) == (mode, int(seed), epoch)
            ]
            if (
                len(record) != 1
                or record[0]["accuracy"] != score
                or record[0]["sha256"]
                != C["sha"](output / f"{mode}-{seed}-epoch{epoch}.safetensors")
            ):
                raise ValueError("Epoch score/checkpoint mismatch")
        if (
            scores != v["scores"]
            or C["choose_epoch"](scores) != v["epoch"]
            or C["sha"](output / v["file"]) != v["sha256"]
        ):
            raise ValueError("Selection mismatch")
    test = [c for c in cases if c["split"] == "test"]
    donors = C["donors"](test)
    if donors != json.loads((output / "donors.json").read_text()):
        raise ValueError("Donor mismatch")
    grades = []
    for row in rows:
        c = by_id[row["id"]]
        ref = refs[c["id"]]
        p = feedback[c["id"]]["effective_probability_correct"]
        native = indexed[c["id"], "native"]
        if (
            row["prompt_sha256"] != C["digest"](c["prompt"])
            or ref["prompt_sha256"] != row["prompt_sha256"]
            or (row["split"], row["task"]) != (c["split"], c["task"])
        ):
            raise ValueError("Input binding mismatch")
        ids = row["generated_token_ids"]
        eos = hardware["eos_ids"]
        cap = m["draft_limit"] if row["arm"] == "native" else m["repair_limit"]
        if (
            not ids
            or len(ids) > cap
            or any(i in eos for i in ids[:-1])
            or (row["finish_reason"] == "eos") != (ids[-1] in eos)
            or row["forwards"] != len(ids)
            or row["processed_tokens"] != len(row["prompt_token_ids"]) + len(ids) - 1
        ):
            raise ValueError("Token/compute contract mismatch")
        if (
            row["arm"] != "native"
            and row["prompt_token_ids"][
                : len(native["prompt_token_ids"]) + len(native["generated_token_ids"])
            ]
            != native["prompt_token_ids"] + native["generated_token_ids"]
        ):
            raise ValueError("Exact draft prefix mismatch")
        if c["split"] == "test" and row["at"] < selection["at"]:
            raise ValueError("Test preceded frozen selection")
        if tokenizer is not None:
            prompt = (
                tokenizer.apply_chat_template(
                    [dict(role="user", content=c["prompt"])],
                    tokenize=True,
                    add_generation_prompt=True,
                )
                if row["arm"] == "native"
                else C["repair_prefix"](
                    tokenizer,
                    native["prompt_token_ids"],
                    native["generated_token_ids"],
                    probability=p if row["arm"] == "text" and c["id"] in responses else None,
                )
            )
            body = ids[:-1] if ids[-1] in eos else ids
            if (
                prompt != row["prompt_token_ids"]
                or tokenizer.decode(body, skip_special_tokens=False) != row["text"]
            ):
                raise ValueError("Tokenizer replay mismatch")
        if row["gate"] is None:
            if row["events"] or row["arm"] not in ("native", "blind", "text"):
                raise ValueError("Unexpected intervention")
        else:
            name = row["arm"].split("/")[1 if row["arm"].startswith("dev/") else 0]
            expected = {"constant": 0.5, "live": 1 - p, "inverted": p}.get(name)
            if name == "shuffled":
                expected = 1 - feedback[donors[c["id"]]]["effective_probability_correct"]
            if row["gate"] != expected or len(row["events"]) != len(ids):
                raise ValueError("Gate/event count mismatch")
            for i, event in enumerate(row["events"]):
                if (
                    event["layer"] != m["layer"]
                    or event["positions"] != [len(row["prompt_token_ids"]) - 1 + i]
                    or event["feedback"] != [expected, expected]
                ):
                    raise ValueError("Internal intervention provenance mismatch")
        grades.append(
            dict(
                id=c["id"],
                task=c["task"],
                split=c["split"],
                arm=row["arm"],
                **C["R"]["readout"](c["prompt"], row["text"], ref),
            )
        )
    train = json.loads((output / "training-examples.json").read_text())
    targets = {
        r["id"]: r["target"] for r in json.loads((folder / "training-targets.json").read_text())
    }
    if len(train) != 384 or {r["id"] for r in train} != set(targets):
        raise ValueError("Training target coverage mismatch")
    if tokenizer is not None:
        for example in train:
            native = indexed[example["id"], "native"]
            if example["prompt_ids"] != C["repair_prefix"](
                tokenizer, native["prompt_token_ids"], native["generated_token_ids"]
            ) or example["target_ids"] != tokenizer.encode(
                targets[example["id"]], add_special_tokens=False
            ) + [tokenizer.convert_tokens_to_ids("<|end_of_text|>")]:
                raise ValueError("Training token provenance mismatch")
    steps = lines(output / "training-steps.jsonl")
    if len(steps) != 384 * 2 * 2 * 2:
        raise ValueError("Training step coverage mismatch")
    test_grades = [g for g in grades if g["split"] == "test"]
    for mode in ("constant", "live", "shuffled", "inverted"):
        for c in test:
            values = [
                g["correct"]
                for g in test_grades
                if g["id"] == c["id"] and g["arm"] in [f"{mode}/{s}" for s in m["seeds"]]
            ]
            if len(values) != 2:
                raise ValueError("Seed coverage mismatch")
            test_grades.append(
                dict(
                    id=c["id"],
                    task=c["task"],
                    split="test",
                    arm=mode + "_mean",
                    correct=sum(values) / 2,
                )
            )
    summaries = {}
    effects = {}
    for task in ["all", "gsm8k", "arc"]:
        cohort = [c for c in test if task == "all" or c["task"] == task]
        allowed = {c["id"] for c in cohort}
        group = [g for g in test_grades if g["id"] in allowed]
        summaries[task] = {
            arm: dict(
                n=len(cohort),
                correct=sum(g["correct"] for g in group if g["arm"] == arm),
                accuracy=sum(g["correct"] for g in group if g["arm"] == arm) / len(cohort),
            )
            for arm in [
                "native",
                *arms,
                "constant_mean",
                "live_mean",
                "shuffled_mean",
                "inverted_mean",
            ]
        }
        effects[task] = {
            f"{arm}-vs-{baseline}": C["paired"](cohort, group, arm, baseline)
            for arm, baseline in [
                ("live_mean", "native"),
                ("live_mean", "constant_mean"),
                ("live_mean", "blind"),
                ("live_mean", "text"),
                ("live_mean", "shuffled_mean"),
                ("live_mean", "inverted_mean"),
                ("blind", "native"),
                ("text", "native"),
            ]
        }
    sensitivity = {
        str(seed): {
            arm: sum(
                indexed[c["id"], f"live/{seed}"]["generated_token_ids"]
                != indexed[c["id"], f"{arm}/{seed}"]["generated_token_ids"]
                for c in test
            )
            for arm in ("shuffled", "inverted")
        }
        for seed in m["seeds"]
    }
    return dict(
        protocol=m["protocol"],
        audited=True,
        tokenizer_replayed=tokenizer is not None,
        planned_outputs=len(planned),
        completed_outputs=len(rows),
        summaries=summaries,
        effects=effects,
        feedback_changed_tokens=sensitivity,
        selection=selection,
        api_calls=len(requests),
        valid_api_receipts=len(responses),
        missing_feedback_ids=sorted(failures),
        api_usd=done["usd"],
        training_steps=len(steps),
        output_tokens=sum(len(r["generated_token_ids"]) for r in rows),
        generation_seconds=sum(r["seconds"] for r in rows),
        completion=done,
        grades=test_grades,
        larger_comparison_gate=all(
            effects[t][e]["delta_pp"] > 0
            for t in ("gsm8k", "arc")
            for e in ("live_mean-vs-native", "live_mean-vs-constant_mean")
        ),
        files={p.name: C["sha"](p) for p in output.iterdir() if p.is_file()},
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--freeze", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--save", type=Path, required=True)
    p.add_argument("--tokenizer", action="store_true")
    a = p.parse_args()
    tok = None
    if a.tokenizer:
        from transformers import AutoTokenizer

        m = C["verify"](a.freeze)
        tok = AutoTokenizer.from_pretrained(
            m["model"], revision=m["revision"], trust_remote_code=False
        )
    C["dump"](a.save, analyze(a.freeze, a.output, tok))
