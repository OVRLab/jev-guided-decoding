"""Offline reconstruction and exploratory paired analysis of R16 factorial controls."""

import argparse
import hashlib
import itertools
import json
import math
import runpy
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research/iterations/adaptive_attention"
A = runpy.run_path(str(HERE / "analyze.py"))
D = runpy.run_path(str(HERE / "data.py"))
J = runpy.run_path(str(HERE / "journal.py"))
F = runpy.run_path(str(ROOT / "research/iterations/adaptive_attention_factorial.py"))
S = runpy.run_path(str(HERE / "scorer.py"))


def corner(bits):
    return f"s{bits[0]}-h{bits[1]}-t{bits[2]}"


def effects(outcomes):
    import numpy as np

    bits = list(itertools.product((0, 1), repeat=3))
    if set(outcomes) != {corner(b) for b in bits} or len({len(v) for v in outcomes.values()}) != 1:
        raise ValueError("All eight corners require paired worlds")
    if not len(next(iter(outcomes.values()))):
        raise ValueError("No paired worlds")
    values = {b: np.asarray(outcomes[corner(b)]) for b in bits}
    names = ("strength", "head", "threshold")
    result = {"averaged": {}, "conditional": {}, "interactions": {}}
    for index, name in enumerate(names):
        conditional = []
        for low in (b for b in bits if b[index] == 0):
            high = tuple(1 if i == index else x for i, x in enumerate(low))
            differences = values[high] - values[low]
            condition = "/".join(f"{'sht'[i]}{x}" for i, x in enumerate(low) if i != index)
            result["conditional"][f"{name}/{condition}"] = A["paired"](differences)
            conditional.append(differences)
        result["averaged"][name] = A["paired"](np.mean(conditional, axis=0))
    for size in (2, 3):
        for indices in itertools.combinations(range(3), size):
            # Difference-of-differences, averaged over factors not in this interaction.
            differences = sum(
                values[b] * math.prod(1 if b[i] else -1 for i in indices) for b in bits
            ) / (2 ** (3 - size))
            result["interactions"][":".join(names[i] for i in indices)] = A["paired"](differences)
    return result


def verify_row(row, case, encoded, expected_policy, receipts, tokenizer):
    if (
        row["policy"] != expected_policy
        or row["contract"] != "constrained"
        or row["world_id"] != case["world_id"]
        or row["prompt_digest"] != encoded["prompt_digest"]
    ):
        raise ValueError("Factorial policy/input binding failed")
    payload = S["payload_for"](D["public_view"](case), "jev-1.13.0")
    key = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    receipt = receipts[key]
    if receipt["payload"] != payload or row["receipt_keys"] != [key]:
        raise ValueError("Factorial receipt binding failed")
    if receipt["status"] != "complete":
        if row["status"] != "provider_failed" or row["text"] or row["grade"]["correct"]:
            raise ValueError("Failed receipt became a scored answer")
        return
    if row["status"] != "complete":
        # Non-provider failures remain zero outcomes and must be reported, not dropped.
        return
    raw = receipt["raw_response"]
    scores = [raw["answers"][f"relevance_{i}"]["noul"] for i in range(len(case["sources"]))]
    if raw["model"] != "jev-1.13.0" or scores != receipt["scores"]:
        raise ValueError("Factorial typed receipt mismatch")
    expected_update = dict(
        reasoning="",
        receipt_key=key,
        raw_scores=scores,
        applied_scores=scores,
        after_generated_tokens=0,
    )
    if row["updates"] != [expected_update]:
        raise ValueError("Factorial source score mismatch")
    selected = [s > expected_policy["threshold"] for s in scores]
    expected_maps = []
    if any(selected) and not all(selected):
        for head, weight in zip(expected_policy["heads"], expected_policy["weights"], strict=True):
            if not weight:
                continue
            pairs = sorted(
                (token, weight)
                for span, active in zip(encoded["span_token_indices"], selected, strict=True)
                if active
                for token in span
            )
            expected_maps.append(
                dict(
                    head=head,
                    keys=len(pairs),
                    maximum=weight,
                    bias_sha256=hashlib.sha256(json.dumps(pairs).encode()).hexdigest(),
                )
            )
    if len(row["phases"]) != 1 or row["phases"][0]["maps"] != expected_maps:
        raise ValueError("Factorial attention mask mismatch")
    A["check_tokens"](row, encoded, tokenizer)
    if D["grade"](case, row["text"], "constrained") != row["grade"]:
        raise ValueError("Factorial independent grade mismatch")


