"""Independent exposed-case completion audit; no model inference or provider call."""

import argparse
import json
import re
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONTRACT = runpy.run_path(str(HERE / "contract.py"))
A = runpy.run_path(str(HERE / "audit.py"))
G = runpy.run_path(str(HERE / "analysis.py"))


def metadata(m, evidence, adapters):
    hw, large, admission, done, original = (
        evidence[k] for k in ("hardware", "larger_hardware", "admission", "complete", "original")
    )
    original_outputs = m["planned_cases"] * (3 + 3 * len(m["specs"]))
    if (
        any(h["device"] not in ("cuda", "cuda:0") or h["eos"] != [100257] for h in (hw, large))
        or hw["dtype"] != "torch.float32"
        or large["dtype"] != m["larger_dtype"]
        or hw["parameters"] != 1631750144
        or large["parameters"] <= hw["parameters"]
        or admission["device"] not in ("cuda", "cuda:0")
        or admission["api_calls"] != 0
        or any(
            admission[k] is not True
            for k in (
                "passed",
                "initial_identity",
                "off_identity",
                "cache_argmax_equal",
                "backbone_gradients_absent",
            )
        )
        or not A["nonnegative"](admission["cache_max_logit_error"])
        or admission["cache_max_logit_error"] > 0.001
        or admission["memory_shape"] != [2048]
        or admission["dummy_adapter_parameters"] != 262144
        or any(
            record[k] != m["backbone_digest"]
            for record in (admission, original)
            for k in ("backbone_before", "backbone_after")
        )
        or original["adapters_before"] != adapters
        or original["adapters_after"] != adapters
        or original["outputs"] != original_outputs
        or done["outputs"] != m["planned_outputs"]
        or done["requests"] != m["planned_requests"]
        or done["charged_input_tokens"] != original["charged_input_tokens"]
        or not A["nonnegative"](done["seconds"])
        or not A["nonnegative"](done["post_original_load_seconds"])
        or done["post_original_load_seconds"] > m["max_seconds"]
        or done["seconds"] < done["post_original_load_seconds"]
    ):
        raise ValueError("Incomplete R32a work, invalid device/dtype or changed frozen weights")


def summarize(cases, refs, rows, responses):
    ids = {c["id"] for c in cases}
    by_id = {c["id"]: c for c in cases}
    if set(refs) != ids or len(ids) != len(cases):
        raise ValueError("Invalid development reference coverage")
    table = {(r["id"], r["arm"]): r for r in rows}
    arms = sorted({r["arm"] for r in rows})
    if len(table) != len(rows) or set(table) != {(i, arm) for i in ids for arm in arms}:
        raise ValueError("Incomplete development output coverage")
    grades = {}
    for (ident, arm), row in table.items():
        grades[ident, arm] = G["grade"](
            row["text"], by_id[ident]["choices"], refs[ident], thinking=arm == "larger/thinking"
        )
    grouped = {arm: [arm] for arm in arms}
    for arm in arms:
        if re.fullmatch(r"(live|constant|donor)/(contextual|embedding)-scalar/\d+", arm):
            grouped.setdefault(arm.rsplit("/", 1)[0], []).append(arm)
    scores, preservation = {}, {}
    for name, members in grouped.items():
        individual = {(ident, arm): grades[ident, arm] for ident in ids for arm in members}
        n = len(individual)
        scores[name] = dict(
            cases=len(ids),
            seed_outputs=len(members),
            accuracy=sum(v["correct"] for v in individual.values()) / n,
            equivalent_choice_accuracy=sum(v["equivalent_choice"] for v in individual.values()) / n,
            unreadable=sum(v["unreadable"] for v in individual.values()) / n,
            format=sum(v["format"] for v in individual.values()) / n,
            length_stops=sum(table[key]["finish_reason"] == "length" for key in individual) / n,
            by_task={
                task: sum(
                    grades[c["id"], a]["correct"]
                    for c in cases
                    if c["task"] == task
                    for a in members
                )
                / (sum(c["task"] == task for c in cases) * len(members))
                for task in sorted({c["task"] for c in cases})
            },
        )
        preservation[name] = dict(
            fixed=sum(
                not grades[i, "native"]["correct"] and grades[i, a]["correct"]
                for i in ids
                for a in members
            )
            / len(members),
            damaged=sum(
                grades[i, "native"]["correct"] and not grades[i, a]["correct"]
                for i in ids
                for a in members
            )
            / len(members),
        )
    response = {r["id"]: r for r in responses}
    if len(response) != len(responses) or set(response) != ids:
        raise ValueError("Incomplete development feedback diagnostic")
    correct = [i for i in sorted(ids) if grades[i, "native"]["correct"]]
    wrong = sorted(ids - set(correct))
    return dict(
        scores=scores,
        preservation=preservation,
        feedback_diagnostic=dict(
            scope="Jev judgments of native correctness; never a generator benchmark arm",
            native_correct=len(correct),
            native_wrong=len(wrong),
            mean_p_correct=sum(response[i]["probability"] for i in correct) / len(correct)
            if correct
            else None,
            mean_p_wrong=sum(response[i]["probability"] for i in wrong) / len(wrong)
            if wrong
            else None,
            brier=sum(
                (response[i]["probability"] - grades[i, "native"]["correct"]) ** 2 for i in ids
            )
            / len(ids),
        ),
    )


