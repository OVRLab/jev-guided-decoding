"""Reconstruct R19 inputs, scores, instruction maps, choices, tokens, work and statistics."""

import argparse
import hashlib
import json
import runpy
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
S = runpy.run_path(str(HERE / "study.py"))
D, P, J = (S[k] for k in ("D", "P", "J"))
OLD = runpy.run_path(str(HERE.parent / "boundary_attention/analyze.py"))
require, bootstrap = OLD["require"], OLD["bootstrap"]


def check_output(row, encoded, view, tokenizer, manifest):
    require(row["status"] == "complete", "Incomplete outcome requires explicit reporting")
    require(row["prompt_digest"] == encoded["prompt_digest"], "Prompt mismatch")
    observation = row["boundary"]["observation"]
    OLD["check_features"](observation)
    require(row["features"] == observation["features"], "Feature mismatch")
    require(
        row["benefit_features"] == P["vector"](row["features"], encoded, view),
        "Benefit feature mismatch",
    )
    called = P["decision"](row["gate"], row["features"], encoded, view)
    require(
        row["call_decision"] == called and row["logical_jev_calls"] == int(called),
        "Gate decision mismatch",
    )
    require(row["gate_requested"] == called, "Dispatch mismatch")
    mapped, action, scale = {}, "native", 0.0
    if row["provider_status"] == "complete":
        require(called and row["guided_path"], "Unexpected successful receipt")
        P["probability"](row["sufficient"])
        require(
            row["raw_scores"] == row["applied_scores"]
            and len(row["raw_scores"]) == len(view["sources"]),
            "Relevance binding mismatch",
        )
        for score in row["raw_scores"]:
            P["probability"](score)
        if row["mode"] != "relevance" and row["sufficient"] <= 0.35:
            keys = encoded["abstention_token_indices"]
            action, scale = "abstention", row["instruction_strength"]
        elif row["mode"] == "relevance" or (row["mode"] == "dual" and row["sufficient"] >= 0.65):
            keep = [v > 0.65 for v in row["raw_scores"]]
            keys = (
                [
                    k
                    for yes, span in zip(keep, encoded["span_token_indices"], strict=True)
                    if yes
                    for k in span
                ]
                if any(keep) and not all(keep)
                else []
            )
            action, scale = "relevance", row["policy"]["strength"]
        else:
            keys = []
        if keys:
            for layer, head in row["policy"]["heads"]:
                mapped.setdefault(str(layer), {})[str(head)] = {str(k): scale for k in keys}
    else:
        require(
            not row["guided_path"] and row["raw_scores"] is None and row["sufficient"] is None,
            "Failure/unasked became a judgment",
        )
        require(
            row["provider_status"] == ("failed_fallback" if called else "unasked"),
            "Fallback mismatch",
        )
    require(json.loads(json.dumps(row["applied_maps"])) == mapped, "Attention map mismatch")
    require(
        row["intervention_action"] == action and row["intervention_used"] == bool(mapped),
        "Intervention mismatch",
    )
    final = row["final"]
    ids, tokens = final["token_ids"], final["tokens"]
    n, layers = len(encoded["input_ids"]), manifest["num_layers"]
    require(
        0 < len(ids) <= 32 and ids == [t["token_id"] for t in tokens], "Token identity mismatch"
    )
    require(final["input_and_output_ids"] == encoded["input_ids"] + ids, "Prefix substitution")
    require(
        tokenizer.decode(ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
        == row["text"]
        == final["text"],
        "Decoded text mismatch",
    )
    require(
        row["prefills"] == 1 and row["discarded_tokens"] == 0 and row["pilot"] is None,
        "Repeated prefill/pilot",
    )
    require(row["model_forwards"] == final["model_forwards"] == len(ids), "Forward mismatch")
    require(
        final["processed_tokens"] == n + len(ids) - 1 and final["prompt_tokens"] == n,
        "Work mismatch",
    )
    require(
        row["layer_calls"] == [len(ids)] * layers
        and row["layer_token_counts"] == [n + len(ids) - 1] * layers,
        "Layer work mismatch",
    )
    for i, t in enumerate(tokens):
        OLD["check_token"](t)
        require(t["cache_lengths"] == [n + i] * layers, "Cache mismatch")
        require(
            t["strength"] == scale
            and t["active_heads"] == sum(len(v) for v in mapped.values())
            and t["hook_calls"] == len(mapped),
            "Token intervention mismatch",
        )
    require(final["hook_calls"] == len(mapped) * len(ids), "Hook count mismatch")
    eos = manifest["eos_ids"]
    require(not any(t in eos for t in ids[:-1]), "Continued after EOS")
    ended = ids[-1] in eos
    require(
        final["finish_reason"] == ("eos" if ended else "token_limit") and (ended or len(ids) == 32),
        "Termination mismatch",
    )
    b = row["boundary"]
    require(
        b["layer"] == manifest["boundary"]
        and b["observer_layer"] == manifest["boundary"] - 1
        and b["decisions"] == 1,
        "Boundary mismatch",
    )
    require(
        b["lower_cache_lengths"] == [n] * manifest["boundary"]
        and b["upper_cache_lengths"] == [0] * (layers - manifest["boundary"])
        and b["lower_cache_unchanged_during_wait"],
        "Boundary cache changed",
    )


def audit(folder, results):
    from transformers import AutoTokenizer

    R = runpy.run_path(str(HERE / "runtime.py"))
    manifest = json.loads((folder / "manifest.json").read_text())
    require(manifest["sources"] == S["source_hashes"](), "Source freeze mismatch")
    require(
        all(D["sha"](folder / n) == v for n, v in manifest["datasets"].items()),
        "Data freeze mismatch",
    )
    require(
        json.loads((results / "freeze.json").read_text()) == manifest, "Execution freeze mismatch"
    )
    tokenizer = AutoTokenizer.from_pretrained(
        manifest["model"],
        revision=manifest["revision"],
        local_files_only=True,
        trust_remote_code=False,
    )
    data = {
        s: json.loads((folder / f"{s}.json").read_text())
        for s in ("fit", "calibration", "test", "schedule")
    }
    cases = {c["id"]: c for stage in ("fit", "calibration", "test") for c in data[stage]}
    inputs = J["rows"](results / "inputs.jsonl")
    require(len(inputs) == len(cases) == len({r["id"] for r in inputs}), "Input count mismatch")
    encoded = {}
    for row in inputs:
        expected = dict(id=row["id"], **R["encode"](tokenizer, D["public_view"](cases[row["id"]])))
        require(row == json.loads(json.dumps(expected)), "Prompt/source identity mismatch")
        encoded[row["id"]] = row
    receipts, dispatch = {}, {}
    for row in J["rows"](results / "receipts.jsonl"):
        key = hashlib.sha256(json.dumps(row["payload"], sort_keys=True).encode()).hexdigest()
        require(key == row["key"], "Receipt key mismatch")
        target = dispatch if row["status"] == "started" else receipts
        require(key not in target, "Duplicate provider record")
        target[key] = row
    require(set(receipts) == set(dispatch), "Unaccounted provider attempt")
    for key, r in receipts.items():
        require(r["reservation"] == dispatch[key]["reservation"], "Reservation changed")
        if r["status"] == "complete":
            raw = r["raw_response"]
            require(
                raw["model"] == r["model"] == manifest["jev_model"] and r["attempts"] == 1,
                "Provider version/attempt mismatch",
            )
            require(raw["usage"]["input_tokens"] == r["input_tokens"], "Usage mismatch")
            require(
                [raw["answers"][f"relevance_{i}"]["noul"] for i in range(len(r["scores"]))]
                == r["scores"]
                and raw["answers"]["sufficient"]["noul"] == r["sufficient"],
                "Raw judgment mismatch",
            )
    selected = json.loads((results / "selected.json").read_text())
    freeze = json.loads((results / "test-freeze.json").read_text())
    require(
        freeze["selected_sha256"] == D["sha"](results / "selected.json")
        and freeze["sources"] == manifest["sources"]
        and freeze["schedule_sha256"] == manifest["datasets"]["schedule.json"],
        "Selection freeze mismatch",
    )
    rows = J["rows"](results / "outputs.jsonl")
    starts = J["rows"](results / "starts.jsonl")
    expected_jobs = {
        f"{s}/{c['id']}/{a}" for s in ("fit", "calibration") for c in data[s] for a in S["DEV_ARMS"]
    } | {f"test/{j['case_id']}/{j['arm']}" for j in data["schedule"]}
    require(len(rows) == len(starts) == len(expected_jobs) == 6096, "Incomplete schedule")
    require(
        {r["job"] for r in rows} == {r["job"] for r in starts} == expected_jobs,
        "Job identity mismatch",
    )
    start_lookup = {r["job"]: r for r in starts}
    lookup = {}
    for row in rows:
        c = cases[row["case_id"]]
        gate, mode, strength = S["configuration"](
            row["arm"], selected if row["stage"] == "test" else None
        )
        require(
            row["policy"] == manifest["treatment"]
            and row["requested_gate"] == row["gate"] == gate
            and row["mode"] == mode
            and row["instruction_strength"] == strength,
            "Frozen configuration mismatch",
        )
        require(
            row["domain"] == D["domain"](c)
            and row["world_id"] == c["world_id"]
            and row["stage"] == c["split"],
            "Case metadata mismatch",
        )
        require(
            all(row.get(k) == v for k, v in start_lookup[row["job"]]["metadata"].items()),
            "Started metadata changed",
        )
        check_output(row, encoded[c["id"]], D["public_view"](c), tokenizer, manifest)
        require(row["grade"] == D["grade"](c, row["text"]), "Grading mismatch")
        events = row["forward_events"]
        require(
            len(events) == row["model_forwards"]
            and [e["query_tokens"] for e in events]
            == [len(encoded[c["id"]]["input_ids"])] + [1] * (len(events) - 1),
            "Measured work mismatch",
        )
        if row["stage"] == "test":
            require(
                start_lookup[row["job"]]["at"] > freeze["at"] > selected["at"],
                "Test preceded freeze",
            )
        if row["receipt_key"]:
            receipt = receipts[row["receipt_key"]]
            require(
                receipt["payload"]
                == S["S"]["payload_for"](D["public_view"](c), manifest["jev_model"]),
                "Scorer input/reference leakage",
            )
            require(
                (row["provider_status"] == "complete") == (receipt["status"] == "complete"),
                "Receipt status mismatch",
            )
            if receipt["status"] == "complete":
                require(
                    row["raw_scores"] == receipt["scores"]
                    and row["sufficient"] == receipt["sufficient"],
                    "Applied receipt mismatch",
                )
        else:
            require(not row["logical_jev_calls"], "Unbound request")
        require(row["physical_jev_attempts"] in (0, 1), "Attempt count mismatch")
        lookup[row["stage"], c["id"], row["arm"]] = row
    development = {}
    for stage in ("fit", "calibration"):
        values = []
        for c in data[stage]:
            out = {a: lookup[stage, c["id"], a] for a in S["DEV_ARMS"]}
            require(
                all(r["features"] == out["native"]["features"] for r in out.values()),
                "Development feature contamination",
            )
            values.append(
                dict(
                    case_id=c["id"],
                    domain=D["domain"](c),
                    x=out["native"]["benefit_features"],
                    **{a: D["quality"](c, r["grade"]) for a, r in out.items()},
                )
            )
        development[stage] = values
    require(selected["development"] == development, "Development selection data mismatch")
    regenerated = P["select"](development["fit"], development["calibration"])
    # BLAS implementations may differ in last-bit coefficients, so compare numerically.
    import numpy as np

    def same(a, b):
        if isinstance(a, dict):
            return isinstance(b, dict) and set(a) == set(b) and all(same(a[k], b[k]) for k in a)
        if isinstance(a, list):
            return (
                isinstance(b, list)
                and len(a) == len(b)
                and all(same(x, y) for x, y in zip(a, b, strict=True))
            )
        if type(a) is float:
            return bool(np.isclose(a, b, atol=1e-8, rtol=1e-8))
        return a == b

    require(
        all(same(v, selected[k]) for k, v in regenerated.items()),
        "Benefit fitting/calibration mismatch",
    )
    branch_checks = 0
    for c in data["test"]:
        out = {a: lookup["test", c["id"], a] for a in S["ARMS"]}
        for a in ("benefit_gate", "random_gate", "r18_gate"):
            expected = out["dual"] if out[a]["call_decision"] else out["native"]
            require(
                out[a]["final"]["token_ids"] == expected["final"]["token_ids"],
                "Conditional branch identity mismatch",
            )
            branch_checks += 1
        require(
            out["benefit_gate"]["physical_jev_attempts"]
            == out["benefit_gate"]["logical_jev_calls"],
            "Gate-first physical call mismatch",
        )
    require(
        sum(r["physical_jev_attempts"] for r in rows) == len(receipts), "Physical calls mismatch"
    )
    ledger = J["rows"](results / "ledger.jsonl")
    reserves = [r["id"] for r in ledger if r["event"] == "reserve"]
    settled = {r["id"]: r["input_tokens"] for r in ledger if r["event"] == "settle"}
    maximum = {r["id"] for r in ledger if r["event"] == "charge_max_unknown"}
    require(
        len(reserves) == len(set(reserves)) == len(receipts)
        and set(reserves) == {r["reservation"] for r in receipts.values()}
        and set(settled).isdisjoint(maximum)
        and set(settled) | maximum == set(reserves),
        "Ledger reconciliation mismatch",
    )
    for receipt in receipts.values():
        require(
            settled.get(receipt["reservation"]) == receipt["input_tokens"]
            if receipt["status"] == "complete"
            else receipt["reservation"] in maximum,
            "Receipt charge mismatch",
        )
    completion = json.loads((results / "completion.json").read_text())
    require(
        completion["completed_schedule"]
        and completion["outputs"] == len(rows)
        and completion["receipts"] == len(receipts)
        and completion["weights_before"] == completion["weights_after"]
        and completion["charged_tokens"] == sum(settled.values()) + 65536 * len(maximum),
        "Completion/weight/charge mismatch",
    )
    domains = {}
    for domain in ("synthetic", "hotpot", "squad2"):
        cohort = [c for c in data["test"] if D["domain"](c) == domain]
        outputs = {a: [lookup["test", c["id"], a] for c in cohort] for a in S["ARMS"]}
        qualities = {
            a: [D["quality"](c, r["grade"]) for c, r in zip(cohort, out, strict=True)]
            for a, out in outputs.items()
        }
        arms = {}
        for a, out in outputs.items():
            arms[a] = dict(
                quality=statistics.mean(qualities[a]),
                calls=sum(r["logical_jev_calls"] for r in out),
                interventions=sum(r["intervention_used"] for r in out),
                actions={
                    act: sum(r["intervention_action"] == act for r in out)
                    for act in ("native", "relevance", "abstention")
                },
                mean_seconds=statistics.mean(r["estimated_uncached_wall_seconds"] for r in out),
                tokens=sum(len(r["final"]["token_ids"]) for r in out),
                prefills=sum(r["prefills"] for r in out),
                abstentions=sum(r["grade"].get("abstained", False) for r in out),
                token_caps=sum(r["final"]["finish_reason"] == "token_limit" for r in out),
                subgroups={},
            )
            for missing in (False, True):
                indices = [i for i, c in enumerate(cohort) if c["missing"] == missing]
                arms[a]["subgroups"]["missing" if missing else "answerable"] = dict(
                    count=len(indices),
                    quality=statistics.mean(qualities[a][i] for i in indices) if indices else None,
                )
            if domain == "squad2":
                arms[a]["raw_f1"] = statistics.mean(r["grade"]["raw_f1"] for r in out)
                arms[a]["raw_em"] = statistics.mean(r["grade"]["raw_em"] for r in out)
        primary = dict(
            sufficiency=bootstrap(
                cohort,
                qualities["dual"],
                qualities["relevance"],
                manifest["primary_interval"],
                19001,
            ),
            routing=bootstrap(
                cohort,
                qualities["dual"],
                qualities["native"],
                manifest["primary_interval"],
                19003,
                calls=[r["logical_jev_calls"] for r in outputs["benefit_gate"]],
            ),
        )
        secondary = {
            f"{a}_minus_{b}": bootstrap(cohort, qualities[a], qualities[b], 0.95, 19101)
            for a, b in [
                ("relevance", "native"),
                ("dual", "native"),
                ("sufficiency", "native"),
                ("benefit_gate", "native"),
                ("benefit_gate", "dual"),
                ("benefit_gate", "r18_gate"),
            ]
        }
        suff = [
            receipts[r["receipt_key"]]
            for r in outputs["dual"]
            if r["receipt_key"] and receipts[r["receipt_key"]]["status"] == "complete"
        ]
        provider_suff = dict(
            count=len(suff),
            mean_probability=statistics.mean(r["sufficient"] for r in suff) if suff else None,
            correct_at_half=sum(
                (r["sufficient"] >= 0.5) == (not c["missing"])
                for c, r in zip(
                    cohort, [receipts[row["receipt_key"]] for row in outputs["dual"]], strict=True
                )
                if r["status"] == "complete"
            ),
        )
        domains[domain] = dict(
            count=len(cohort),
            arms=arms,
            primary=primary,
            secondary=secondary,
            sufficiency_classification=provider_suff,
        )
    return dict(
        at=J["now"](),
        protocol=manifest["protocol"],
        outcomes=len(rows),
        test_outcomes=len(data["schedule"]),
        inputs=len(cases),
        final_tokens=sum(len(r["final"]["token_ids"]) for r in rows),
        branch_identity_checks=branch_checks,
        receipts=len(receipts),
        provider_failures=len(maximum),
        known_input_tokens=sum(settled.values()),
        charged_tokens=completion["charged_tokens"],
        selected={k: v for k, v in selected.items() if k not in ("development", "candidates")},
        domains=domains,
        weights_unchanged=True,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.manifest, args.results)
    D["dump"](args.output, result)
    print(
        json.dumps({k: v for k, v in result.items() if k not in ("domains", "selected")}, indent=2)
    )


if __name__ == "__main__":
    main()
