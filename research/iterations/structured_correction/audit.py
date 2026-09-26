"""Independent saved-token, source, judgment and statistical reconstruction."""

import argparse
import json
import random
import re
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
C = runpy.run_path(str(HERE / "common.py"))


def replay_reference(case):
    """Solve the published text as a graph, independently of the world generator."""
    edges = {}
    for line in case["prompt"].splitlines():
        initial = re.fullmatch(r"Initially, the (.+) is in the (.+)\.", line)
        event = re.fullmatch(r"Event \d+: the (.+) is moved to the (.+)\.", line)
        if initial or event:
            entity, destination = (initial or event).groups()
            edges[entity] = destination
    result = []
    for question in case["questions"]:
        match = re.fullmatch(r"Which room contains the (.+) after the final event\?", question)
        if not match or match[1] not in edges:
            raise ValueError("Unresolvable question")
        node, visited = match[1], set()
        while node in edges:
            if node in visited:
                raise ValueError("Cyclic location graph")
            visited.add(node)
            node = edges[node]
        result.append(node)
    return result


def lines(path):
    return [json.loads(s) for s in path.read_text().splitlines()] if path.exists() else []


def contrast(cases, treatment, baseline, draws=10000):
    ids = [c["id"] for c in cases]
    if (
        len(ids) != len(set(ids))
        or not ids
        or set(ids) != set(treatment)
        or set(ids) != set(baseline)
    ):
        raise ValueError("Incomplete paired denominator")
    diff = {i: treatment[i] - baseline[i] for i in ids}
    groups = [
        [c["id"] for c in cases if c["task"] == task] for task in sorted({c["task"] for c in cases})
    ]
    rng = random.Random(2900)
    samples = sorted(
        100 * sum(diff[rng.choice(g)] for g in groups for _ in g) / len(ids) for _ in range(draws)
    )
    return dict(
        n=len(ids),
        delta_pp=100 * sum(diff.values()) / len(ids),
        ci95_pp=[samples[int(0.025 * draws)], samples[min(draws - 1, int(0.975 * draws))]],
        fixed=sum(max(d, 0) for d in diff.values()),
        damaged=sum(max(-d, 0) for d in diff.values()),
    )