def analyze(manifest, main, supplement, tokenizer):
    R = runpy.run_path(str(HERE / "runtime.py"))
    freeze = json.loads((supplement / "freeze.json").read_text())
    bound_paths = {
        "source": ROOT / "research/iterations/adaptive_attention_factorial.py",
        "protocol": ROOT / "research/adaptive-attention-factorial.md",
        "main_manifest": manifest / "manifest.json",
        "main_completion": main / "completion.json",
        "main_outputs": main / "outputs.jsonl",
        "main_receipts": main / "receipts.jsonl",
    }
    for name, path in bound_paths.items():
        if D["sha"](path) != freeze[f"{name}_sha256"]:
            raise ValueError("Factorial artifact binding mismatch: " + name)
    if freeze["paid_calls"] != 0 or freeze["policies"] != F["new_policies"]():
        raise ValueError("Factorial configuration changed")
    complete = json.loads((supplement / "completion.json").read_text())
    if (
        complete["planned"] != 3600
        or complete["outputs"] != 3600
        or complete["paid_calls"] != 0
        or complete["weights_before"] != complete["weights_after"]
        or complete["weights_after"]
        != json.loads((main / "completion.json").read_text())["weights_after"]
    ):
        raise ValueError("Factorial completion or checkpoint mismatch")
    cases = {c["id"]: c for c in json.loads((manifest / "test.json").read_text())}
    receipts = {r["key"]: r for r in J["rows"](main / "receipts.jsonl") if r["status"] != "started"}
    inputs = {r["id"]: r for r in J["rows"](supplement / "inputs.jsonl")}
    for ident, recorded in inputs.items():
        case = cases[ident]
        if D["visible_reference"](case) != case["reference"]:
            raise ValueError("Factorial graph reference mismatch")
        encoded = R["encode"](tokenizer, D["public_view"](case), "constrained")
        if json.loads(json.dumps(encoded)) != {k: v for k, v in recorded.items() if k != "id"}:
            raise ValueError("Factorial prompt reconstruction failed")
    rows = J["rows"](supplement / "outputs.jsonl")
    starts = J["rows"](supplement / "starts.jsonl")
    planned = {(ident, name) for ident in cases for name in F["new_policies"]()}
    if (
        len(rows) != 3600
        or {(r["case_id"], r["arm"]) for r in rows} != planned
        or len(starts) != len(rows)
        or len({r["job"] for r in starts}) != len(rows)
        or {r["job"] for r in starts} != {r["job"] for r in rows}
    ):
        raise ValueError("Factorial schedule mismatch")
    start_index = {r["job"]: r["metadata"] for r in starts}
    for row in rows:
        if row["stage"] != "factorial" or any(
            row[k] != v for k, v in start_index[row["job"]].items()
        ):
            raise ValueError("Factorial journal identity mismatch")
    primary = [
        r
        for r in J["rows"](main / "outputs.jsonl")
        if r["stage"] == "test" and r["contract"] == "constrained" and r["arm"] in ("r15", "tuned")
    ]
    if len(primary) != 1200:
        raise ValueError("Missing original factorial corners")
    policies = F["factorial_policies"]()
    combined = []
    for row in primary + rows:
        name = {"r15": "s0-h0-t0", "tuned": "s1-h1-t1"}.get(row["arm"], row["arm"])
        verify_row(
            row, cases[row["case_id"]], inputs[row["case_id"]], policies[name], receipts, tokenizer
        )
        combined.append((name, row))
    worlds = sorted({c["world_id"] for c in cases.values()})
    outcomes, summary = {}, {}
    for name, policy in policies.items():
        sub = [r for n, r in combined if n == name]
        outcomes[name] = []
        for world in worlds:
            group = [r for r in sub if r["world_id"] == world]
            if len(group) != 2:
                raise ValueError("Incomplete paired factorial world")
            outcomes[name].append(sum(r.get("grade", {}).get("correct", 0) for r in group) / 2)
        summary[name] = dict(
            policy=policy,
            n=len(sub),
            accuracy=sum(outcomes[name]) / len(worlds),
            groups={
                label: sum(
                    r.get("grade", {}).get("correct", 0)
                    for r in sub
                    if cases[r["case_id"]]["missing"] == missing
                )
                / sum(cases[r["case_id"]]["missing"] == missing for r in sub)
                for label, missing in (("answerable", False), ("missing", True))
            },
        )
    return dict(
        audit_passed=True,
        exploratory=True,
        new_outputs=len(rows),
        reused_outputs=len(primary),
        statuses=dict(Counter(r["status"] for r in rows)),
        verified_generated_tokens=sum(r.get("generated_tokens", 0) for _, r in combined),
        paid_calls=0,
        corners=summary,
        effects=effects(outcomes),
        frozen_artifacts=freeze,
    )


def main():
    from transformers import AutoTokenizer

    parser = argparse.ArgumentParser()
    for name in ("manifest", "main", "supplement", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    tokenizer = AutoTokenizer.from_pretrained(
        "ibm-granite/granite-4.0-1b",
        revision="6a7381ba1f54d684ff508d991aeb7dc580157103",
        local_files_only=True,
    )
    result = analyze(args.manifest, args.main, args.supplement, tokenizer)
    D["dump"](args.output, result)
    print(
        json.dumps(
            {k: v for k, v in result.items() if k not in ("corners", "effects", "frozen_artifacts")}
        )
    )


if __name__ == "__main__":
    main()
