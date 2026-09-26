"""Independent reconstruction of contextual memory, training and generated answers."""

import argparse
import json
import math
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
N = runpy.run_path(str(HERE / "common.py"))
K = runpy.run_path(str(HERE / "checks.py"))
P = runpy.run_path(str(HERE.parent / "feedback_pairing/audit.py"))
C, lines = P["OLD"], P["lines"]
FROZEN = runpy.run_path(str(HERE / "contract.py"))


def read(output, name):
    return json.loads((output / name).read_text())


def summarize(cases, records, manifest, *, draws=10000):
    if manifest["informative"] != "both" or any(c["split"] != "test" for c in cases):
        raise ValueError("Summary requires the full factorial held-out cohort")
    N["coverage"](cases, records, manifest)
    table = {(r["id"], r["arm"]): r for r in records}
    ids, arms = [c["id"] for c in cases], N["test_arms"](manifest)
    scores = {arm: {i: float(table[i, arm]["correct"]) for i in ids} for arm in arms}
    names = sorted({arm.rsplit("/", 1)[0] for arm in arms if "/" in arm})
    for name in names:
        scores[name] = {
            i: sum(scores[f"{name}/{seed}"][i] for seed in manifest["seeds"])
            / len(manifest["seeds"])
            for i in ids
        }
    primary = [
        ("contextual-scalar", "native"),
        ("contextual-scalar", "embedding-scalar"),
        ("contextual-structured", "contextual-scalar"),
        ("contextual-scalar", "donor/contextual-scalar"),
    ]
    pairs = list(primary)
    for name, _, feedback in N["specifications"]("both"):
        pairs.extend((name, other) for other in ("native", "blind"))
        if feedback != "constant":
            pairs.extend(
                (name, f"{control}/{name}") for control in ("same_constant", "donor", "oracle")
            )
    pairs.extend(
        (f"contextual-{f}", f"embedding-{f}") for f in ("structured", "scalar", "constant")
    )
    pairs.extend((f"contextual-{f}", "contextual-constant") for f in ("structured", "scalar"))
    contrasts = {
        f"{a}-minus-{b}": N["effect"](cases, {i: scores[a][i] - scores[b][i] for i in ids}, draws)
        | dict(primary=(a, b) in primary)
        for a, b in dict.fromkeys(pairs)
    }
    interaction = {
        i: (scores["contextual-structured"][i] - scores["contextual-scalar"][i])
        - (scores["embedding-structured"][i] - scores["embedding-scalar"][i])
        for i in ids
    }
    return dict(
        scores={
            arm: dict(
                n=len(ids),
                accuracy=sum(values.values()) / len(ids),
                by_task={
                    task: sum(values[c["id"]] for c in cases if c["task"] == task)
                    / sum(c["task"] == task for c in cases)
                    for task in sorted({c["task"] for c in cases})
                },
            )
            for arm, values in scores.items()
        },
        contrasts=contrasts,
        memory_feedback_interaction=N["effect"](cases, interaction, draws) | dict(primary=False),
        preservation={
            arm: dict(
                fixed=sum(scores[arm][i] and not scores["native"][i] for i in ids),
                damaged=sum(scores["native"][i] and not scores[arm][i] for i in ids),
            )
            for arm in arms
            if arm != "native"
        },
        per_arm_readout={
            arm: dict(
                slot_accuracy=sum(sum(table[i, arm]["slots"]) for i in ids) / (3 * len(ids)),
                format_passes=sum(table[i, arm]["format"] for i in ids),
                length_stops=sum(table[i, arm]["finish_reason"] == "length" for i in ids),
            )
            for arm in arms
        },
    )