def audit(folder, output):
    import torch
    from safetensors.torch import load_file
    from transformers import AutoTokenizer

    S = runpy.run_path(str(HERE / "study.py"))
    m = S["verify"](folder)
    cases = json.loads((folder / "cases.json").read_text())
    refs = json.loads((folder / "references.json").read_text())
    if any(replay_reference(c) != refs[c["id"]] for c in cases):
        raise ValueError("Independent oracle disagrees")
    complete = json.loads((output / "complete.json").read_text())
    execution = json.loads((output / "execution.json").read_text())
    if (
        execution["manifest_sha256"] != C["sha"](folder / "manifest.json")
        or execution["sources"] != m["sources"]
    ):
        raise ValueError("Source or manifest binding mismatch")
    if (
        complete["backbone_before"] != complete["backbone_after"]
        or (output / "failures.jsonl").exists()
    ):
        raise ValueError("Backbone mutation or failed request")
    rows = lines(output / "outputs.jsonl")
    table = {(r["id"], r["arm"]): r for r in rows}
    expected = {(c["id"], "native") for c in cases}
    test_arms = ["native", "blind"] + [
        f"{mode}/{seed}" for seed in m["seeds"] for mode in (*m["modes"], "shuffled")
    ]
    for c in cases:
        if c["split"] == "development":
            expected.update(
                (c["id"], f"development/{mode}/{seed}/{epoch}")
                for mode in m["modes"]
                for seed in m["seeds"]
                for epoch in (1, 2)
            )
        elif c["split"] == "test":
            expected.update((c["id"], arm) for arm in test_arms)
    if len(table) != len(rows) or set(table) != expected or complete["outputs"] != len(rows):
        raise ValueError("Missing, duplicate or unexpected outputs")
    requests, receipts = lines(output / "requests.jsonl"), lines(output / "responses.jsonl")
    req = {r["id"]: r for r in requests}
    res = {r["id"]: r for r in receipts}
    if (
        len(req) != len(requests)
        or len(res) != len(receipts)
        or set(req) != set(refs)
        or set(res) != set(refs)
    ):
        raise ValueError("Incomplete or duplicate feedback")
    ledger = lines(output / "budget.jsonl")
    reservations = {r["id"] for r in ledger if r["event"] == "reserve"}
    settlements = {r["id"]: r["input_tokens"] for r in ledger if r["event"] == "settle"}
    if reservations != set(settlements) or reservations != {r["reservation"] for r in receipts}:
        raise ValueError("Unresolved or extra budget reservation")
    if sum(settlements.values()) != complete["charged_input_tokens"]:
        raise ValueError("Usage total mismatch")
    selection = json.loads((output / "selection.json").read_text())
    donors = json.loads((output / "donors.json").read_text())
    tok = AutoTokenizer.from_pretrained(m["model"], revision=m["revision"])
    eos = tok.convert_tokens_to_ids("<|end_of_text|>")
    grades = {}
    by_id = {c["id"]: c for c in cases}
    for c in cases:
        ident = c["id"]
        native = table[ident, "native"]
        if req[ident]["payload"] != C["payload"](c, native["text"]):
            raise ValueError("Judgment not bound to original draft")
        receipt = res[ident]
        raw = receipt["raw"]
        if (
            receipt["model"] != "jev-1.13.0"
            or raw["model"] != receipt["model"]
            or receipt["attempts"] != 1
            or req[ident]["reservation"] != receipt["reservation"]
            or raw["usage"]["input_tokens"] != receipt["input_tokens"]
            or raw["usage"]["output_tokens"] != receipt["output_tokens"]
            or settlements[receipt["reservation"]] != receipt["input_tokens"]
        ):
            raise ValueError("Invalid provider receipt")
        values = [raw["answers"][f"q{i}"]["noul"] for i in (1, 2, 3)]
        if C["probabilities"](values) != receipt["probabilities"]:
            raise ValueError("Changed feedback probability")
        if c["split"] == "test" and native["at"] <= selection["at"]:
            raise ValueError("Test generated before selection freeze")
    for row in rows:
        c = by_id[row["id"]]
        native = table[c["id"], "native"]
        mode = (
            row["arm"].split("/")[1]
            if row["arm"].startswith("development/")
            else row["arm"].split("/")[0]
        )
        ids = tok.apply_chat_template(
            [dict(role="user", content=c["prompt"])], tokenize=True, add_generation_prompt=True
        )
        p = res[c["id"]]["probabilities"]
        if mode != "native":
            ids = C["repair_prefix"](
                tok, ids, native["generated_token_ids"], feedback=p if mode == "text" else None
            )
        if row["prompt_token_ids"] != ids:
            raise ValueError("Prompt/draft token provenance mismatch")
        generated = row["generated_token_ids"]
        if not generated or len(generated) > m["limit"] or eos in generated[:-1]:
            raise ValueError("Invalid completion tokens")
        body = generated[:-1] if generated[-1] == eos else generated
        if tok.decode(body, skip_special_tokens=False) != row["text"]:
            raise ValueError("Final text not decoded from Granite tokens")
        if row["finish_reason"] != ("eos" if generated[-1] == eos else "length"):
            raise ValueError("Completion reason mismatch")
        if mode in ("native", "blind"):
            if row["probabilities"] is not None or row["events"]:
                raise ValueError("Unexpected native intervention")
        else:
            if mode == "shuffled":
                donor = donors[c["id"]]
                if (
                    donor == c["id"]
                    or by_id[donor]["task"] != c["task"]
                    or by_id[donor]["split"] != "test"
                ):
                    raise ValueError("Invalid feedback donor")
                expected_p = res[donor]["probabilities"]
            else:
                expected_p = C["signal"](
                    mode, p, C["grade"](native["text"], refs[c["id"]])["slots"]
                )
            if row["probabilities"] != expected_p:
                raise ValueError("Wrong feedback treatment")
            positions = [p for event in row["events"] for p in event["positions"]]
            if positions != list(range(len(ids) - 1, len(ids) + len(generated) - 1)) or any(
                e["feedback"] != expected_p or e["layer"] != m["layer"] for e in row["events"]
            ):
                raise ValueError("Intervention positions or signal mismatch")
        grades[row["id"], row["arm"]] = C["grade"](row["text"], refs[row["id"]])
    targets = json.loads((output / "training-targets.json").read_text())
    for c in cases:
        if c["split"] == "train":
            row = table[c["id"], "native"]
            expected_ids = C["target_ids"](
                "train",
                grades[c["id"], "native"]["correct"],
                row["generated_token_ids"],
                tok.encode(C["target"](refs[c["id"]]), add_special_tokens=False),
                eos,
            )
            if targets[c["id"]]["target_ids"] != expected_ids:
                raise ValueError("Training preservation target mismatch")
    dev = [c for c in cases if c["split"] == "development"]
    for seed in m["seeds"]:
        init = None
        for mode in m["modes"]:
            tensors = load_file(str(output / f"{mode}-{seed}-initial.safetensors"))
            if init is not None and any(not torch.equal(tensors[k], init[k]) for k in init):
                raise ValueError("Initialization differs between conditions")
            init = tensors
            scores = [
                sum(grades[c["id"], f"development/{mode}/{seed}/{epoch}"]["correct"] for c in dev)
                / len(dev)
                for epoch in (1, 2)
            ]
            chosen = selection["models"][f"{mode}/{seed}"]
            if (
                chosen["scores"] != scores
                or chosen["epoch"] != max(range(2), key=lambda i: scores[i]) + 1
                or C["sha"](output / chosen["file"]) != chosen["sha256"]
            ):
                raise ValueError("Checkpoint selection mismatch")
            if mode == "structured":
                threshold = C["choose_threshold"](
                    [min(res[c["id"]]["probabilities"]) for c in dev],
                    [grades[c["id"], "native"]["correct"] for c in dev],
                    [
                        grades[c["id"], f"development/{mode}/{seed}/{chosen['epoch']}"]["correct"]
                        for c in dev
                    ],
                )
                if selection["thresholds"][str(seed)] != threshold:
                    raise ValueError("Retention threshold mismatch")
    steps = lines(output / "training-steps.jsonl")
    expected_steps = {
        (mode, seed, epoch, c["id"])
        for mode in m["modes"]
        for seed in m["seeds"]
        for epoch in (1, 2)
        for c in cases
        if c["split"] == "train"
    }
    if (
        len(steps) != len(expected_steps)
        or {(r["mode"], r["seed"], r["epoch"], r["id"]) for r in steps} != expected_steps
    ):
        raise ValueError("Incomplete training")
    test = [c for c in cases if c["split"] == "test"]
    scores = {
        arm: {c["id"]: float(grades[c["id"], arm]["correct"]) for c in test} for arm in test_arms
    }
    for mode in (*m["modes"], "shuffled"):
        scores[mode] = {
            c["id"]: sum(scores[f"{mode}/{seed}"][c["id"]] for seed in m["seeds"]) / len(m["seeds"])
            for c in test
        }
        scores[f"retained/{mode}"] = {
            c["id"]: sum(
                scores[f"{mode}/{seed}"][c["id"]]
                if min(res[c["id"]]["probabilities"]) < selection["thresholds"][str(seed)]
                else scores["native"][c["id"]]
                for seed in m["seeds"]
            )
            / len(m["seeds"])
            for c in test
        }
    comparisons = [(mode, "native") for mode in (*m["modes"], "shuffled", "retained/structured")]
    comparisons += [("structured", mode) for mode in ("constant", "scalar", "text", "shuffled")]
    comparisons += [
        ("retained/structured", f"retained/{mode}")
        for mode in ("constant", "scalar", "text", "shuffled")
    ]
    result = dict(
        passed=True,
        scope="Authored mechanism diagnostic, not public benchmark performance",
        outputs=len(rows),
        requests=len(receipts),
        training_steps=len(steps),
        generated_tokens=sum(len(r["generated_token_ids"]) for r in rows),
        generation_seconds=sum(r["seconds"] for r in rows),
        input_tokens=sum(r["input_tokens"] for r in receipts),
        thresholds=selection["thresholds"],
        scores={
            arm: dict(
                n=len(test),
                accuracy=sum(vals.values()) / len(test),
                by_task={
                    task: sum(vals[c["id"]] for c in test if c["task"] == task)
                    / sum(c["task"] == task for c in test)
                    for task in ("temporal", "compositional")
                },
            )
            for arm, vals in scores.items()
        },
        contrasts={f"{a}-minus-{b}": contrast(test, scores[a], scores[b]) for a, b in comparisons},
        feedback_token_changes={
            str(seed): sum(
                table[c["id"], f"structured/{seed}"]["generated_token_ids"]
                != table[c["id"], f"shuffled/{seed}"]["generated_token_ids"]
                for c in test
            )
            for seed in m["seeds"]
        },
        test_rows=[
            dict(
                id=c["id"],
                task=c["task"],
                arm=arm,
                **grades[c["id"], arm],
                finish_reason=table[c["id"], arm]["finish_reason"],
            )
            for c in test
            for arm in test_arms
        ],
    )
    C["dump"](output / "analysis.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = audit(args.input, args.output)
    print(json.dumps({k: result[k] for k in ("passed", "outputs", "requests", "scores")}))
