"""Offline R17 provenance reconstruction, paired statistics and gate trade-offs."""

import argparse
import hashlib
import json
import math
import random
import runpy
import statistics
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
D = runpy.run_path(str(HERE / "data.py"))
P = runpy.run_path(str(HERE / "policies.py"))
J = runpy.run_path(str(HERE.parent / "adaptive_attention/journal.py"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_output(row, encoded, tokenizer=None):
    require(row["status"] == "complete", "Incomplete outcome requires explicit accounting")
    require(row["prompt_digest"] == encoded["prompt_digest"], "Prompt binding mismatch")
    for name in ("final", "pilot"):
        output = row[name]
        if output is None:
            continue
        ids, tokens = output["token_ids"], output["tokens"]
        require(0 < len(ids) <= (8 if name == "pilot" else 32), "Token cap mismatch")
        require(ids == [t["token_id"] for t in tokens], "Token records mismatch")
        require(output["input_and_output_ids"] == encoded["input_ids"] + ids, "Prefix mismatch")
        require(output["model_forwards"] == len(ids), "Forward accounting mismatch")
        require(
            output["processed_tokens"] == len(encoded["input_ids"]) + len(ids) - 1,
            "Cache accounting mismatch",
        )
        require(output["prompt_tokens"] == len(encoded["input_ids"]), "Prompt accounting mismatch")
        require(
            output["hook_calls"] == sum(t["hook_calls"] for t in tokens), "Hook accounting mismatch"
        )
        require(output["finish_reason"] in ("eos", "token_limit"), "Unknown termination")
        for step, t in enumerate(tokens):
            require(t["token_id"] == t["argmax_id"] == t["top_ids"][0], "Non-generator token")
            require(
                "allowed_ids" not in t and t["selected_logit"] == t["top_logits"][0],
                "Constrained token",
            )
            require(
                0 <= t["probability"] <= 1 and math.isfinite(t["entropy"]) and t["entropy"] >= 0,
                "Invalid gate observation",
            )
            scale = (
                P["strength"](row["policy"], step)
                if name == "final" and row["guided_path"]
                else 0.0
            )
            require(t["strength"] == scale, "Wrong intervention envelope")
            heads, layers = 0, 0
            if scale:
                mapped = [s > row["policy"]["threshold"] for s in row["applied_scores"]]
                if any(mapped) and not all(mapped):
                    heads = len(row["policy"]["heads"])
                    layers = len({h[0] for h in row["policy"]["heads"]})
            require(
                (t["active_heads"], t["hook_calls"]) == (heads, layers), "Wrong head/layer activity"
            )
        if tokenizer is not None:
            require(
                tokenizer.decode(ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
                == output["text"],
                "Text decoding mismatch",
            )
    final, pilot = row["final"], row["pilot"]
    require(row["text"] == final["text"], "Final answer provenance mismatch")
    require(
        row["intervention_used"] == any(t["active_heads"] for t in final["tokens"]),
        "Intervention status mismatch",
    )
    extra = 0
    if pilot:
        if row["pilot_reused"]:
            require(
                final["tokens"][: len(pilot["tokens"])] == pilot["tokens"], "Accepted pilot changed"
            )
        else:
            extra = len(pilot["token_ids"])
    require(
        row["model_forwards"] == len(final["token_ids"]) + extra,
        "Discarded work accounting mismatch",
    )
    require(row["logical_jev_calls"] in (0, 1), "Call cap exceeded")
    require(
        (row["receipt_key"] is None) == (row["logical_jev_calls"] == 0),
        "Hidden/skipped provider call",
    )
    if row["gate"] is not None:
        require(pilot is not None, "Gate lacks a pilot")
        expected = P["gate_decision"](row["gate"], row["features"], row.get("case_id", "test"))
        require(expected == row["call_decision"], "Gate decision mismatch")
        require(row["logical_jev_calls"] == int(expected), "Skipped gate called provider")
    if row["provider_status"] == "failed_fallback":
        require(
            not row["guided_path"] and not row["intervention_used"],
            "Failed receipt changed inference",
        )


def paired(values, level=0.95):
    import numpy as np

    x = np.asarray(values, dtype=float)
    rng = np.random.default_rng(170922349)
    bootstrap = np.empty(10000)
    for start in range(0, 10000, 500):
        bootstrap[start : start + 500] = rng.choice(x, size=(500, len(x)), replace=True).mean(1)
    alpha = 1 - level
    return dict(
        difference=float(x.mean()),
        interval=np.quantile(bootstrap, [alpha / 2, 1 - alpha / 2]).tolist(),
        level=level,
        units=len(x),
        wins=int((x > 0).sum()),
        losses=int((x < 0).sum()),
        ties=int((x == 0).sum()),
    )


def analyze(manifest_folder, results, tokenizer):
    S, STUDY, R = (runpy.run_path(str(HERE / f"{n}.py")) for n in ("scorer", "study", "runtime"))
    manifest = json.loads((manifest_folder / "manifest.json").read_text())
    require(STUDY["source_hashes"]() == manifest["sources"], "Scientific source changed")
    require(
        json.loads((results / "freeze.json").read_text()) == manifest, "Execution freeze changed"
    )
    for name, digest in manifest["datasets"].items():
        require(D["sha"](manifest_folder / name) == digest, "Dataset changed")
    data = {
        n: json.loads((manifest_folder / f"{n}.json").read_text())
        for n in ("development", "test", "admission", "schedule")
    }
    cases = {c["id"]: c for c in data["development"] + data["test"]}
    require(len(cases) == len(data["development"]) + len(data["test"]), "Split overlap")
    for c in cases.values():
        if c["family"] != "hotpot":
            require(
                D["OLD"]["visible_reference"](c) == c["reference"], "Visible graph truth mismatch"
            )
    inputs = {r["id"]: r for r in J["rows"](results / "inputs.jsonl")}
    require(set(inputs) == set(cases), "Missing/extra inputs")
    for ident, recorded in inputs.items():
        rebuilt = R["encode"](tokenizer, D["public_view"](cases[ident]))
        require(
            json.loads(json.dumps(rebuilt)) == {k: v for k, v in recorded.items() if k != "id"},
            "Prompt reconstruction mismatch",
        )
    outputs = J["rows"](results / "outputs.jsonl")
    starts = J["rows"](results / "starts.jsonl")
    index = {(r["stage"], r["case_id"], r["arm"]): r for r in outputs}
    require(len(index) == len(outputs), "Duplicate outcomes")
    require({r["job"] for r in starts} == {r["job"] for r in outputs}, "Unaccounted started jobs")
    planned = {("test", j["case_id"], j["arm"]) for j in data["schedule"]}
    planned |= {
        ("development", c["id"], p["id"] if p else "native")
        for c in data["development"]
        for p in [None, *P["grid"]()]
    }
    require(set(index) == planned, "Incomplete or expanded schedule")
    require(all(r["status"] == "complete" for r in outputs), "Incomplete schedule outcomes")
    start_index = {r["job"]: r for r in starts}
    receipts_raw = J["rows"](results / "receipts.jsonl")
    receipts = {r["key"]: r for r in receipts_raw if r["status"] != "started"}
    attempts = [r for r in receipts_raw if r["status"] == "started"]
    require(
        len(attempts) == len(receipts) == len({r["key"] for r in attempts}),
        "Attempt replay/incomplete receipt",
    )
    for key, receipt in receipts.items():
        require(
            hashlib.sha256(json.dumps(receipt["payload"], sort_keys=True).encode()).hexdigest()
            == key,
            "Receipt hash mismatch",
        )
        if receipt["status"] == "complete":
            raw = receipt["raw_response"]
            require(
                raw["model"] == manifest["jev_model"]
                and raw["usage"]["input_tokens"] == receipt["input_tokens"],
                "Provider model/usage mismatch",
            )
            require(
                [raw["answers"][f"relevance_{i}"]["noul"] for i in range(len(receipt["scores"]))]
                == receipt["scores"],
                "Raw score mismatch",
            )
    for row in outputs:
        c, encoded = cases[row["case_id"]], inputs[row["case_id"]]
        require(
            all(row.get(k) == v for k, v in start_index[row["job"]]["metadata"].items()),
            "Job metadata changed",
        )
        check_output(row, encoded, tokenizer)
        require(
            D["grade"](c, row["text"], "open_explicit") == row["grade"],
            "Grade reconstruction mismatch",
        )
        if row["pilot"]:
            expected = P["features"](
                row["pilot"]["tokens"], row["pilot"]["text"], D["public_view"](c)
            )
            require(expected == row["features"], "Gate feature reconstruction mismatch")
        if row["receipt_key"]:
            receipt = receipts[row["receipt_key"]]
            require(
                receipt["payload"] == S["payload_for"](D["public_view"](c), manifest["jev_model"]),
                "Scorer saw wrong input",
            )
            require(
                row["raw_scores"]
                == (receipt["scores"] if receipt["status"] == "complete" else None),
                "Wrong scorer scores",
            )
        elif row["arm"] == "lexical":
            require(
                row["raw_scores"] == D["OLD"]["lexical"](D["public_view"](c)),
                "Wrong lexical scores",
            )
        applied = None if row["raw_scores"] is None else list(row["raw_scores"])
        if applied is not None and row["arm"] == "shuffled":
            random.Random("r17-shuffle/" + c["id"]).shuffle(applied)
        require(applied == row["applied_scores"], "Applied relevance mismatch")
    selected = json.loads((results / "selected.json").read_text())
    metrics, gate_rows = [], []
    for p in P["grid"]():
        rows = [
            {
                "family": D["domain"](c),
                "quality": D["quality"](c, index["development", c["id"], p["id"]]["grade"]),
            }
            for c in data["development"]
        ]
        metrics.append(dict(policy=p, quality=P["balanced"](rows, "quality")))
    require(
        metrics == selected["all_policies"] and P["choose_policy"](metrics) == selected["selected"],
        "Policy selection mismatch",
    )
    for c in data["development"]:
        n = index["development", c["id"], "native"]
        guided = index["development", c["id"], selected["selected"]["policy"]["id"]]
        tokens = n["final"]["tokens"][:8]
        text = tokenizer.decode(
            [t["token_id"] for t in tokens],
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )
        gate_rows.append(
            dict(
                case_id=c["id"],
                family=D["domain"](c),
                features=P["features"](tokens, text, D["public_view"](c)),
                native_quality=D["quality"](c, n["grade"]),
                guided_quality=D["quality"](c, guided["grade"]),
            )
        )
    require(
        gate_rows == selected["gate_development"]
        and P["fit_gates"](gate_rows) == selected["gates"],
        "Gate fitting mismatch",
    )
    freeze = json.loads((results / "test-freeze.json").read_text())
    require(
        freeze["selected_sha256"] == D["sha"](results / "selected.json")
        and freeze["sources"] == manifest["sources"]
        and freeze["schedule_sha256"] == manifest["datasets"]["schedule.json"],
        "Test freeze mismatch",
    )
    require(
        selected["at"] < min(s["at"] for s in starts if s["metadata"]["stage"] == "test"),
        "Selection happened after test start",
    )
    native_pairs = pilot_pairs = 0
    for c in data["test"]:
        native = index["test", c["id"], "native"]
        always = index["test", c["id"], "always"]
        for arm in STUDY["ARMS"]:
            row = index["test", c["id"], arm]
            policy, gate = STUDY["arm_config"](arm, selected)
            require(
                (row["policy"], row["gate"]) == (policy, gate),
                "Held-out policy differs from freeze",
            )
            if row["pilot"]:
                require(
                    row["pilot"]["tokens"]
                    == native["final"]["tokens"][: len(row["pilot"]["tokens"])],
                    "Native pilot drift",
                )
                pilot_pairs += 1
            if not row["guided_path"]:
                require(
                    row["final"]["token_ids"] == native["final"]["token_ids"],
                    "Skipped/fallback native drift",
                )
                native_pairs += 1
            elif arm in ("benefit_gate", "uncertainty_gate", "random_gate"):
                require(
                    row["final"]["token_ids"] == always["final"]["token_ids"],
                    "Gate changed guided output",
                )
        benefit = index["test", c["id"], "benefit_gate"]
        require(
            benefit["physical_jev_attempts"] == benefit["logical_jev_calls"],
            "Prospective gate used a prior cached receipt",
        )
    ledger = J["rows"](results / "ledger.jsonl")
    reserves = {r["id"] for r in ledger if r["event"] == "reserve"}
    settled = {r["id"]: r["input_tokens"] for r in ledger if r["event"] == "settle"}
    unknown = {r["id"] for r in ledger if r["event"] == "charge_max_unknown"}
    require(
        reserves == {r["reservation"] for r in attempts} == set(settled) | unknown
        and not set(settled) & unknown,
        "Reservation accounting mismatch",
    )
    require(
        sum(r["physical_jev_attempts"] for r in outputs) == len(attempts),
        "Job/physical attempt mismatch",
    )
    completion = json.loads((results / "completion.json").read_text())
    loads = J["rows"](results / "loads.jsonl")
    require(
        completion["weights_before"] == completion["weights_after"] == loads[0]["weights_before"]
        and len(loads) == 1
        and not loads[0]["dirty"],
        "Weights/source execution mismatch",
    )
    require(
        completion["charged_tokens"] == sum(settled.values()) + 65536 * len(unknown),
        "Charged tokens mismatch",
    )
    summaries, contrasts, gate_diagnostics = [], [], []
    for domain in ("synthetic", "hotpot"):
        cohort = [c for c in data["test"] if D["domain"](c) == domain]
        for arm in STUDY["ARMS"]:
            rows = [index["test", c["id"], arm] for c in cohort]
            summaries.append(
                dict(
                    domain=domain,
                    arm=arm,
                    cases=len(rows),
                    quality=sum(
                        D["quality"](c, r["grade"]) for c, r in zip(cohort, rows, strict=True)
                    )
                    / len(rows),
                    em=statistics.mean(r["grade"]["em"] for r in rows),
                    f1=statistics.mean(r["grade"]["f1"] for r in rows),
                    parser_coverage=statistics.mean(r["grade"]["parsed"] is not None for r in rows)
                    if domain == "synthetic"
                    else None,
                    call_fraction=statistics.mean(r["logical_jev_calls"] for r in rows),
                    actual_api_attempts=sum(r["physical_jev_attempts"] for r in rows),
                    fallbacks=sum(r["provider_status"] == "failed_fallback" for r in rows),
                    mean_model_seconds=statistics.mean(r["model_seconds"] for r in rows),
                    mean_uncached_wall_seconds=statistics.mean(
                        r["estimated_uncached_wall_seconds"] for r in rows
                    ),
                    median_uncached_wall_seconds=statistics.median(
                        r["estimated_uncached_wall_seconds"] for r in rows
                    ),
                    model_forwards=sum(r["model_forwards"] for r in rows),
                    final_tokens=sum(len(r["final"]["tokens"]) for r in rows),
                    discarded_tokens=sum(
                        len(r["pilot"]["tokens"])
                        for r in rows
                        if r["pilot"] and not r["pilot_reused"]
                    ),
                    eos=sum(r["final"]["finish_reason"] == "eos" for r in rows),
                )
            )
        pairs = [
            ("always", "native", True),
            ("benefit_gate", "always", True),
            ("benefit_gate", "native", False),
            ("benefit_gate", "random_gate", False),
            ("uncertainty_gate", "always", False),
            ("benefit_gate", "uncertainty_gate", False),
            ("always", "r16", False),
            ("mass_all", "r16", False),
            ("always", "lexical", False),
            ("always", "shuffled", False),
        ]
        for left, right, primary in pairs:
            diffs = defaultdict(list)
            for c in cohort:
                diffs[c["world_id"]].append(
                    D["quality"](c, index["test", c["id"], left]["grade"])
                    - D["quality"](c, index["test", c["id"], right]["grade"])
                )
            stats = paired(
                [statistics.mean(v) for v in diffs.values()], 0.9875 if primary else 0.95
            )
            contrasts.append(
                dict(
                    domain=domain,
                    left=left,
                    right=right,
                    primary=primary,
                    **stats,
                    noninferior_at_3pp=(stats["interval"][0] > -0.03)
                    if left == "benefit_gate" and right == "always"
                    else None,
                )
            )
        for arm in ("benefit_gate", "uncertainty_gate", "random_gate"):
            counts = dict(
                domain=domain,
                arm=arm,
                called=0,
                skipped=0,
                missed_benefits=0,
                called_harms=0,
                called_ties=0,
                called_benefits=0,
            )
            for c in cohort:
                call = index["test", c["id"], arm]["call_decision"]
                delta = D["quality"](c, index["test", c["id"], "always"]["grade"]) - D["quality"](
                    c, index["test", c["id"], "native"]["grade"]
                )
                counts["called" if call else "skipped"] += 1
                if call:
                    counts[
                        "called_benefits"
                        if delta > 0
                        else "called_harms"
                        if delta < 0
                        else "called_ties"
                    ] += 1
                elif delta > 0:
                    counts["missed_benefits"] += 1
            gate_diagnostics.append(counts)
    return dict(
        at=J["now"](),
        protocol=manifest["protocol"],
        audit_passed=True,
        outcomes=len(outputs),
        test_outcomes=len(data["schedule"]),
        development_outcomes=len(outputs) - len(data["schedule"]),
        complete_outcomes=len(outputs),
        verified_inputs=len(inputs),
        verified_final_tokens=sum(len(r["final"]["tokens"]) for r in outputs),
        model_forwards=sum(r["model_forwards"] for r in outputs),
        native_identity_pairs=native_pairs,
        pilot_identity_pairs=pilot_pairs,
        actual_api_attempts=len(attempts),
        successful_receipts=sum(r["status"] == "complete" for r in receipts.values()),
        unknown_calls=len(unknown),
        known_input_tokens=sum(settled.values()),
        charged_input_tokens=completion["charged_tokens"],
        selected=selected,
        summaries=summaries,
        contrasts=contrasts,
        gate_diagnostics=gate_diagnostics,
        artifact_hashes={
            p.name: D["sha"](p)
            for p in sorted(results.iterdir())
            if p.is_file() and p.suffix in (".json", ".jsonl")
        },
    )


def main():
    from transformers import AutoTokenizer

    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads((args.manifest / "manifest.json").read_text())
    tokenizer = AutoTokenizer.from_pretrained(
        manifest["model"],
        revision=manifest["revision"],
        local_files_only=True,
        trust_remote_code=False,
    )
    report = analyze(args.manifest, args.results, tokenizer)
    D["dump"](args.output, report)
    print(json.dumps({k: report[k] for k in ("audit_passed", "outcomes", "actual_api_attempts")}))


if __name__ == "__main__":
    main()
