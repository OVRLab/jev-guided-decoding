"""Independent R18 source/input/token/feature/dispatch/work reconstruction and statistics."""

import argparse
import hashlib
import json
import math
import random
import runpy
import statistics
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
D = runpy.run_path(str(HERE / "data.py"))
P = runpy.run_path(str(HERE / "policies.py"))
S = runpy.run_path(str(HERE / "study.py"))
J = S["J"]
OLD = runpy.run_path(str(HERE.parent / "selective_attention/analyze.py"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_features(observation):
    require(observation["query_rows_computed"] == 1, "Feature query count mismatch")
    observed = observation["features"]
    expected = P["F"]["reconstruct"](observation["head_source_mass"])
    require(set(observed) == set(expected), "Feature names mismatch")
    require(
        all(type(v) in (int, float) and math.isfinite(v) for v in observed.values()),
        "Invalid recorded feature type",
    )
    require(
        all(abs(observed[k] - v) <= 1e-12 for k, v in expected.items()),
        "Feature reconstruction mismatch",
    )


def check_token(t):
    require(t["token_id"] == t["argmax_id"] == t["top_ids"][0], "Non-generator token")
    require(
        "allowed_ids" not in t and t["selected_logit"] == t["top_logits"][0],
        "Constrained or forged logit",
    )
    require(
        math.isfinite(t["entropy"]) and t["entropy"] >= 0 and 0 <= t["probability"] <= 1,
        "Nonfinite token statistics",
    )


def check_output(row, encoded, tokenizer, manifest):
    require(row["status"] == "complete", "Incomplete outcome must be accounted for explicitly")
    require(row["prompt_digest"] == encoded["prompt_digest"], "Prompt binding mismatch")
    n = len(encoded["input_ids"])
    layers, boundary = manifest["num_layers"], manifest["boundary"]
    for name in ("final", "pilot"):
        output = row[name]
        if output is None:
            continue
        ids, tokens = output["token_ids"], output["tokens"]
        require(0 < len(ids) <= (8 if name == "pilot" else 32), "Token budget mismatch")
        require(ids == [t["token_id"] for t in tokens], "Token record mismatch")
        require(output["input_and_output_ids"] == encoded["input_ids"] + ids, "Prefix substitution")
        require(
            output["model_forwards"] == len(ids) and output["processed_tokens"] == n + len(ids) - 1,
            "Generation work mismatch",
        )
        require(
            tokenizer.decode(ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
            == output["text"],
            "Decoded text mismatch",
        )
        require(output["hook_calls"] == sum(t["hook_calls"] for t in tokens), "Hook count mismatch")
        for step, t in enumerate(tokens):
            check_token(t)
            guided = name == "final" and row["guided_path"]
            scale = row["policy"]["strength"] if guided else 0.0
            require(t["strength"] == scale, "Wrong treatment strength")
            mapped = [s > 0.65 for s in (row["applied_scores"] or [])] if guided else []
            active = bool(mapped) and any(mapped) and not all(mapped)
            heads = len(row["policy"]["heads"]) if active else 0
            active_layers = len({h[0] for h in row["policy"]["heads"]}) if active else 0
            require(
                (t["active_heads"], t["hook_calls"]) == (heads, active_layers),
                "Wrong treatment heads",
            )
            if row["arm"].startswith("boundary_"):
                require(
                    t["cache_lengths"] == [n + step] * layers, "Boundary cache lengths mismatch"
                )
        eos_ids = manifest.get("eos_ids", [tokenizer.eos_token_id])
        ended = ids[-1] in eos_ids
        require(not any(t in eos_ids for t in ids[:-1]), "Continued after EOS")
        require(
            output["finish_reason"] == ("eos" if ended else "token_limit"),
            "EOS termination mismatch",
        )
        if name == "final" and not ended:
            require(len(ids) == 32, "Premature final token limit")
        require(output["prompt_tokens"] == n, "Prompt token count mismatch")
    require(row["text"] == row["final"]["text"], "Final provenance mismatch")
    discarded = len(row["pilot"]["tokens"]) if row["pilot"] and not row["pilot_reused"] else 0
    require(row["discarded_tokens"] == discarded, "Discarded pilot count mismatch")
    if row["pilot_reused"]:
        require(
            row["final"]["token_ids"][: len(row["pilot"]["token_ids"])]
            == row["pilot"]["token_ids"],
            "Retained pilot changed",
        )
    forwards = len(row["final"]["token_ids"]) + discarded
    processed = n + len(row["final"]["token_ids"]) - 1 + (n + discarded - 1 if discarded else 0)
    require(
        row["model_forwards"] == forwards == len(row["forward_events"]),
        "Measured forward count mismatch",
    )
    require(
        row["layer_calls"] == [forwards] * layers
        and row["layer_token_counts"] == [processed] * layers,
        "Measured layer work mismatch",
    )
    require(row["prefills"] == 1 + bool(discarded), "Repeated prefill mismatch")
    require(
        sum(e["query_tokens"] for e in row["forward_events"]) == processed,
        "Processed input-token work mismatch",
    )
    require(row["logical_jev_calls"] in (0, 1), "More than one logical call")
    require((row["receipt_key"] is None) == (row["logical_jev_calls"] == 0), "Hidden provider call")
    require(row["gate_requested"] == bool(row["logical_jev_calls"]), "Call decision mismatch")
    if row["arm"].startswith("boundary_"):
        record = row["boundary"]
        require(row["pilot"] is None and discarded == 0, "Boundary created pilot")
        require(
            record["decisions"] == 1
            and record["layer"] == boundary
            and record["observer_layer"] == boundary - 1,
            "Wrong decision boundary",
        )
        require(
            record["lower_cache_lengths"] == [n] * boundary
            and record["upper_cache_lengths"] == [0] * (layers - boundary),
            "Boundary cache order mismatch",
        )
        require(
            record["layer_calls_before"] == [1] * boundary + [0] * (layers - boundary)
            and record["lower_cache_unchanged_during_wait"],
            "Lower layers were recomputed or changed",
        )
        require(record["observation"]["key_length"] == n, "Feature key count mismatch")
        check_features(record["observation"])
        require(row["features"] == record["observation"]["features"], "Detached gate features")
        decision = P["decision"](row["gate"], row["features"], row["case_id"])
        require(
            decision == row["call_decision"] == row["gate_requested"],
            "Boundary gate decision mismatch",
        )
    elif row["gate"]:
        pilot = row["pilot"]
        require(pilot is not None, "Pilot gate missing observation")
        # Feature reconstruction against original public evidence occurs in audit().
        require(
            P["decision"](row["gate"], row["features"], row["case_id"]) == row["call_decision"],
            "Pilot gate decision mismatch",
        )


def mean(rows, key):
    return statistics.mean(r[key] for r in rows)


def bootstrap(cases, left, right, level, seed, *, calls=None):
    import numpy as np

    groups = defaultdict(list)
    for i, c in enumerate(cases):
        groups[c.get("cluster_id", c["world_id"])].append(i)
    indices = list(groups.values())
    counts = np.array([len(g) for g in indices], dtype=float)
    a = np.array([sum(left[i] for i in g) for g in indices])
    b = np.array([sum(right[i] for i in g) for g in indices])
    rng = np.random.default_rng(seed)
    selected = rng.integers(len(indices), size=(10000, len(indices)))
    sizes = counts[selected].sum(1)
    if calls is None:
        draws = (a[selected].sum(1) - b[selected].sum(1)) / sizes
        point = (sum(left) - sum(right)) / len(cases)
    else:
        # Routing value: E[g * treatment_gain] - E[g] E[treatment_gain].
        gain = np.asarray(left) - np.asarray(right)
        cross = np.array([sum(gain[i] * calls[i] for i in g) for g in indices])
        call_sums = np.array([sum(calls[i] for i in g) for g in indices])
        delta = a - b
        draws = (
            cross[selected].sum(1) / sizes
            - call_sums[selected].sum(1) * delta[selected].sum(1) / sizes**2
        )
        point = float(
            sum(gain * np.asarray(calls)) / len(cases) - sum(calls) * sum(gain) / len(cases) ** 2
        )
    low, high = np.quantile(draws, [(1 - level) / 2, 1 - (1 - level) / 2])
    return dict(
        difference=point,
        interval=[float(low), float(high)],
        interval_level=level,
        clusters=len(indices),
    )


def audit(folder, results, *, tokenizer=None):
    from transformers import AutoTokenizer

    R = runpy.run_path(str(HERE / "runtime.py"))
    manifest = json.loads((folder / "manifest.json").read_text())
    require(manifest["sources"] == S["source_hashes"](), "Scientific source freeze mismatch")
    require(
        all(D["sha"](folder / n) == v for n, v in manifest["datasets"].items()),
        "Dataset freeze mismatch",
    )
    require(
        json.loads((results / "freeze.json").read_text()) == manifest, "Executed freeze mismatch"
    )
    tokenizer = tokenizer or AutoTokenizer.from_pretrained(
        manifest["model"],
        revision=manifest["revision"],
        local_files_only=True,
        trust_remote_code=False,
    )
    data = {
        k: json.loads((folder / f"{k}.json").read_text())
        for k in ("development", "test", "schedule")
    }
    cases = {c["id"]: c for c in data["development"] + data["test"]}
    inputs = J["rows"](results / "inputs.jsonl")
    require(len(inputs) == len(cases) == len({r["id"] for r in inputs}), "Missing/duplicate input")
    encoded = {}
    for row in inputs:
        expected = {"id": row["id"], **R["encode"](tokenizer, D["public_view"](cases[row["id"]]))}
        require(row == json.loads(json.dumps(expected)), "Source text/input identity mismatch")
        encoded[row["id"]] = row
    for c in cases.values():
        if D["domain"](c) == "synthetic":
            require(
                D["OLD"]["OLD"]["visible_reference"](c) == c["reference"],
                "Visible authored truth mismatch",
            )
    receipts, starts_receipts = {}, {}
    for receipt in J["rows"](results / "receipts.jsonl"):
        key = hashlib.sha256(json.dumps(receipt["payload"], sort_keys=True).encode()).hexdigest()
        require(key == receipt["key"], "Receipt content hash mismatch")
        target = starts_receipts if receipt["status"] == "started" else receipts
        require(key not in target, "Duplicate receipt dispatch/completion")
        target[key] = receipt
    require(set(receipts) == set(starts_receipts), "Unaccounted provider attempt")
    for key, receipt in receipts.items():
        require(
            receipt["reservation"] == starts_receipts[key]["reservation"],
            "Receipt reservation changed",
        )
        if receipt["status"] == "complete":
            raw = receipt["raw_response"]
            require(
                raw["model"] == manifest["jev_model"]
                and raw["usage"]["input_tokens"] == receipt["input_tokens"],
                "Raw provider model/usage mismatch",
            )
            require(
                [raw["answers"][f"relevance_{i}"]["noul"] for i in range(len(receipt["scores"]))]
                == receipt["scores"],
                "Raw provider scores mismatch",
            )
    outputs, starts = J["rows"](results / "outputs.jsonl"), J["rows"](results / "starts.jsonl")
    expected_jobs = {
        f"development/{c['id']}/{a}"
        for c in data["development"]
        for a in ("boundary_never", "boundary_always")
    } | {f"test/{j['case_id']}/{j['arm']}" for j in data["schedule"]}
    require(len(outputs) == len(starts) == len(expected_jobs) == 9376, "Incomplete schedule")
    require(
        {r["job"] for r in outputs} == {r["job"] for r in starts} == expected_jobs,
        "Job identity mismatch",
    )
    start_lookup = {r["job"]: r for r in starts}
    selected = json.loads((results / "selected.json").read_text())
    freeze = json.loads((results / "test-freeze.json").read_text())
    require(
        freeze["selected_sha256"] == D["sha"](results / "selected.json")
        and freeze["sources"] == manifest["sources"]
        and freeze["schedule_sha256"] == manifest["datasets"]["schedule.json"],
        "Selected policy freeze mismatch",
    )
    lookup = {}
    physical = 0
    for row in outputs:
        c = cases[row["case_id"]]
        require(
            row["domain"] == D["domain"](c) and row["world_id"] == c["world_id"],
            "Output case identity mismatch",
        )
        require(row["grade"] == D["grade"](c, row["text"]), "Grade mismatch")
        require(
            row["policy"] == (None if row["arm"] == "native" else manifest["treatment"]),
            "Treatment mismatch",
        )
        wanted_gate = S["gate_for"](row["arm"], selected)
        require(row["requested_gate"] == row["gate"] == wanted_gate, "Gate freeze mismatch")
        require(
            all(row.get(k) == v for k, v in start_lookup[row["job"]]["metadata"].items()),
            "Job metadata mismatch",
        )
        check_output(row, encoded[c["id"]], tokenizer, manifest)
        if row["stage"] == "test":
            require(
                start_lookup[row["job"]]["at"] > selected["at"]
                and start_lookup[row["job"]]["at"] > freeze["at"],
                "Test began before selection freeze",
            )
        if row["arm"] == "pilot_gate":
            pilot = row["pilot"]
            observed = S["OLD"]["P"]["features"](
                pilot["tokens"], pilot["text"], D["public_view"](c)
            )
            require(observed == row["features"], "Pilot feature reconstruction mismatch")
        if row["receipt_key"]:
            receipt = receipts[row["receipt_key"]]
            require(
                receipt["payload"]
                == S["OLD"]["S"]["payload_for"](D["public_view"](c), manifest["jev_model"]),
                "Scorer reference/input leakage",
            )
            if receipt["status"] == "complete":
                require(
                    receipt["model"] == manifest["jev_model"]
                    and receipt["attempts"] == 1
                    and row["raw_scores"] == receipt["scores"],
                    "Provider receipt mismatch",
                )
                expected_scores = list(receipt["scores"])
                if row["arm"] == "shuffled":
                    random.Random("r17-shuffle/" + c["id"]).shuffle(expected_scores)
                require(
                    expected_scores == row["applied_scores"] and row["guided_path"],
                    "Applied relevance mismatch",
                )
            else:
                require(
                    row["provider_status"] == "failed_fallback" and not row["guided_path"],
                    "Failed call did not fall back",
                )
        elif row["arm"] == "lexical":
            require(
                row["applied_scores"] == D["OLD"]["OLD"]["lexical"](D["public_view"](c)),
                "Lexical control mismatch",
            )
        else:
            require(not row["guided_path"], "Unasked provider guided generation")
        require(row["physical_jev_attempts"] in (0, 1), "Physical dispatch cap")
        physical += row["physical_jev_attempts"]
        lookup[row["stage"], row["case_id"], row["arm"]] = row
    require(physical == len(receipts), "Physical calls do not reconcile")
    dev_rows = []
    for c in data["development"]:
        native, guided = (
            lookup["development", c["id"], a] for a in ("boundary_never", "boundary_always")
        )
        require(native["features"] == guided["features"], "Development feature leakage")
        tokens = native["final"]["tokens"][:8]
        text = tokenizer.decode(
            [t["token_id"] for t in tokens],
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )
        dev_rows.append(
            dict(
                case_id=c["id"],
                domain=D["domain"](c),
                features=native["features"],
                pilot_features=S["OLD"]["P"]["features"](tokens, text, D["public_view"](c)),
                native_quality=D["quality"](c, native["grade"]),
                guided_quality=D["quality"](c, guided["grade"]),
            )
        )
    require(dev_rows == selected["development"], "Development selection data mismatch")
    require(P["fit"](dev_rows) == selected["boundary"], "Boundary selection mismatch")
    require(
        P["fit"](
            [{**r, "features": r["pilot_features"]} for r in dev_rows], names=P["PILOT_FEATURES"]
        )
        == selected["pilot"],
        "Pilot selection mismatch",
    )
    actual_test_order = [
        dict(case_id=r["metadata"]["case_id"], arm=r["metadata"]["arm"])
        for r in starts
        if r["metadata"]["stage"] == "test"
    ]
    require(
        actual_test_order == data["schedule"] == S["schedule"](data["test"]),
        "Gate-first execution order mismatch",
    )
    identity_pairs = 0
    for c in data["test"]:
        rows = {a: lookup["test", c["id"], a] for a in S["ARMS"]}
        require(
            rows["boundary_gate"]["physical_jev_attempts"]
            == rows["boundary_gate"]["logical_jev_calls"],
            "Primary gate did not execute before receipt reuse",
        )
        for arm in (
            "boundary_never",
            "boundary_always",
            "boundary_gate",
            "boundary_random",
            "pilot_gate",
        ):
            row = rows[arm]
            expected = rows["always"] if row["guided_path"] else rows["native"]
            require(
                row["final"]["token_ids"] == expected["final"]["token_ids"],
                "Native/guided branch identity mismatch",
            )
            identity_pairs += 1
            if arm.startswith("boundary_"):
                require(
                    row["features"] == rows["boundary_never"]["features"],
                    "Intervention affected early features",
                )
    ledger = J["rows"](results / "ledger.jsonl")
    require(
        ledger[0]
        == dict(
            event="terms",
            max_usd=str(manifest["max_api_usd"]),
            usd_per_million="0.05",
            request_token_ceiling=65536,
        ),
        "Ledger terms mismatch",
    )
    completion = json.loads((results / "completion.json").read_text())
    loads = J["rows"](results / "loads.jsonl")
    require(
        completion["weights_before"] == completion["weights_after"] == loads[0]["weights_before"],
        "Model weights changed",
    )
    require(
        completion["completed_schedule"]
        and completion["outputs"] == len(outputs)
        and completion["receipts"] == len(receipts),
        "Completion receipt mismatch",
    )
    # Reuse the durable budget's parser without writing to the original evidence.
    settlements = [r for r in ledger if r.get("event") == "settle"]
    reserves = [r["id"] for r in ledger if r["event"] == "reserve"]
    settled = {r["id"]: r["input_tokens"] for r in settlements}
    maximum = [r["id"] for r in ledger if r["event"] == "charge_max_unknown"]
    require(
        len(reserves) == len(set(reserves)) == len(receipts), "Reservation replay/count mismatch"
    )
    require(
        set(reserves)
        == {r["reservation"] for r in starts_receipts.values()}
        == set(settled) | set(maximum)
        and not set(settled) & set(maximum),
        "Ledger reservation reconciliation mismatch",
    )
    require(
        len(settled) == len(settlements) and len(set(maximum)) == len(maximum),
        "Repeated settlement",
    )
    for r in receipts.values():
        require(
            settled.get(r["reservation"]) == r.get("input_tokens")
            if r["status"] == "complete"
            else r["reservation"] in maximum,
            "Receipt/ledger usage mismatch",
        )
    require(len(loads) == 1 and not loads[0]["dirty"], "Dirty or repeated model load")
    known = sum(r.get("input_tokens", 0) for r in receipts.values() if r["status"] == "complete")
    unknown = sum(r["status"] != "complete" for r in receipts.values())
    require(
        completion["charged_tokens"] == known + unknown * 65536,
        "Charged token reconciliation mismatch",
    )
    require(
        json.loads((results / "admission.json").read_text())["passed"], "Failed numerical admission"
    )
    summaries, contrasts, routing = [], [], []
    for domain in ("synthetic", "hotpot", "squad2"):
        cohort = [c for c in data["test"] if D["domain"](c) == domain]
        by_arm = {a: [lookup["test", c["id"], a] for c in cohort] for a in S["ARMS"]}
        values = {
            a: [D["quality"](c, r["grade"]) for c, r in zip(cohort, rows, strict=True)]
            for a, rows in by_arm.items()
        }
        for arm, rows in by_arm.items():

            def timing(key, rows=rows):
                v = sorted(r[key] for r in rows)
                return dict(
                    mean=statistics.mean(v),
                    median=statistics.median(v),
                    p95=v[math.ceil(0.95 * len(v)) - 1],
                )

            subgroups = {}
            for missing in (False, True):
                subgroup = [
                    (c, r) for c, r in zip(cohort, rows, strict=True) if c["missing"] == missing
                ]
                if subgroup:
                    subgroups[str(missing)] = dict(
                        cases=len(subgroup),
                        quality=statistics.mean(D["quality"](c, r["grade"]) for c, r in subgroup),
                    )
            summaries.append(
                dict(
                    domain=domain,
                    arm=arm,
                    cases=len(rows),
                    quality=statistics.mean(values[arm]),
                    em=statistics.mean(r["grade"]["correct"] for r in rows),
                    raw_f1=statistics.mean(
                        r["grade"].get("raw_f1", r["grade"]["f1"]) for r in rows
                    ),
                    call_fraction=mean(rows, "logical_jev_calls"),
                    physical_attempts=sum(r["physical_jev_attempts"] for r in rows),
                    model_forwards=sum(r["model_forwards"] for r in rows),
                    processed_tokens=sum(r["layer_token_counts"][0] for r in rows),
                    discarded_tokens=sum(r["discarded_tokens"] for r in rows),
                    prefills=sum(r["prefills"] for r in rows),
                    feature_seconds=statistics.mean(r.get("feature_seconds", 0) for r in rows),
                    timings={
                        k: timing(k)
                        for k in (
                            "model_seconds",
                            "estimated_uncached_wall_seconds",
                            "first_token_seconds",
                            "estimated_uncached_first_token_seconds",
                        )
                    },
                    peak_gpu_bytes=max((r["peak_gpu_bytes"] or 0) for r in rows),
                    terminations=dict(Counter(r["final"]["finish_reason"] for r in rows)),
                    abstentions=sum(
                        r["grade"].get("abstained", r["grade"].get("parsed") == "UNKNOWN")
                        for r in rows
                    ),
                    missing_subgroups=subgroups,
                )
            )
        for arm in ("boundary_gate", "pilot_gate", "boundary_random"):
            calls = [r["logical_jev_calls"] for r in by_arm[arm]]
            stats = bootstrap(
                cohort,
                values["always"],
                values["native"],
                manifest["primary_interval"] if arm == "boundary_gate" else 0.95,
                180922751,
                calls=calls,
            )
            expected_random = statistics.mean(values["native"]) + statistics.mean(calls) * (
                statistics.mean(values["always"]) - statistics.mean(values["native"])
            )
            routing.append(
                dict(
                    domain=domain,
                    arm=arm,
                    primary=arm == "boundary_gate",
                    quality=statistics.mean(values[arm]),
                    call_fraction=statistics.mean(calls),
                    expected_random_quality=expected_random,
                    **stats,
                )
            )
        for left, right in [
            ("always", "native"),
            ("boundary_gate", "native"),
            ("boundary_gate", "always"),
            ("boundary_gate", "pilot_gate"),
            ("boundary_gate", "boundary_random"),
            ("always", "lexical"),
            ("always", "shuffled"),
        ]:
            contrasts.append(
                dict(
                    domain=domain,
                    left=left,
                    right=right,
                    primary=False,
                    **bootstrap(cohort, values[left], values[right], 0.95, 180922757),
                )
            )
    return dict(
        at=J["now"](),
        audit_passed=True,
        outcomes=len(outputs),
        development_outcomes=520,
        test_outcomes=8856,
        exact_inputs=len(inputs),
        final_tokens=sum(len(r["final"]["token_ids"]) for r in outputs),
        model_forwards=sum(r["model_forwards"] for r in outputs),
        branch_identity_pairs=identity_pairs,
        paid_attempts=len(receipts),
        successful_receipts=len(receipts) - unknown,
        unknown_calls=unknown,
        known_input_tokens=known,
        charged_tokens=completion["charged_tokens"],
        weights_unchanged=True,
        source_freeze_verified=True,
        selected=selected,
        summaries=summaries,
        contrasts=contrasts,
        routing=routing,
        ledger_settlements=len(settlements),
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--results", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    D["dump"](args.output, audit(args.manifest, args.results))
    print("AUDIT PASSED")


if __name__ == "__main__":
    main()
