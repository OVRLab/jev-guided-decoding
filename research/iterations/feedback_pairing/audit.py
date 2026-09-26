"""Independent R30 token, feedback, checkpoint and paired-outcome reconstruction."""

import argparse
import json
import math
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
C = runpy.run_path(str(HERE / "common.py"))
OLD = C["R29"]


def lines(path):
    return [json.loads(s) for s in path.read_text().splitlines()] if path.exists() else []


def check_receipts(cases, natives, requests, responses, ledger):
    ids = {c["id"] for c in cases}
    req = {r["id"]: r for r in requests}
    res = {r["id"]: r for r in responses}
    if (
        len(ids) != len(cases)
        or set(req) != ids
        or set(res) != ids
        or len(req) != len(requests)
        or len(res) != len(responses)
    ):
        raise ValueError("Missing or duplicate feedback")
    reserves = [r["id"] for r in ledger if r["event"] == "reserve"]
    settled_rows = [r for r in ledger if r["event"] == "settle"]
    settles = {r["id"]: r["input_tokens"] for r in settled_rows}
    if (
        len(set(reserves)) != len(reserves)
        or len(settles) != len(settled_rows)
        or set(reserves) != set(settles)
        or set(reserves) != {r["reservation"] for r in responses}
        or len(reserves) != len(cases)
    ):
        raise ValueError("Duplicate, missing or unresolved charge")
    for case in cases:
        ident = case["id"]
        request, receipt, native = req[ident], res[ident], natives[ident]
        raw = receipt["raw"]
        if request["payload"] != OLD["payload"](case, native["text"]):
            raise ValueError("Payload does not bind the exact native draft")
        if (
            receipt["model"] != "jev-1.13.0"
            or raw["model"] != receipt["model"]
            or receipt["attempts"] != 1
            or request["reservation"] != receipt["reservation"]
            or raw["usage"]["input_tokens"] != receipt["input_tokens"]
            or raw["usage"]["output_tokens"] != receipt["output_tokens"]
            or settles[receipt["reservation"]] != receipt["input_tokens"]
            or native["at"] > request["at"]
            or request["at"] > receipt["at"]
            or not math.isfinite(receipt["seconds"])
            or receipt["seconds"] < 0
            or set(raw["answers"]) != {"q1", "q2", "q3"}
        ):
            raise ValueError("Provider identity, usage or timing mismatch")
        if any(
            type(receipt[k]) is not int or receipt[k] < 0 for k in ("input_tokens", "output_tokens")
        ):
            raise ValueError("Invalid usage count")
        answers = [raw["answers"][f"q{i}"] for i in (1, 2, 3)]
        if (
            any(a["type"] != "noul" for a in answers)
            or OLD["probabilities"]([a["noul"] for a in answers]) != receipt["probabilities"]
        ):
            raise ValueError("Changed feedback probabilities")
    return sum(settles.values())


def check_generation(row, prompt, p, tok, eos, limit, layer):
    generated = row["generated_token_ids"]
    if row["prompt_token_ids"] != prompt or not prompt or len(prompt) > 2048:
        raise ValueError("Prompt/draft token provenance mismatch")
    if (
        not generated
        or len(generated) > limit
        or any(type(t) is not int or t < 0 for t in generated)
        or eos in generated[:-1]
    ):
        raise ValueError("Invalid generation tokens")
    body = generated[:-1] if generated[-1] == eos else generated
    if tok.decode(body, skip_special_tokens=False) != row["text"] or row["finish_reason"] != (
        "eos" if generated[-1] == eos else "length"
    ):
        raise ValueError("Final tokens, text or stop reason changed")
    if row["probabilities"] != p:
        raise ValueError("Wrong paired feedback")
    if p is None:
        if row["events"]:
            raise ValueError("Unexpected baseline intervention")
    else:
        positions = [i for e in row["events"] for i in e["positions"]]
        if positions != list(range(len(prompt) - 1, len(prompt) + len(generated) - 1)) or any(
            e["feedback"] != p or e["layer"] != layer for e in row["events"]
        ):
            raise ValueError("Intervention positions or scores changed")


