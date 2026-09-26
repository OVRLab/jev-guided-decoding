"""Independent artifact reconstruction, token audit and world-clustered statistics."""

import argparse
import hashlib
import json
import math
import random
import runpy
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
D = runpy.run_path(str(HERE / "data.py"))
J = runpy.run_path(str(HERE / "journal.py"))
P = runpy.run_path(str(HERE / "policies.py"))


def check_tokens(row, encoded, tokenizer=None):
    if row["status"] != "complete":
        return
    sequence = list(encoded["input_ids"])
    events = sorted(row["phases"] + row["framing"], key=lambda p: p["start"])
    count = 0
    for event in events:
        if event["start"] != len(sequence) or not event["token_ids"]:
            raise ValueError("Noncontiguous output/framing")
        sequence.extend(event["token_ids"])
        if "phase" not in event:
            continue
        records = event["tokens"]
        if len(records) != len(event["token_ids"]):
            raise ValueError("Missing token decision")
        count += len(records)
        for selected, decision in zip(event["token_ids"], records, strict=True):
            if selected != decision["token_id"]:
                raise ValueError("Token decision mismatch")
            if row["contract"] == "constrained":
                labels, logits = decision["allowed_ids"], decision["label_logits"]
                if selected != labels[max(range(len(logits)), key=logits.__getitem__)]:
                    raise ValueError("Constrained label is not Granite argmax")
            elif selected != decision["argmax_id"] or selected != decision["top_ids"][0]:
                raise ValueError("Unrestricted token is not Granite argmax")
        if tokenizer is not None:
            decoded = tokenizer.decode(
                event["token_ids"], skip_special_tokens=True, clean_up_tokenization_spaces=False
            )
            if decoded != event["text"]:
                raise ValueError("Generated text is not exact token decoding")
    if sequence != row["final_input_and_output_ids"]:
        raise ValueError("Full prefix/output mismatch")
    if count != row["generated_tokens"] or count != row["model_forwards"]:
        raise ValueError("Generated token/forward count mismatch")
    if row["processed_tokens"] != len(sequence) - 1:
        raise ValueError("Cached processed prefix mismatch")
    if row["phases"][-1]["phase"] != "final" or row["phases"][-1]["text"] != row["text"]:
        raise ValueError("Final text attribution mismatch")


def paired(differences, alpha=0.05, draws=10000):
    import numpy as np

    values = np.asarray(differences, dtype=float)
    rng = np.random.default_rng(160922211)
    boot = np.empty(draws)
    for start in range(0, draws, 500):
        take = min(500, draws - start)
        boot[start : start + take] = rng.choice(
            values, size=(take, len(values)), replace=True
        ).mean(1)
    return dict(
        difference=float(values.mean()),
        interval=np.quantile(boot, [alpha / 2, 1 - alpha / 2]).tolist(),
        level=1 - alpha,
        units=len(values),
        wins=int((values > 0).sum()),
        losses=int((values < 0).sum()),
        ties=int((values == 0).sum()),
    )