def check(inputs, output):
    import torch
    from safetensors.torch import load_file
    from transformers import AutoTokenizer

    m = CONTRACT["verify"](inputs)
    required = {
        "execution.json",
        "original-hardware.json",
        "mechanical-admission.json",
        "adapter-bindings.json",
        "original-complete.json",
        "larger-hardware.json",
        "complete.json",
        "original",
        "larger",
    }
    if {p.name for p in output.iterdir()} - {"analysis.json"} != required or any(
        p.is_symlink() for p in output.rglob("*")
    ):
        raise ValueError("Incomplete or unexpected R32a artifacts")

    def read(name):
        return json.loads((output / name).read_text())

    execution = read("execution.json")
    if (
        execution["manifest_sha256"] != CONTRACT["sha"](inputs / "manifest.json")
        or execution["sources"] != m["sources"]
        or execution["device"] != "cuda"
    ):
        raise ValueError("Unbound R32a source/manifest/device execution")
    cases = json.loads((inputs / "cases.json").read_text())
    groups = json.loads((inputs / "groups.json").read_text())
    selection = json.loads((inputs / "selection.json").read_text())
    runtime = runpy.run_path(str(HERE / "runtime.py"))
    adapters = {}
    for name, seed in m["specs"]:
        key = f"{name}/{seed}"
        model = runtime["B"]["Repair"](2048, m["rank"])
        model.load_state_dict(
            load_file(str(inputs / "adapters" / selection[key]["file"])), strict=True
        )
        if any(not torch.isfinite(p).all() for p in model.parameters()):
            raise ValueError("Nonfinite selected checkpoint")
        adapters[key] = runtime["weight_digest"](model)
    evidence = dict(
        hardware=read("original-hardware.json"),
        larger_hardware=read("larger-hardware.json"),
        admission=read("mechanical-admission.json"),
        complete=read("complete.json"),
        original=read("original-complete.json"),
    )
    metadata(m, evidence, adapters)
    bindings = read("adapter-bindings.json")
    if bindings["before"] != adapters:
        raise ValueError("Changed pre-inference adapter binding")
    expected_original = {
        "memories",
        "budget.jsonl",
        "requests.jsonl",
        "responses.jsonl",
        "generation-bindings.jsonl",
        "jobs.jsonl",
        "outputs.jsonl",
        "memory-records.jsonl",
        "donors.json",
    }
    if {p.name for p in (output / "original").iterdir()} != expected_original:
        raise ValueError("Unknown charge or unexpected original-run artifact")
    tok = AutoTokenizer.from_pretrained(m["model"], revision=m["revision"], trust_remote_code=False)
    small = A["check_run"](cases, groups, output / "original", tok, m, adapters)
    larger_tok = AutoTokenizer.from_pretrained(
        m["larger_model"], revision=m["larger_revision"], trust_remote_code=False
    )
    large = A["check_comparator"](cases, m["larger_profiles"], output / "larger", larger_tok)
    small_rows = A["lines"](output / "original/outputs.jsonl")
    large_rows = A["lines"](output / "larger/outputs.jsonl")
    large_admission = json.loads((output / "larger/mechanical-admission.json").read_text())
    if (
        small["outputs"] + large["outputs"] != m["planned_outputs"]
        or small["input_tokens"] != evidence["complete"]["charged_input_tokens"]
        or not execution["at"] <= bindings["at"] <= min(r["at"] for r in small_rows)
        or max(r["at"] for r in small_rows) > evidence["original"]["at"]
        or evidence["original"]["at"] > min(r["at"] for r in large_rows)
        or max(r["at"] for r in large_rows) > evidence["complete"]["at"]
        or large_admission["device"] not in ("cuda", "cuda:0")
        or large_admission["dtype"] != m["larger_dtype"]
    ):
        raise ValueError("Incorrect combined coverage, charge or temporal ownership")
    refs = json.loads((inputs / "references.json").read_text())
    quality = summarize(
        cases,
        refs,
        small_rows + [r | dict(arm="larger/" + r["arm"]) for r in large_rows],
        A["lines"](output / "original/responses.jsonl"),
    )
    return dict(
        passed=True,
        scope="Twelve exposed development cases; not fresh public benchmark quality",
        cases=len(cases),
        groups=len(set(groups.values())),
        outputs=small["outputs"] + large["outputs"],
        requests=small["requests"],
        original_work=small,
        larger_work=large,
        **quality,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = check(args.input, args.output)
    CONTRACT["dump"](args.output / "analysis.json", result)
    print(json.dumps(dict(passed=True, outputs=result["outputs"], requests=result["requests"])))


if __name__ == "__main__":
    main()