def audit_records(cases, refs, rows, receipts, output, tok, manifest, *, eos, width=2048):
    N["coverage"](cases, rows, manifest)
    table = {(r["id"], r["arm"]): r for r in rows}
    natives = {c["id"]: table[c["id"], "native"] for c in cases}
    by_id = {c["id"]: c for c in cases}
    tests = [c for c in cases if c["split"] == "test"]
    if set(receipts) != set(by_id) or set(refs) != set(by_id):
        raise ValueError("Incomplete feedback or reference coverage")
    selection = read(output, "selection.json")
    donors = P["C"]["donors"](tests)
    if donors != read(output, "donors.json"):
        raise ValueError("Substituted feedback donor pairing")
    memory_records = lines(output / "memory-records.jsonl")
    memories = K["check_memories"](
        cases, natives, memory_records, output, tok, eos=eos, width=width, layer=manifest["layer"]
    )
    memory_times = {r["id"]: r["at"] for r in memory_records}
    steps = lines(output / "training-steps.jsonl")
    trained = K["check_training"](
        cases,
        refs,
        natives,
        rows,
        steps,
        read(output, "training-targets.json"),
        lines(output / "epochs.jsonl"),
        selection,
        memories["digests"],
        receipts,
        output,
        tok,
        manifest,
        eos=eos,
        width=width,
    )
    if any(r["at"] < memory_times[r["id"]] for r in steps):
        raise ValueError("Training preceded recorded memory extraction")
    for case in cases:
        ident = case["id"]
        if memory_times[ident] < receipts[ident].get("at", natives[ident]["at"]):
            raise ValueError("Extraction preceded its recorded judgment")
        if case["split"] == "test" and natives[ident]["at"] <= selection["at"]:
            raise ValueError("Test draft generated before selection freeze")
    expected_bindings, grades = {}, {}
    for row in rows:
        ident, arm = row["id"], row["arm"]
        case, native = by_id[ident], natives[ident]
        prompt = tok.apply_chat_template(
            [dict(role="user", content=case["prompt"])], tokenize=True, add_generation_prompt=True
        )
        if arm != "native":
            prompt = C["repair_prefix"](tok, prompt, native["generated_token_ids"])
        digest, adapter_digest, values = None, None, None
        if arm not in ("native", "blind"):
            parts = arm.split("/")
            if parts[0] == "development":
                name, seed, epoch = parts[1], int(parts[2]), int(parts[3])
                adapter_digest = trained["epoch_digests"][name, seed, epoch]
                control = None
            else:
                control = parts[0] if len(parts) == 3 else None
                name, seed = parts[-2], int(parts[-1])
                adapter_digest = trained["selected_digests"][name, seed]
            memory_kind, feedback = name.split("-")
            digest = memories["digests"][ident][memory_kind]
            values = receipts[ident]["probabilities"]
            if control == "same_constant":
                values = [0.5] * 3
            elif control == "donor":
                values = C["signal"](feedback, receipts[donors[ident]]["probabilities"])
            elif control == "oracle":
                values = C["signal"](
                    feedback, [float(v) for v in C["grade"](native["text"], refs[ident])["slots"]]
                )
            elif control is None:
                values = C["signal"](feedback, values)
            else:
                raise ValueError("Unknown generation condition")
            if row["at"] < memory_times[ident]:
                raise ValueError("Generation preceded its memory extraction")
        P["check_generation"](row, prompt, values, tok, eos, manifest["limit"], manifest["layer"])
        if (
            row["task"] != case["task"]
            or row["split"] != case["split"]
            or row["processed_tokens"] != len(prompt) + len(row["generated_token_ids"]) - 1
            or not math.isfinite(row["seconds"])
            or row["seconds"] < 0
        ):
            raise ValueError("Changed output metadata or generation work")
        expected_bindings[ident, arm] = dict(
            memory_digest=digest, adapter_digest=adapter_digest, probabilities=values
        )
        grades[ident, arm] = C["grade"](row["text"], refs[ident])
    binding_seconds = K["check_bindings"](
        rows, lines(output / "generation-bindings.jsonl"), expected_bindings
    )
    jobs = lines(output / "jobs.jsonl")
    if len(jobs) != 2 * len(rows):
        raise ValueError("Incomplete generation job record")
    for i, row in enumerate(rows):
        start, finish = jobs[2 * i : 2 * i + 2]
        if (
            any(r["id"] != row["id"] or r["arm"] != row["arm"] for r in (start, finish))
            or start["event"] != "start"
            or finish["event"] != "finish"
            or not start["at"] <= row["at"] <= finish["at"]
            or (i and jobs[2 * i - 1]["at"] > start["at"])
        ):
            raise ValueError("Unbound, overlapping or incomplete generation job")
    return dict(
        outputs=len(rows),
        test_cases=len(tests),
        memory_extractions=memories["count"],
        memory_processed_tokens=memories["processed_tokens"],
        memory_seconds=memories["seconds"],
        training_steps=trained["examples"],
        optimizer_updates=trained["updates"],
        generated_tokens=sum(len(r["generated_token_ids"]) for r in rows),
        generation_processed_tokens=sum(r["processed_tokens"] for r in rows),
        generation_seconds=sum(r["seconds"] for r in rows),
        binding_seconds=binding_seconds,
        selected_digests={
            f"{name}/{seed}": digest for (name, seed), digest in trained["selected_digests"].items()
        },
        test_rows=[
            dict(
                id=c["id"],
                task=c["task"],
                arm=arm,
                **grades[c["id"], arm],
                finish_reason=table[c["id"], arm]["finish_reason"],
            )
            for c in tests
            for arm in N["test_arms"](manifest)
        ],
    )