def summarize(cases, grades, table, responses, seeds):
    ids = [c["id"] for c in cases]
    scores = {arm: {i: float(grades[i, arm]["correct"]) for i in ids} for arm in C["arms"](seeds)}
    for mode in C["MODES"]:
        scores[mode] = {
            i: sum(scores[f"{mode}/{seed}"][i] for seed in seeds) / len(seeds) for i in ids
        }
    scores["permutation_mean"] = {
        i: (scores["rotate_left"][i] + scores["rotate_right"][i]) / 2 for i in ids
    }
    scores["retained_half"] = {
        i: scores["live"][i] if min(responses[i]["probabilities"]) < 0.5 else scores["native"][i]
        for i in ids
    }
    scores["retained_zero"] = dict(scores["native"])
    primary = ("native", "mean", "permutation_mean")
    other = (
        "blind",
        "rotate_left",
        "rotate_right",
        "donor",
        "constant",
        "type_only",
        "oracle",
        "scalar_trained",
    )
    contrasts = {
        f"live-minus-{arm}": C["effect"](cases, scores["live"], scores[arm])
        | {"primary": arm in primary}
        for arm in (*primary, *other)
    }
    contrasts["retained_half-minus-native"] = C["effect"](
        cases, scores["retained_half"], scores["native"]
    ) | {"primary": False}
    return dict(
        scores={
            arm: dict(
                n=len(ids),
                accuracy=sum(v.values()) / len(ids),
                by_task={
                    task: sum(v[c["id"]] for c in cases if c["task"] == task)
                    / sum(c["task"] == task for c in cases)
                    for task in sorted({c["task"] for c in cases})
                },
            )
            for arm, v in scores.items()
        },
        contrasts=contrasts,
        practical_equivalence_mean_95=all(
            -2 <= bound <= 2 for bound in contrasts["live-minus-mean"]["ci95_pp"]
        ),
        selected_at_half=sum(min(responses[i]["probabilities"]) < 0.5 for i in ids),
        token_changes={
            str(seed): {
                mode: sum(
                    table[i, f"live/{seed}"]["generated_token_ids"]
                    != table[i, f"{mode}/{seed}"]["generated_token_ids"]
                    for i in ids
                )
                for mode in C["MODES"]
                if mode != "live"
            }
            for seed in seeds
        },
        per_seed_native_effects={
            str(seed): C["effect"](cases, scores[f"live/{seed}"], scores["native"])
            for seed in seeds
        },
        per_arm_readout={
            arm: dict(
                slot_accuracy=sum(sum(grades[i, arm]["slots"]) for i in ids) / (3 * len(ids)),
                format_passes=sum(grades[i, arm]["format"] for i in ids),
                empty=sum(not table[i, arm]["text"].strip() for i in ids),
                length_stops=sum(table[i, arm]["finish_reason"] == "length" for i in ids),
            )
            for arm in C["arms"](seeds)
        },
        test_rows=[
            dict(id=c["id"], task=c["task"], arm=arm, **grades[c["id"], arm])
            for c in cases
            for arm in C["arms"](seeds)
        ],
    )


