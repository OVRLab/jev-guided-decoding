"""Independent artifact reconstruction for the frozen R22 training/evaluation run."""

import argparse
import json
import math
import random
import runpy
from pathlib import Path

from jev_guided_decoding.jev import _probability
from jev_guided_decoding.local_claims import LocalClaimScorer

ROOT = Path(__file__).resolve().parents[2]
S = runpy.run_path(str(ROOT / "research/iterations/learned_feedback/study.py"))
LABELS = {"constructed_supported", "constructed_unsupported", "granite_draft"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def receipt_check(row):
    r, order = row["jev"], row["question_order"]
    raw = r["raw_response"]
    require(len(order) == 3 and set(order) == LABELS, "Question binding")
    require(
        raw["model"] == r["model"] == "jev-1.13.0" and r["attempts"] == 1, "Receipt model/attempt"
    )
    for key in ("input_tokens", "output_tokens"):
        require(
            type(raw["usage"][key]) is int
            and raw["usage"][key] >= 0
            and raw["usage"][key] == r[key],
            "Receipt usage mismatch",
        )
    expected = {
        label: [
            _probability(raw["answers"], f"support_{i}"),
            _probability(raw["answers"], f"assessable_{i}"),
        ]
        for i, label in enumerate(order)
    }
    require(expected == row["feedback"], "Receipt feedback mismatch")
    return r["input_tokens"], r["output_tokens"]


def work_check(row, length, eos, feedback, guided):
    ids = row["token_ids"]
    require(
        len(ids) == row["forwards"]
        and row["processed_tokens"] == length + len(ids) - 1
        and row["prefill_tokens"] == length,
        "Forward work mismatch",
    )
    require(not set(ids[:-1]) & eos, "Tokens after EOS")
    require(row["finish_reason"] == ("eos" if ids[-1] in eos else "length"), "Stop reason mismatch")
    events = row["adapter_events"]
    require(len(events) == (len(ids) if guided else 0), "Intervention count")
    for i, event in enumerate(events):
        require(
            event["layer"] == 19 and event["positions"] == [length - 1 + i], "Intervention position"
        )
        require(event["feedback"] == feedback, "Intervention feedback")
        require(
            math.isfinite(event["relative_delta"]) and 0 <= event["relative_delta"] <= 0.10001,
            "Residual norm bound",
        )


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def audit(freeze, output, tok):
    import torch
    from safetensors.torch import load_file

    runtime = runpy.run_path(str(ROOT / "research/iterations/learned_feedback/runtime.py"))
    m = S["verify"](freeze)
    require(json.loads((output / "freeze.json").read_text()) == m, "Run freeze mismatch")
    cohorts = {
        part: json.loads((freeze / (part + ".json")).read_text())
        for part in ("train", "development", "test")
    }
    cases = {c["id"]: c for part in cohorts.values() for c in part}
    starts, completed = rows(output / "starts.jsonl"), rows(output / "outputs.jsonl")
    require(len({r["job"] for r in starts}) == len(starts), "Duplicate starts")
    require(len({r["job"] for r in completed}) == len(completed), "Duplicate completions")
    require(
        {r["job"] for r in starts} == {r["job"] for r in completed}
        and all(r["status"] == "complete" for r in completed),
        "Unfinished jobs",
    )
    complete = {r["job"]: r for r in completed}
    prepared = {r["case_id"]: r for r in completed if r["job"].startswith("prepare/")}
    require(len(cases) == 864 and set(prepared) == set(cases), "Prepared coverage")
    draft_rows, attempts = (
        rows(output / "prepared-drafts.jsonl"),
        rows(output / "provider-attempts.jsonl"),
    )
    require(len(draft_rows) == len(attempts) == len(cases), "Preparation work coverage")
    require(
        len({r["case_id"] for r in draft_rows}) == len(cases)
        and len({r["case_id"] for r in attempts}) == len(cases),
        "Duplicate draft/attempt",
    )
    draft_rows = {r["case_id"]: r for r in draft_rows}
    attempts = {r["case_id"]: r for r in attempts}
    hardware = json.loads((output / "hardware.json").read_text())
    done = json.loads((output / "completion.json").read_text())
    require(
        done["unchanged_weights"]
        and hardware["original_weights_sha256"] == done["before_sha256"] == done["after_sha256"],
        "Original weight hashes",
    )
    require(hardware["adapter_parameters"] == 65568, "Adapter capacity")
    require(
        json.loads((output / "mechanical-admission.json").read_text())["passed"],
        "Missing mechanical admission",
    )
    eos = set(hardware["eos_ids"])
    scorer = LocalClaimScorer("offline-reconstruction")
    api_input, api_output, draft_tokens = 0, 0, 0
    training_examples = []
    for ident, c in cases.items():
        r = prepared[ident]
        require(r["part"] == c["split"] and r["motif"] == c["motif"], "Prepared identity")
        # Chronological event state is the oracle; never trust a stored color label alone.
        owner = None
        for event in c["events"]:
            if event["parcel"] == c["parcel"] and event["kind"] == "assign":
                owner = event["courier"]
            elif event["parcel"] == c["parcel"] and event["kind"] == "deny":
                require(owner != event["courier"], "Conflicting world")
        require(
            owner == c["owner"] and owner != c["wrong_owner"] and c["badges"][owner] == c["answer"],
            "World reference mismatch",
        )
        messages = S["D"]["messages"](c)
        ids = tok.apply_chat_template(messages, tokenize=True, add_generation_prompt=True)
        require(messages == r["messages"] and ids == r["prompt_token_ids"], "Prompt binding")
        for key, value in draft_rows[ident].items():
            if key not in ("at", "status"):
                require(r[key] == value, "Draft journal binding")
        request, candidates, order = S["S"]["feedback_inputs"](c, r["draft"])
        payload = scorer._build_payload(request, "", candidates)
        require(
            payload == r["payload"] == attempts[ident]["payload"] and order == r["question_order"],
            "Provider input binding",
        )
        require(payload["state"] == {"evidence": c["assignments"]}, "Reference-free provider view")
        inp, out = receipt_check(r)
        api_input += inp
        api_output += out
        if c["split"] == "train":
            require(
                r["draft_origin"] == "authored_training_pair" and len(r["variants"]) == 2,
                "Training draft origin",
            )
            for v, kind, entity in zip(
                r["variants"],
                ("constructed_supported", "constructed_unsupported"),
                (owner, c["wrong_owner"]),
                strict=True,
            ):
                expected_draft = tok.encode(entity, add_special_tokens=False) + [
                    tok.convert_tokens_to_ids("<|end_of_text|>")
                ]
                final = runtime["final_prefix"](tok, ids, expected_draft, c["final_question"])
                target = tok.encode(c["answer"], add_special_tokens=False) + [
                    tok.convert_tokens_to_ids("<|end_of_text|>")
                ]
                require(
                    v
                    == dict(
                        kind=kind,
                        draft_token_ids=expected_draft,
                        framing_ids=final["framing_ids"],
                        prompt_ids=final["ids"],
                        target_ids=target,
                        feedback=r["feedback"][kind],
                    ),
                    "Training example mismatch",
                )
                training_examples.append((ident, v))
        else:
            require(r["draft_origin"] == "granite", "Evaluation draft origin")
            g = r["draft_generation"]
            text = tok.decode(g["token_ids"], skip_special_tokens=True)
            require(
                text == r["draft"] == g["text"] and 0 < len(g["token_ids"]) <= 24,
                "Draft token provenance",
            )
            work_check(g, len(ids), eos, [0.5, 0.5], False)
            require(r["draft_oracle"] == S["D"]["assess"](c, text), "Draft oracle binding")
            final = runtime["final_prefix"](tok, ids, g["token_ids"], c["final_question"])
            require(
                final["ids"] == r["final_prompt_ids"] and final["framing_ids"] == r["framing_ids"],
                "Exact draft continuation",
            )
            draft_tokens += len(g["token_ids"])
    ledger = rows(output / "jev-budget.jsonl")
    reserve, settle = ([r for r in ledger if r["event"] == name] for name in ("reserve", "settle"))
    require(
        len(ledger) == 1 + len(reserve) + len(settle) and len(reserve) == len(settle) == 864,
        "Ledger coverage",
    )
    require(
        len({r["id"] for r in reserve}) == 864
        and {r["id"] for r in reserve} == {r["id"] for r in settle},
        "Budget reservation identity",
    )
    require(
        sum(r["input_tokens"] for r in settle) == api_input == done["input_tokens"], "Budget usage"
    )
    require(done["unknown_calls"] == 0 and done["successful_calls"] == 864, "Call completion")
    require(done["jev_estimate_usd"] == api_input * m["usd_per_million"] / 1e6, "Provider cost")
    selection = json.loads((output / "selection.json").read_text())
    require(
        selection["at"] < min(r["at"] for r in completed if r.get("part") == "test"),
        "Test opened before selection",
    )
    donors = json.loads((freeze / "donors.json").read_text())
    answer_counts, token_counts = {}, {}
    for part in ("development", "test"):
        answers = rows(output / (part + "-answers.jsonl"))
        expected = {
            (c["id"], mode, seed, epoch)
            for c in cohorts[part]
            for mode, seed in (
                S["ARMS"]
                if part == "test"
                else [(mo, se) for se in S["SEEDS"] for mo in ("constant", "live")]
            )
            for epoch in ((0,) if part == "test" else (1, 2))
        }
        require(
            len(answers) == len(expected)
            and {(r["case_id"], r["mode"], r["seed"], r["epoch"]) for r in answers} == expected,
            "Answer coverage",
        )
        for r in answers:
            c, source = cases[r["case_id"]], prepared[r["case_id"]]
            require(r["part"] == part and 0 < len(r["token_ids"]) <= 8, "Answer phase/budget")
            text = tok.decode(r["token_ids"], skip_special_tokens=True)
            require(
                text == r["text"] and r["grade"] == runtime["grade"](c["answer"], text),
                "Answer token/grade binding",
            )
            feedback = source["feedback"]["granite_draft"]
            if r["mode"] in ("native", "constant"):
                feedback = [0.5, 0.5]
            elif r["mode"] == "permuted":
                feedback = prepared[donors[c["id"]]]["feedback"]["granite_draft"]
            elif r["mode"] == "oracle":
                oracle = source["draft_oracle"]
                feedback = [float(oracle["supported"]), 1.0] if oracle else [0.0, 0.0]
            require(r["feedback"] == feedback, "Answer arm feedback")
            work_check(r, len(source["final_prompt_ids"]), eos, feedback, r["mode"] != "native")
            job = f"{part}/{r['mode']}/{r['seed']}/{r['epoch']}/{c['id']}"
            require(
                {k: v for k, v in complete[job].items() if k not in ("job", "at")} == r,
                "Answer journal binding",
            )
        answer_counts[part] = len(answers)
        token_counts[part] = sum(len(r["token_ids"]) for r in answers)
    steps = rows(output / "training-steps.jsonl")
    require(len(steps) == 6144, "Training forward count")
    for seed in S["SEEDS"]:
        initial = [
            load_file(str(output / f"{mode}-{seed}-initial.safetensors"))
            for mode in ("constant", "live")
        ]
        require(
            set(initial[0]) == {"down.weight", "up.weight", "condition.weight"},
            "Unexpected trained parameter",
        )
        require(
            all(torch.equal(initial[0][k], initial[1][k]) for k in initial[0])
            and not initial[0]["up.weight"].count_nonzero(),
            "Matched initial weights",
        )
        for mode in ("constant", "live"):
            dev_scores = []
            for epoch in (1, 2):
                batch = [
                    r for r in steps if (r["mode"], r["seed"], r["epoch"]) == (mode, seed, epoch)
                ]
                order = list(range(768))
                random.Random(seed * 10 + epoch).shuffle(order)
                require(
                    len(batch) == 768 and [r["example_index"] for r in batch] == order,
                    "Matched training order",
                )
                for i, r in enumerate(batch):
                    ident, example = training_examples[order[i]]
                    require(
                        r["step"] == i and r["case_id"] == ident and r["kind"] == example["kind"],
                        "Training step identity",
                    )
                    require(
                        r["updates"] == (epoch - 1) * 96 + (i + 1) // 8
                        and math.isfinite(r["loss"]),
                        "Training updates/loss",
                    )
                    require(
                        r["input_tokens"]
                        == len(example["prompt_ids"]) + len(example["target_ids"]) - 1
                        and r["target_tokens"] == len(example["target_ids"]),
                        "Training token work",
                    )
                checkpoint = output / f"{mode}-{seed}-epoch{epoch}.safetensors"
                weights = load_file(str(checkpoint))
                require(
                    set(weights) == set(initial[0])
                    and all(
                        weights[k].shape == initial[0][k].shape and torch.isfinite(weights[k]).all()
                        for k in weights
                    ),
                    "Checkpoint shape/finite",
                )
                record = complete[f"train/{mode}/{seed}/{epoch}"]
                require(
                    record["checkpoint_sha256"] == S["S"]["sha"](checkpoint)
                    and record["updates"] == epoch * 96,
                    "Checkpoint provenance",
                )
                dev = [
                    r
                    for r in rows(output / "development-answers.jsonl")
                    if (r["mode"], r["seed"], r["epoch"]) == (mode, seed, epoch)
                ]
                score = sum(r["grade"]["correct"] for r in dev) / len(dev)
                require(record["development_accuracy"] == score, "Development selection score")
                dev_scores.append(score)
            selected = selection["models"][f"{mode}/{seed}"]
            require(
                selected["epoch"] == S["choose_epoch"](dev_scores)
                and selected["development_scores"] == dev_scores,
                "Held-out checkpoint selection",
            )
            require(
                selected["sha256"] == S["S"]["sha"](output / selected["checkpoint"]),
                "Selected checkpoint hash",
            )
    expected = S["analyze"](cohorts["test"], rows(output / "test-answers.jsonl"))
    require(
        expected == json.loads((output / "analysis.json").read_text()),
        "Primary analysis reconstruction",
    )
    return dict(
        passed=True,
        source_files=len(m["sources"]),
        original_weights_unchanged=True,
        adapter_parameters=hardware["adapter_parameters"],
        training_examples=768,
        training_forwards=len(steps),
        optimizer_updates=768,
        development_outputs=answer_counts["development"],
        test_outputs=answer_counts["test"],
        draft_tokens=draft_tokens,
        answer_tokens=token_counts,
        jev_calls=864,
        jev_input_tokens=api_input,
        jev_output_tokens=api_output,
        all_output_hashes={
            p.name: S["S"]["sha"](p) for p in sorted(output.iterdir()) if p.is_file()
        },
    )


def main():
    from transformers import AutoTokenizer

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--freeze", type=Path, required=True)
    p.add_argument("--results", type=Path, required=True)
    a = p.parse_args()
    tok = AutoTokenizer.from_pretrained(
        S["S"]["MODEL"], revision=S["S"]["REVISION"], local_files_only=True
    )
    print(json.dumps(audit(a.freeze, a.results, tok), indent=2))


if __name__ == "__main__":
    main()