def analyze(manifest_folder, result_folder, *, tokenizer=None):
    R = runpy.run_path(str(HERE / "runtime.py")) if tokenizer is not None else None
    S = runpy.run_path(str(HERE / "scorer.py"))
    STUDY = runpy.run_path(str(HERE / "study.py"))
    manifest = json.loads((manifest_folder / "manifest.json").read_text())
    for filename, digest in manifest["datasets"].items():
        if D["sha"](manifest_folder / filename) != digest:
            raise ValueError("Frozen dataset mismatch")
    if json.loads((result_folder / "freeze.json").read_text()) != manifest:
        raise ValueError("Execution manifest mismatch")

    def read(name):
        return json.loads((manifest_folder / f"{name}.json").read_text())

    dev, test, hotpot = read("development"), read("test"), read("hotpot")
    all_cases = STUDY["all_cases"](test, hotpot)
    cases = {c["id"]: c for c in dev + all_cases}
    for case in dev + all_cases:
        if case["family"] != "hotpot" and D["visible_reference"](case) != case["reference"]:
            raise ValueError("Independent graph reference mismatch")
    inputs = {(r["id"], r["contract"]): r for r in J["rows"](result_folder / "inputs.jsonl")}
    if tokenizer:
        for (ident, contract), recorded in inputs.items():
            encoded = R["encode"](tokenizer, D["public_view"](cases[ident]), contract)
            if json.loads(json.dumps(encoded)) != {k: v for k, v in recorded.items() if k != "id"}:
                raise ValueError("Independent prompt reconstruction failed")
    outputs = J["rows"](result_folder / "outputs.jsonl")
    starts = J["rows"](result_folder / "starts.jsonl")
    if len({r["job"] for r in outputs}) != len(outputs):
        raise ValueError("Duplicate output")
    if {r["job"] for r in starts} != {r["job"] for r in outputs}:
        raise ValueError("Started operations not accounted for")
    start_index = {r["job"]: r["metadata"] for r in starts}
    receipt_rows = J["rows"](result_folder / "receipts.jsonl")
    receipts = {r["key"]: r for r in receipt_rows if r["status"] != "started"}
    attempts = [r for r in receipt_rows if r["status"] == "started"]
    if len({r["key"] for r in attempts}) != len(attempts) or len(attempts) != len(receipts):
        raise ValueError("Receipt attempt accounting failed")
    for key, receipt in receipts.items():
        if (
            hashlib.sha256(json.dumps(receipt["payload"], sort_keys=True).encode()).hexdigest()
            != key
        ):
            raise ValueError("Receipt payload digest mismatch")
        if receipt["status"] == "complete":
            raw = receipt["raw_response"]
            if (
                raw["model"] != manifest["jev_model"]
                or raw["usage"]["input_tokens"] != receipt["input_tokens"]
            ):
                raise ValueError("Receipt model/usage mismatch")
            if [
                raw["answers"][f"relevance_{i}"]["noul"] for i in range(len(receipt["scores"]))
            ] != receipt["scores"]:
                raise ValueError("Raw typed score mismatch")
    ledger = J["rows"](result_folder / "ledger.jsonl")
    reserves = {r["id"] for r in ledger if r["event"] == "reserve"}
    settle = {r["id"]: r["input_tokens"] for r in ledger if r["event"] == "settle"}
    unknown = {r["id"] for r in ledger if r["event"] == "charge_max_unknown"}
    if reserves != {r["reservation"] for r in attempts} or reserves != set(settle) | unknown:
        raise ValueError("Paid reservation accounting mismatch")
    verified_tokens = 0
    for row in outputs:
        if any(row.get(k) != value for k, value in start_index[row["job"]].items()):
            raise ValueError("Started/completed job metadata mismatch")
        case = cases[row["case_id"]]
        encoded = inputs[(case["id"], row["contract"])]
        check_tokens(row, encoded, tokenizer)
        if row["status"] == "complete":
            if D["grade"](case, row["text"], row["contract"]) != row["grade"]:
                raise ValueError("Independent answer grading mismatch")
            verified_tokens += row["generated_tokens"]
        for update in row.get("updates", []):
            if update["reasoning"] and tokenizer is not None:
                count = update["after_generated_tokens"]
                previous = []
                total = 0
                for phase in row.get("phases", []):
                    total += len(phase["token_ids"])
                    previous.append(phase)
                    if total == count:
                        break
                if total != count or not previous or not row.get("framing"):
                    raise ValueError("Dynamic score has no matching generated prefix")
                first = row["framing"][0]
                start = first["start"] + len(first["token_ids"])
                end = previous[-1]["start"] + len(previous[-1]["token_ids"])
                prefix = row["final_input_and_output_ids"][start:end]
                text = tokenizer.decode(
                    prefix, skip_special_tokens=True, clean_up_tokenization_spaces=False
                )
                if text != update["reasoning"]:
                    raise ValueError("Dynamic judgment used a different reasoning prefix")
            if update["receipt_key"] is not None:
                receipt = receipts[update["receipt_key"]]
                if receipt["status"] != "complete":
                    raise ValueError("Failed receipt used as relevance")
                expected = S["payload_for"](
                    D["public_view"](case), manifest["jev_model"], update["reasoning"]
                )
                if expected != receipt["payload"] or receipt["scores"] != update["raw_scores"]:
                    raise ValueError("Receipt does not bind to exact source and generated state")
            else:
                expected = D["lexical"](D["public_view"](case), update["reasoning"])
                if expected != update["raw_scores"]:
                    raise ValueError("Lexical control mismatch")
            applied = list(update["raw_scores"])
            if row["arm"].startswith("shuffled"):
                random.Random(f"r16-shuffle/{case['id']}/{update['reasoning']}").shuffle(applied)
            if applied != update["applied_scores"]:
                raise ValueError("Applied relevance mismatch")
        generated_before = 0
        for phase in row.get("phases", []):
            applicable = [
                u for u in row.get("updates", []) if u["after_generated_tokens"] <= generated_before
            ]
            maps = (
                P["token_maps"](
                    row["policy"], encoded["span_token_indices"], applicable[-1]["applied_scores"]
                )
                if applicable
                else {}
            )
            map_record = [
                {
                    "head": list(h),
                    "keys": len(b),
                    "maximum": max(b.values()),
                    "bias_sha256": hashlib.sha256(
                        json.dumps(sorted(b.items())).encode()
                    ).hexdigest(),
                }
                for h, b in maps.items()
            ]
            if map_record != phase["maps"]:
                raise ValueError("Attention mapping differs from recorded phase")
            generated_before += len(phase["token_ids"])
    planned = {(j["case_id"], j["contract"], j["arm"]) for j in read("schedule")}
    executed = {(r["case_id"], r["contract"], r["arm"]) for r in outputs if r["stage"] == "test"}
    if executed != planned:
        raise ValueError("Planned evaluation schedule not complete")
    selected = json.loads((result_folder / "selected.json").read_text())
    dev_index = defaultdict(list)
    for row in outputs:
        if row["stage"] == "development":
            dev_index[row["policy"]["id"]].append(row)
    rebuilt = {}
    for metric in selected["all_metrics"]:
        ident = metric["policy"]["id"]
        rows = dev_index[ident]
        if len(rows) != len(dev) or {r["case_id"] for r in rows} != {c["id"] for c in dev}:
            raise ValueError("Incomplete development policy")
        complete = [r for r in rows if r["status"] == "complete"]
        accuracy = sum(r.get("grade", {}).get("correct", 0) for r in rows) / len(dev)
        logprob = (
            sum(r["reference_logprob"] for r in complete) / len(complete) if complete else -1000
        )
        if (
            abs(accuracy - metric["accuracy"]) > 1e-12
            or abs(logprob - metric["mean_logprob"]) > 1e-10
        ):
            raise ValueError("Development metric mismatch")
        for r in complete:
            logits = r["phases"][0]["tokens"][0]["label_logits"]
            m = max(logits)
            target = [*D["COLORS"], "UNKNOWN"].index(cases[r["case_id"]]["reference"])
            independent_logprob = (
                logits[target] - m - math.log(sum(math.exp(x - m) for x in logits))
            )
            if abs(independent_logprob - r["reference_logprob"]) > 1e-10:
                raise ValueError("Reference log probability mismatch")
        rebuilt[ident] = metric

    def pick(policies):
        values = [rebuilt[p["id"]] for p in policies]
        return sorted(
            values,
            key=lambda m: (
                -m["accuracy"],
                -m["mean_logprob"],
                sum(m["policy"]["weights"]),
                m["policy"]["id"],
            ),
        )[0]["policy"]

    current = pick(P["diagnostic_policies"]())
    for i in range(12):
        options = []
        for level in P["LEVELS"]:
            weights = list(current["weights"])
            weights[i] = level
            options.append(P["changed"](current, weights=weights))
        current = pick(options)
    options = [
        P["changed"](current, mapping=m, threshold=t)
        for m, t in [
            ("threshold", 0.35),
            ("threshold", 0.5),
            ("threshold", 0.65),
            ("threshold", 0.8),
            ("soft", 0.5),
        ]
    ]
    if pick(options) != selected["selected"]["policy"]:
        raise ValueError("Development selection reconstruction failed")
    panels = defaultdict(list)
    for row in outputs:
        if row["stage"] == "test":
            panels[(row["family"], row["contract"])].append(row)
    summaries = {}
    for (family, contract), rows in panels.items():
        arms = sorted({r["arm"] for r in rows})
        units = sorted({r["world_id"] for r in rows})
        by_arm = {}
        for arm in arms:
            sub = [r for r in rows if r["arm"] == arm]

            def mean_metric(name, sub=sub):
                return sum(r.get("grade", {}).get(name, 0) for r in sub) / len(sub)

            groups = {}
            for name, condition in [("answerable", False), ("missing", True)]:
                subset = [r for r in sub if cases[r["case_id"]]["missing"] == condition]
                if subset:
                    groups[name] = dict(
                        n=len(subset),
                        accuracy=sum(r.get("grade", {}).get("correct", 0) for r in subset)
                        / len(subset),
                    )
            by_arm[arm] = dict(
                n=len(sub),
                complete=sum(r["status"] == "complete" for r in sub),
                accuracy=mean_metric("correct"),
                em=mean_metric("em"),
                f1=mean_metric("f1"),
                parsed=sum(r.get("grade", {}).get("parsed") is not None for r in sub),
                groups=groups,
                model_seconds=sum(r.get("model_seconds", 0) for r in sub),
                model_forwards=sum(r.get("model_forwards", 0) for r in sub),
                generated_tokens=sum(r.get("generated_tokens", 0) for r in sub),
                deployed_jev_seconds=sum(
                    sum(receipts[k]["seconds"] for k in set(r.get("receipt_keys", []))) for r in sub
                ),
                per_depth={
                    str(depth): {
                        "n": len(ss),
                        "accuracy": sum(x.get("grade", {}).get("correct", 0) for x in ss) / len(ss),
                    }
                    for depth in sorted({cases[r["case_id"]]["depth"] for r in sub})
                    if (ss := [r for r in sub if cases[r["case_id"]]["depth"] == depth])
                },
            )
        main = "dynamic" if contract == "staged" else "tuned"
        contrasts = {}
        for control in arms:
            if control == main:
                continue
            metric = "f1" if family == "hotpot" else "correct"
            confirmatory = (family, contract, main, control) in {
                ("original", "constrained", "tuned", "r15"),
                ("original", "staged", "dynamic", "tuned"),
                ("hotpot", "open_explicit", "tuned", "native"),
            }
            differences = []
            for world in units:

                def average(arm, rows=rows, world=world, metric=metric):
                    group = [r for r in rows if r["world_id"] == world and r["arm"] == arm]
                    return sum(r.get("grade", {}).get(metric, 0) for r in group) / len(group)

                differences.append(average(main) - average(control))
            contrasts[control] = {
                **paired(differences, 0.05 / 3 if confirmatory else 0.05),
                "metric": metric,
                "confirmatory": confirmatory,
            }
        summaries[f"{family}/{contract}"] = dict(arms=by_arm, main=main, contrasts=contrasts)
    test_index = {
        (r["case_id"], r["contract"], r["arm"]): r for r in outputs if r["stage"] == "test"
    }
    zero_pairs = 0
    for c in test:
        native = test_index[c["id"], "constrained", "native"]
        zero = test_index[c["id"], "constrained", "zero"]
        if native.get("phases") != zero.get("phases"):
            raise ValueError("Zero/native exact token/logit identity failed")
        zero_pairs += 1
    return dict(
        audit_passed=True,
        reconstructed_inputs=len(inputs),
        verified_generated_tokens=verified_tokens,
        outputs=len(outputs),
        statuses=dict(Counter(r["status"] for r in outputs)),
        model_forwards=sum(r.get("model_forwards", 0) for r in outputs),
        zero_pairs=zero_pairs,
        paid_attempts=len(attempts),
        unknown_calls=len(unknown),
        known_input_tokens=sum(settle.values()),
        charged_tokens=sum(settle.values()) + 65536 * len(unknown),
        development_policies=len(rebuilt),
        selected=selected["selected"],
        panels=summaries,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        "ibm-granite/granite-4.0-1b",
        revision="6a7381ba1f54d684ff508d991aeb7dc580157103",
        local_files_only=True,
    )
    result = analyze(args.manifest, args.results, tokenizer=tokenizer)
    D["dump"](args.output, result)
    print(json.dumps({k: v for k, v in result.items() if k not in ("panels", "selected")}))


if __name__ == "__main__":
    main()