def audit(folder, output):
    m = FROZEN["verify"](folder)
    complete, execution = read(output, "complete.json"), read(output, "execution.json")
    if (
        execution["manifest_sha256"] != C["sha"](folder / "manifest.json")
        or execution["sources"] != m["sources"]
    ):
        raise ValueError("Unbound execution source or frozen manifest")
    if complete["backbone_before"] != complete["backbone_after"] or any(
        (output / f).exists() for f in ("failed.json", "failures.jsonl")
    ):
        raise ValueError("Changed backbone or failed execution")
    admission, hardware = read(output, "mechanical-admission.json"), read(output, "hardware.json")
    if (
        any(
            admission.get(k) is not True
            for k in (
                "passed",
                "initial_identity",
                "off_identity",
                "backbone_gradients_absent",
                "cache_argmax_equal",
            )
        )
        or not math.isfinite(admission["cache_max_logit_error"])
        or not 0 <= admission["cache_max_logit_error"] <= 0.001
        or admission["backbone_before"] != complete["backbone_before"]
        or admission["backbone_after"] != complete["backbone_after"]
        or admission["contextual_memory_shape"] != [3, 2048]
        or admission["parameters"] != 262144
        or admission["device"] != "cuda"
        or hardware["device"] != "cuda"
        or hardware["dtype"] != "torch.float32"
        or hardware["parameters"] != 1631750144
    ):
        raise ValueError("Unadmitted device, dimensions, identity or cache")
    cases, refs = read(folder, "cases.json"), read(folder, "references.json")
    replay = runpy.run_path(str(HERE.parent / "structured_correction/audit.py"))["replay_reference"]
    if any(replay(c) != refs[c["id"]] for c in cases):
        raise ValueError("Independent reference replay disagrees")
    rows = lines(output / "outputs.jsonl")
    N["coverage"](cases, rows, m)
    natives = {r["id"]: r for r in rows if r["arm"] == "native"}
    responses, ledger = lines(output / "responses.jsonl"), lines(output / "budget.jsonl")
    input_tokens = P["check_receipts"](
        cases, natives, lines(output / "requests.jsonl"), responses, ledger
    )
    terms = [r for r in ledger if r["event"] == "terms"]
    if (
        len(terms) != 1
        or terms[0]["max_usd"] != str(m["api_cap_usd"])
        or terms[0]["usd_per_million"] != str(m["usd_per_million"])
        or any(r["event"] not in ("terms", "reserve", "settle") for r in ledger)
        or input_tokens != complete["charged_input_tokens"]
        or input_tokens * m["usd_per_million"] / 1e6 > m["api_cap_usd"]
    ):
        raise ValueError("Changed, extra or excessive API budget accounting")
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(m["model"], revision=m["revision"])
    eos = tok.convert_tokens_to_ids("<|end_of_text|>")
    if hardware["eos"] != [eos]:
        raise ValueError("Changed EOS contract")
    receipts = {r["id"]: r for r in responses}
    result = audit_records(cases, refs, rows, receipts, output, tok, m, eos=eos)
    selected = read(output, "adapter-bindings.json")
    if (
        result["outputs"] != m["planned_outputs"]
        or result["outputs"] != complete["outputs"]
        or result["training_steps"] != m["planned_training_steps"]
        or result["optimizer_updates"] != m["planned_optimizer_updates"]
        or result["test_cases"] != m["planned_test_cases"]
        or result["memory_extractions"] != m["planned_cases"]
        or selected["before"] != result["selected_digests"]
        or complete["adapters_before"] != result["selected_digests"]
        or complete["adapters_after"] != result["selected_digests"]
        or any(r["at"] <= selected["at"] for r in rows if r["split"] == "test")
        or selected["at"] < read(output, "selection.json")["at"]
        or max(r["at"] for r in rows) > complete["at"]
    ):
        raise ValueError("Incomplete planned work or changed selected adapters")
    tests = [c for c in cases if c["split"] == "test"]
    result.update(summarize(tests, result["test_rows"], m))
    result.update(
        passed=True,
        scope="Authored contextual-memory mechanism study, not public benchmark performance",
        requests=len(responses),
        input_tokens=input_tokens,
        api_seconds=sum(r["seconds"] for r in responses),
    )
    table = {(r["id"], r["arm"]): r for r in rows}
    result["token_changes"] = {
        str(seed): {
            name: sum(
                table[c["id"], f"{name}/{seed}"]["generated_token_ids"]
                != table[c["id"], f"donor/{name}/{seed}"]["generated_token_ids"]
                for c in tests
            )
            for name, _, feedback in N["specifications"]("both")
            if feedback != "constant"
        }
        for seed in m["seeds"]
    }
    C["dump"](output / "analysis.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = audit(args.input, args.output)
    print(json.dumps({k: result[k] for k in ("passed", "outputs", "requests", "scores")}))