def audit(folder, output):
    import torch
    from safetensors.torch import load_file
    from transformers import AutoTokenizer

    S = runpy.run_path(str(HERE / "study.py"))
    R = runpy.run_path(str(HERE.parent / "structured_correction/runtime.py"))
    replay = runpy.run_path(str(HERE.parent / "structured_correction/audit.py"))["replay_reference"]
    m = S["verify"](folder)
    cases = json.loads((folder / "cases.json").read_text())
    refs = json.loads((folder / "references.json").read_text())
    if any(replay(c) != refs[c["id"]] for c in cases):
        raise ValueError("Independent graph replay disagrees")
    old, _ = OLD["make_data"]()
    if {c["prompt"] for c in cases} & {c["prompt"] for c in old}:
        raise ValueError("Exposed R29 case overlap")
    complete = json.loads((output / "complete.json").read_text())
    execution = json.loads((output / "execution.json").read_text())
    admission = json.loads((output / "mechanical-admission.json").read_text())
    if (
        execution["manifest_sha256"] != C["sha"](folder / "manifest.json")
        or execution["sources"] != m["sources"]
        or not admission["passed"]
    ):
        raise ValueError("Frozen execution/admission mismatch")
    if (
        complete["backbone_before"] != complete["backbone_after"]
        or complete["adapters_before"] != complete["adapters_after"]
        or any((output / f).exists() for f in ("failed.json", "failures.jsonl"))
    ):
        raise ValueError("Changed weights or failed execution")
    selection = json.loads((folder / "r29-selection.json").read_text())
    prov = json.loads((folder / "r29-provenance.json").read_text())
    if (
        prov
        != json.loads(
            (C["ROOT"] / "reports/2026-09-26-structured-correction/provenance.json").read_text()
        )
        or C["sha"](folder / "r29-selection.json")
        != prov["original_backup_inventory"]["selection.json"]
    ):
        raise ValueError("Changed upstream provenance")
    bindings = json.loads((output / "adapter-bindings.json").read_text())
    if (
        bindings["checkpoints"] != m["checkpoints"]
        or bindings["before"] != complete["adapters_before"]
    ):
        raise ValueError("Adapter binding mismatch")
    expected_keys = {f"{mode}/{seed}" for mode in ("structured", "scalar") for seed in m["seeds"]}
    if set(m["checkpoints"]) != expected_keys or set(bindings["before"]) != expected_keys:
        raise ValueError("Missing or substituted adapters")
    for key, row in m["checkpoints"].items():
        selected = selection["models"][key]
        if (
            row
            != dict(
                file="checkpoints/" + selected["file"],
                sha256=selected["sha256"],
                epoch=selected["epoch"],
            )
            or row["sha256"] != prov["original_backup_inventory"][selected["file"]]
        ):
            raise ValueError("Adapter differs from original selected checkpoint")
        weights = load_file(str(folder / row["file"]))
        adapter = R["B"]["Repair"](weights["down.weight"].shape[1], m["rank"])
        adapter.load_state_dict(weights)
        if (
            any(not torch.isfinite(p).all() for p in adapter.parameters())
            or R["weight_digest"](adapter) != bindings["before"][key]
        ):
            raise ValueError("Loaded adapter digest mismatch")
    rows = lines(output / "outputs.jsonl")
    C["coverage"](cases, rows, m["seeds"])
    if len(rows) != complete["outputs"] or len(rows) != m["planned_outputs"]:
        raise ValueError("Wrong output denominator")
    table = {(r["id"], r["arm"]): r for r in rows}
    native = {c["id"]: table[c["id"], "native"] for c in cases}
    responses = lines(output / "responses.jsonl")
    input_tokens = check_receipts(
        cases, native, lines(output / "requests.jsonl"), responses, lines(output / "budget.jsonl")
    )
    if input_tokens != complete["charged_input_tokens"]:
        raise ValueError("Charge total mismatch")
    res = {r["id"]: r for r in responses}
    donors = json.loads((output / "donors.json").read_text())
    if donors != C["donors"](cases):
        raise ValueError("Incorrect donor mapping")
    jobs = lines(output / "jobs.jsonl")
    if [(j["id"], j["arm"], j["event"]) for j in jobs] != [
        (r["id"], r["arm"], event) for r in rows for event in ("start", "finish")
    ]:
        raise ValueError("Unmatched, missing or repeated generation job")
    tok = AutoTokenizer.from_pretrained(m["model"], revision=m["revision"])
    eos = tok.convert_tokens_to_ids("<|end_of_text|>")
    grades, by_id = {}, {c["id"]: c for c in cases}
    for row in rows:
        case = by_id[row["id"]]
        ident, mode = case["id"], row["arm"].split("/")[0]
        prompt = tok.apply_chat_template(
            [dict(role="user", content=case["prompt"])], tokenize=True, add_generation_prompt=True
        )
        if mode != "native":
            prompt = OLD["repair_prefix"](tok, prompt, native[ident]["generated_token_ids"])
        p = (
            None
            if mode in ("native", "blind")
            else C["signal"](
                mode,
                res[ident]["probabilities"],
                donor=res[donors[ident]]["probabilities"],
                truth=OLD["grade"](native[ident]["text"], refs[ident])["slots"],
                draft=native[ident]["text"],
            )
        )
        check_generation(row, prompt, p, tok, eos, m["limit"], m["layer"])
        if (
            row["task"] != case["task"]
            or row["split"] != "test"
            or not math.isfinite(row["seconds"])
            or row["seconds"] < 0
            or row["processed_tokens"] != len(prompt) + len(row["generated_token_ids"]) - 1
        ):
            raise ValueError("Case or work accounting mismatch")
        if mode != "native" and row["at"] < res[ident]["at"]:
            raise ValueError("Repair preceded its feedback")
        grades[ident, row["arm"]] = OLD["grade"](row["text"], refs[ident])
    result = dict(
        passed=True,
        scope="Fresh authored-world replication; not public benchmark performance",
        outputs=len(rows),
        requests=len(responses),
        input_tokens=input_tokens,
        generated_tokens=sum(len(r["generated_token_ids"]) for r in rows),
        generation_seconds=sum(r["seconds"] for r in rows),
        source_manifest_sha256=C["sha"](folder / "manifest.json"),
        **summarize(cases, grades, table, res, m["seeds"]),
    )
    C["dump"](output / "analysis.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.input, args.output)
    print(
        json.dumps({k: result[k] for k in ("passed", "outputs", "requests", "scores", "contrasts")})
    )
