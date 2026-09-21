"""Independent R15 reconstruction of maps, selection, token ownership and statistics."""

import argparse
import copy
import hashlib
import json
import math
import random
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
A = runpy.run_path(str(ROOT / "research/analysis/evidence_attention.py"))
require = A["require"]
ARMS = (
    "native",
    "r14",
    "r15",
    "shuffled",
    "lexical",
    "prompt",
    "oracle",
    "zero",
    "mapping_only",
    "heads_only",
    "strength_only",
    "scope_only",
)


def read(path):
    return json.loads(path.read_text())


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def expected_policy(arm, previous, selected):
    if arm in ("native", "prompt"):
        return None
    result = copy.deepcopy(previous if arm == "r14" or arm.endswith("_only") else selected)
    if arm == "zero":
        result.update(strength=0.0, id="zero")
    fields = {
        "heads_only": ("heads", "count"),
        "mapping_only": ("mapping",),
        "strength_only": ("strength",),
        "scope_only": ("scope",),
    }
    if arm in fields:
        for key in fields[arm]:
            result[key] = copy.deepcopy(selected[key])
        result["id"] = arm
    return result


def audit_row(row, encoded, policy, scores):
    require(
        row["policy"] == policy and row["raw_scores"] == scores, "Policy or source score mismatch"
    )
    query = (
        len(encoded["input_ids"]) - 1
        if policy and policy["scope"] == "answer"
        else encoded["query_start"]
    )
    require(row["query_start"] == query, "Wrong query scope")
    mapped = []
    if policy:
        if policy["mapping"] == "soft":
            mapped = scores
        else:
            require(policy["mapping"] in ("hard50", "hard80"), "Unknown mapping")
            threshold = 0.5 if policy["mapping"] == "hard50" else 0.8
            mapped = [int(value > threshold) for value in scores]
    A["audit_decision"](row, encoded)
    A["audit_bias"](
        row,
        {**encoded, "query_start": query},
        policy["heads"] if policy else [],
        mapped,
        policy["strength"] if policy else 0.0,
    )


def independent_statistics(records, cases, summary, draws, confirmatory):
    import numpy as np

    index = {(r["id"], r["mode"]): r for r in records}
    groups = {}
    for c in cases:
        groups.setdefault(c["world_id"], []).append(c)

    def correct(c, mode):
        r = index.get((c["id"], mode), {})
        return int(r.get("status") == "complete" and r.get("label") == c["reference"])

    values = np.array(
        [
            [sum(correct(c, arm) for c in group) / len(group) for arm in ARMS]
            for group in groups.values()
        ]
    )
    rng = random.Random(150922071)
    indices = np.array([rng.choices(range(len(groups)), k=len(groups)) for _ in range(draws)])
    result = {}
    for i, arm in enumerate(ARMS):
        require(
            math.isclose(
                float(values[:, i].mean()), summary["arms"][arm]["accuracy"], abs_tol=1e-12
            ),
            "Accuracy mismatch",
        )
        if arm == "r15":
            continue
        diff = values[:, ARMS.index("r15")] - values[:, i]
        boot = np.sort(diff[indices].mean(axis=1))
        alpha = 0.025 if confirmatory and arm in ("native", "r14") else 0.05
        lo, hi = (
            float(boot[int(draws * alpha / 2)]),
            float(boot[min(draws - 1, int(draws * (1 - alpha / 2)))]),
        )
        given = summary["primary" if arm in ("native", "r14") else "secondary"][arm]
        require(
            math.isclose(float(diff.mean()), given["difference"], abs_tol=1e-12),
            "Paired difference mismatch",
        )
        require(
            all(
                math.isclose(x, y, abs_tol=1e-12)
                for x, y in zip((lo, hi), given["interval"], strict=True)
            ),
            "Bootstrap mismatch",
        )
        require(
            [int((diff > 0).sum()), int((diff < 0).sum()), int((diff == 0).sum())]
            == [given["world_wins"], given["world_losses"], given["world_ties"]],
            "Paired world counts mismatch",
        )
        result[arm] = dict(
            difference=float(diff.mean()), interval=[lo, hi], interval_level=1 - alpha
        )
    expected = (
        (
            result["r14"]["difference"] >= 0.02 - 1e-12
            and result["r14"]["interval"][0] > 0
            and result["native"]["interval"][0] > 0
        )
        if confirmatory
        else None
    )
    require(summary["advancement"] == expected, "Advancement decision mismatch")
    return result


def grade_metrics(records, cases):
    index = {c["id"]: c for c in cases}

    def correct(r):
        return r.get("status") == "complete" and r.get("label") == index[r["id"]]["reference"]

    successful = [r for r in records if r["status"] == "complete"]
    out = dict(
        accuracy=sum(correct(r) for r in records) / len(records),
        mean_logprob=sum(
            math.log(
                r["label_probabilities"][
                    index[r["id"]]["labels"].index(index[r["id"]]["reference"])
                ]
            )
            for r in successful
        )
        / len(successful),
    )
    for name, keep in [
        ("answerable", lambda c: not c["missing"]),
        ("missing", lambda c: c["missing"]),
        ("clean", lambda c: c["condition"] == "clean"),
    ]:
        subset = [r for r in records if keep(index[r["id"]])]
        out[name] = sum(correct(r) for r in subset) / len(subset)
    return out


def run(args):
    from transformers import AutoTokenizer

    data = runpy.run_path(str(ROOT / "research/iterations/evidence_v2/data.py"))
    runtime = runpy.run_path(str(ROOT / "research/experiments/evidence_runtime.py"))
    scorer = runpy.run_path(str(ROOT / "research/experiments/evidence_scorer.py"))
    manifest = read(args.manifest / "manifest.json")
    metadata, completion = (
        read(args.results / "metadata.json"),
        read(args.results / "completion.json"),
    )
    require(metadata["source_hashes"] == manifest["source_hashes"], "Executing source mismatch")
    for name, digest in manifest["source_hashes"].items():
        require(
            hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest,
            "Current source mismatch: " + name,
        )
    require(
        hashlib.sha256(
            (ROOT / "research/evidence-attention-v2-protocol.md").read_bytes()
        ).hexdigest()
        == manifest["protocol_sha256"],
        "Protocol changed",
    )
    require(
        metadata["weights_before"] == completion["weights_before"] == completion["weights_after"],
        "Weights changed",
    )
    require(metadata["git_status"] == "", "Executing checkout was dirty")
    require(
        metadata["model"]["resolved_revision"] == manifest["revision"], "Model revision mismatch"
    )
    recovery = None
    if (args.results / "recovery.json").exists():
        recovery = read(args.results / "recovery.json")
        require(
            args.prior is not None and args.ledger is not None,
            "Recovery needs original artifacts and ledger",
        )
        registration_name = (
            "recovery2.json" if "ancestor_registration" in recovery else "recovery.json"
        )
        require(
            recovery == read(args.manifest / registration_name), "Recovery registration changed"
        )
        if "ancestor_registration" in recovery:
            ancestor = read(ROOT / recovery["ancestor_registration"])
            require(args.original is not None, "Original transport segment is required")
            require(
                read(args.prior / "recovery.json") == ancestor,
                "Original recovery registration changed",
            )
            for name, expected in ancestor["prior_files"].items():
                raw = (args.original / name).read_bytes()
                require(
                    len(raw) == expected["bytes"]
                    and hashlib.sha256(raw).hexdigest() == expected["sha256"],
                    "Original transport artifact changed",
                )
                if name.endswith(".jsonl"):
                    require(
                        (args.prior / name).read_bytes().startswith(raw),
                        "First recovery changed raw prefix",
                    )
            for key, digest_key in (
                ("helper_path", "helper_sha256"),
                ("amendment_path", "amendment_sha256"),
            ):
                require(
                    hashlib.sha256((ROOT / ancestor[key]).read_bytes()).hexdigest()
                    == ancestor[digest_key],
                    "First recovery source changed",
                )
            require(
                read(args.original / "completion.json")["weights_after"]
                == read(args.prior / "metadata.json")["weights_before"],
                "First recovery weights changed",
            )
            require(
                ancestor["at"] < read(args.prior / "metadata.json")["at"],
                "First recovery registration not prospective",
            )
        for name, expected in recovery["prior_files"].items():
            original_bytes = (args.prior / name).read_bytes()
            require(
                len(original_bytes) == expected["bytes"]
                and hashlib.sha256(original_bytes).hexdigest() == expected["sha256"],
                "Original interrupted artifact changed",
            )
            if name.endswith(".jsonl"):
                require(
                    (args.results / name).read_bytes().startswith(original_bytes),
                    "Original raw prefix changed",
                )
        for path_key, hash_key in (
            ("helper_path", "helper_sha256"),
            ("amendment_path", "amendment_sha256"),
        ):
            require(
                hashlib.sha256((ROOT / recovery[path_key]).read_bytes()).hexdigest()
                == recovery[hash_key],
                "Recovery source or amendment changed",
            )
        require(
            read(args.prior / "completion.json")["weights_after"] == metadata["weights_before"],
            "Recovery weight lineage changed",
        )
        require(
            not any(
                (args.prior / name).exists()
                for name in ("selected-policy.json", "test.jsonl", "challenge.jsonl")
            ),
            "Recovery occurred after selection or test",
        )
        require(recovery["at"] < metadata["at"], "Recovery was not registered prospectively")
    previous = manifest["previous_policy"]
    ranking = read(ROOT / "reports/2026-09-21-evidence-attention/artifacts/head-ranking.json")
    original = read(ROOT / "reports/2026-09-21-evidence-attention/artifacts/selected-policy.json")
    require(
        previous["heads"] == original["heads"] and previous["strength"] == original["strength"],
        "R14 lineage changed",
    )
    require(
        previous["mapping"] == "soft" and previous["scope"] == "question", "R14 semantics changed"
    )
    grid = manifest["grid"]
    require(len(grid) == 90 and len({p["id"] for p in grid}) == 90, "Wrong grid size")
    required = {
        (n, math.log(f), m, q)
        for n in (1, 2, 4, 8, 12)
        for f in (4, 8, 16)
        for m in ("soft", "hard50", "hard80")
        for q in ("question", "answer")
    }
    require(
        {(p["count"], p["strength"], p["mapping"], p["scope"]) for p in grid} == required,
        "Wrong grid factors",
    )
    for p in grid:
        require(p["heads"] == [r["head"] for r in ranking[: p["count"]]], "Wrong profiled heads")
    splits, all_cases = {}, {}
    used = data["exposed_aliases"]()
    for split, count in [("development", 96), ("test", 600), ("challenge", 120)]:
        path = args.manifest / f"{split}.json"
        require(
            hashlib.sha256(path.read_bytes()).hexdigest() == manifest["dataset_hashes"][split],
            "Dataset changed",
        )
        worlds = read(path)
        regenerated = json.loads(json.dumps(data["worlds"](split, count, used)))
        require(worlds == regenerated, "Seed/data reconstruction failed")
        cases = []
        for w in worlds:
            for condition in ("clean", "distracted"):
                c = data["context"](w, condition)
                edges = A["visible_edges"](c["sources"])
                require(edges == [tuple(e) for e in c["edges"]], "Visible edge direction mismatch")
                require(
                    A["reference_for"](c["target"], edges) == c["reference"],
                    "Independent graph grade mismatch",
                )
                # Independently mark only source edges visited from the queried parcel.
                relevant = set()
                node = c["target"]
                successors = dict(edges)
                while node in successors and node not in relevant:
                    relevant.add(node)
                    node = successors[node]
                require(
                    [int(a in relevant) for a, b in edges] == c["oracle_scores"],
                    "Oracle span mismatch",
                )
                c["labels"] = list(data["D"]["LABELS"])
                require(c["id"] not in all_cases, "Overlapping case ID")
                cases.append(c)
                all_cases[c["id"]] = c
        splits[split] = cases
    tokenizer = AutoTokenizer.from_pretrained(manifest["model"], revision=manifest["revision"])
    encoded = A["audit_inputs"](
        rows(args.results / "inputs.jsonl"), all_cases, tokenizer, runtime["SYSTEM"]
    )
    counters = dict(
        inputs=len(encoded),
        decisions=0,
        receipts=0,
        zero_pairs=0,
        failed_receipts=0,
        failed_outputs=0,
    )
    evaluations = {}
    for stage in splits:
        by = {}
        for r in rows(args.results / f"{stage}-scores.jsonl"):
            require(r["id"] not in by, "Duplicate receipt")
            by[r["id"]] = r
            if r["status"] != "complete":
                transport = (
                    r.get("status_code") is None
                    and r.get("usage_unknown") is True
                    and r.get("message") == "Jev request failed or timed out; it was not replayed"
                )
                require(
                    recovery is not None and (transport or r.get("status_code") in (429, 529)),
                    "Unadmitted provider failure",
                )
                require("evaluation" not in r, "Failure invents receipt")
                counters["failed_receipts"] += 1
                require(counters["failed_receipts"] <= 3, "Too many admitted incidents")
                continue
            case = all_cases[r["id"]]
            require(
                r["payload"]
                == scorer["payload_for"](data["model_view"](case), manifest["jev_model"]),
                "Scorer payload mismatch",
            )
            ev = r["evaluation"]
            require(
                ev["model"] == manifest["jev_model"] and ev["attempts"] == 1,
                "Provider identity/attempt mismatch",
            )
            answers = ev["raw_response"]["answers"]
            require(
                ev["scores"]
                == [answers[f"relevance_{i}"]["noul"] for i in range(len(case["sources"]))],
                "Typed receipt mismatch",
            )
            require(
                ev["input_tokens"] == ev["raw_response"]["usage"]["input_tokens"], "Usage mismatch"
            )
            require(
                ev["output_tokens"] == ev["raw_response"]["usage"]["output_tokens"],
                "Usage mismatch",
            )
            counters["receipts"] += 1
        require(set(by) == {c["id"] for c in splits[stage]}, "Receipt schedule mismatch")
        evaluations[stage] = by
    selected_record = read(args.results / "selected-policy.json")
    selected = selected_record["selected"]["policy"]
    dev = rows(args.results / "development.jsonl")
    expected = {(c["id"], p["id"]) for c in splits["development"] for p in grid}
    expected |= {(c["id"], "native") for c in splits["development"]}
    expected |= {(c["id"], "zero_check") for c in splits["development"][:12]}
    if recovery:
        original_ids = {
            r["id"] for r in rows(args.prior / "development.jsonl") if r["mode"] == "native"
        }
        fresh_successful = [
            c
            for c in splits["development"]
            if c["id"] not in original_ids
            and evaluations["development"][c["id"]]["status"] == "complete"
        ][: recovery.get("new_full_vocabulary_checks", 12)]
        require(
            len(fresh_successful) == recovery.get("new_full_vocabulary_checks", 12),
            "Missing fresh zero sample",
        )
        if "ancestor_registration" in recovery:
            previous_checks = (
                recovery["retained_full_vocabulary_check_ids"]
                + recovery["lost_full_vocabulary_check_ids"]
            )
            expected |= {(ident, "recovery_zero_check") for ident in previous_checks}
        expected |= {(c["id"], "recovery_zero_check") for c in fresh_successful}
    require(
        len(dev) == len(expected) and {(r["id"], r["mode"]) for r in dev} == expected,
        "Development schedule mismatch",
    )
    buckets = {p["id"]: [] for p in grid}
    native = []
    dev_pairs = {}
    grid_by = {p["id"]: p for p in grid}
    for r in dev:
        if r["status"] != "complete":
            receipt = evaluations["development"][r["id"]]
            require(
                recovery is not None and receipt["status"] == "failed" and r["mode"] in grid_by,
                "Unexplained failed development output",
            )
            require(
                r["provider_failure"]
                in (
                    receipt,
                    {k: v for k, v in receipt.items() if k not in ("id", "stage", "status")},
                )
                and "label" not in r
                and "generated_token_ids" not in r,
                "Fabricated failed output",
            )
            buckets[r["mode"]].append(r)
            counters["failed_outputs"] += 1
            continue
        policy = (
            None
            if r["mode"] == "native"
            else {**previous, "strength": 0.0}
            if r["mode"] in ("zero_check", "recovery_zero_check")
            else grid_by[r["mode"]]
        )
        scores = (
            None if policy is None else evaluations["development"][r["id"]]["evaluation"]["scores"]
        )
        audit_row(r, encoded[(r["id"], r["prompt_digest"])], policy, scores)
        require(
            r["correct"] == (r["label"] == all_cases[r["id"]]["reference"]), "Stored grade mismatch"
        )
        counters["decisions"] += 1
        dev_pairs[r["id"], r["mode"]] = r
        if r["mode"] == "native":
            native.append(r)
        elif r["mode"] not in ("zero_check", "recovery_zero_check"):
            buckets[r["mode"]].append(r)
    prior_metrics = grade_metrics(buckets[previous["id"]], splits["development"])
    candidates = []
    for policy in grid:
        metric = grade_metrics(buckets[policy["id"]], splits["development"])
        if recovery:
            metric.update(
                complete=sum(r["status"] == "complete" for r in buckets[policy["id"]]),
                failed=sum(r["status"] != "complete" for r in buckets[policy["id"]]),
            )
        failures = [
            k
            for k in ("answerable", "missing", "clean")
            if metric[k] < prior_metrics[k] - 0.03 - 1e-12
        ]
        entry = dict(policy=policy, **metric, eligible=not failures, floor_failures=failures)
        given = next(c for c in selected_record["candidates"] if c["policy"]["id"] == policy["id"])
        for k, v in entry.items():
            require(
                math.isclose(v, given[k], abs_tol=1e-12) if type(v) is float else v == given[k],
                "Calibration summary mismatch",
            )
        candidates.append(entry)
    winner = min(
        [c for c in candidates if c["eligible"]],
        key=lambda c: (
            -c["accuracy"],
            -c["mean_logprob"],
            c["policy"]["count"],
            c["policy"]["strength"],
            c["policy"]["mapping"],
            c["policy"]["scope"],
        ),
    )
    require(winner["policy"] == selected, "Selection mismatch")
    for c in splits["development"][:12]:
        a, b = dev_pairs[c["id"], "native"], dev_pairs[c["id"], "zero_check"]
        require(
            a["label_logits"] == b["label_logits"]
            and a["generated_token_ids"] == b["generated_token_ids"],
            "Development zero mismatch",
        )
        counters["zero_pairs"] += 1
    equivalence = read(args.results / "zero-equivalence.json")
    require(
        len(equivalence) == 12
        and all(r["equal"] and r["max_logit_delta"] <= 1e-6 for r in equivalence),
        "Full-vocabulary zero control failed",
    )
    if recovery:
        require(
            [r["id"] for r in equivalence]
            == recovery.get("retained_full_vocabulary_check_ids", [])
            + [c["id"] for c in fresh_successful],
            "Full-vocabulary checks are not first new successful contexts",
        )
        checks = [
            all_cases[ident]
            for ident in recovery.get("retained_full_vocabulary_check_ids", [])
            + recovery.get("lost_full_vocabulary_check_ids", [])
        ] + fresh_successful
        for c in checks:
            a, b = dev_pairs[c["id"], "native"], dev_pairs[c["id"], "recovery_zero_check"]
            require(
                a["label_logits"] == b["label_logits"]
                and a["generated_token_ids"] == b["generated_token_ids"],
                "Fresh zero control mismatch",
            )
            counters["zero_pairs"] += 1
    statistics = {}
    all_records = {"development": dev}
    for stage in ("test", "challenge"):
        records = rows(args.results / f"{stage}.jsonl")
        all_records[stage] = records
        expected = {(c["id"], arm) for c in splits[stage] for arm in ARMS}
        require(
            len(records) == len(expected) and {(r["id"], r["mode"]) for r in records} == expected,
            "Held-out schedule mismatch",
        )
        index = {(r["id"], r["mode"]): r for r in records}
        for ci, c in enumerate(splits[stage]):
            receipt = evaluations[stage][c["id"]]
            scores = receipt.get("evaluation", {}).get("scores", [])
            shuffled = scores.copy()
            random.Random(f"r15/{stage}/{ci}/shuffle").shuffle(shuffled)
            for arm in ARMS:
                r = index[c["id"], arm]
                dependent = arm not in ("native", "lexical", "oracle", "zero")
                if receipt["status"] == "failed" and dependent:
                    require(
                        r["status"] == "failed"
                        and "label" not in r
                        and "generated_token_ids" not in r,
                        "Failed receipt produced guided tokens",
                    )
                    require(
                        r["provider_failure"]
                        == {k: v for k, v in receipt.items() if k not in ("id", "stage", "status")},
                        "Failed outcome receipt mismatch",
                    )
                    counters["failed_outputs"] += 1
                    continue
                require(
                    r["status"] == "complete",
                    "Incomplete independent or successful guided decision",
                )
                policy = expected_policy(arm, previous, selected)
                raw = (
                    None
                    if policy is None
                    else (
                        [0.0] * len(c["sources"])
                        if arm == "zero"
                        else c["oracle_scores"]
                        if arm == "oracle"
                        else data["lexical_scores"](data["model_view"](c))
                        if arm == "lexical"
                        else shuffled
                        if arm == "shuffled"
                        else scores
                    )
                )
                enc = encoded[(c["id"], r["prompt_digest"])]
                highlights = (
                    [s["id"] for s, score in zip(c["sources"], scores, strict=True) if score > 0.5]
                    if arm == "prompt"
                    else []
                )
                require(
                    enc["highlighted_source_ids"] == sorted(highlights),
                    "Prompt highlighting mismatch",
                )
                audit_row(r, enc, policy, raw)
                require(
                    r["correct"] == (r["label"] == c["reference"]), "Held-out stored grade mismatch"
                )
                counters["decisions"] += 1
            a, b = index[c["id"], "native"], index[c["id"], "zero"]
            require(
                a["label_logits"] == b["label_logits"]
                and a["generated_token_ids"] == b["generated_token_ids"],
                "Held-out zero mismatch",
            )
            counters["zero_pairs"] += 1
        statistics[stage] = independent_statistics(
            records,
            splits[stage],
            read(args.results / f"{stage}-summary.json"),
            manifest["bootstrap_draws"],
            stage == "test",
        )
    starts = rows(args.results / "starts.jsonl")
    expected_starts = {
        ("model", stage, r["id"], r["mode"])
        for stage, records in all_records.items()
        for r in records
        if r["status"] == "complete"
    }
    expected_starts |= {
        ("jev", stage, c["id"], "relevance") for stage, cases in splits.items() for c in cases
    }
    require(
        len(starts) == len(expected_starts)
        and {(r["kind"], r["stage"], r["id"], r["mode"]) for r in starts} == expected_starts,
        "Started schedule mismatch",
    )
    freeze = read(args.results / "test-freeze.json")
    require(
        freeze["selected_policy_sha256"]
        == hashlib.sha256((args.results / "selected-policy.json").read_bytes()).hexdigest(),
        "Selected-policy freeze mismatch",
    )
    require(
        freeze["source_hashes"] == manifest["source_hashes"]
        and freeze["dataset_hashes"] == manifest["dataset_hashes"],
        "Test freeze mismatch",
    )
    require(
        all(r["at"] > freeze["at"] for r in starts if r["stage"] in ("test", "challenge")),
        "Held-out operation before freeze",
    )
    total = sum(
        r["evaluation"]["input_tokens"]
        for stage in evaluations.values()
        for r in stage.values()
        if r["status"] == "complete"
    )
    require(
        completion["ledger"]
        == dict(charged_input_tokens=total + 65536 * counters["failed_receipts"], unresolved=0),
        "Budget usage mismatch",
    )
    if recovery:
        events = rows(args.ledger)
        reserves = [r["id"] for r in events if r["event"] == "reserve"]
        settlements = [r for r in events if r["event"] == "settle"]
        maximums = [r for r in events if r["event"] == "charge_max_unknown"]
        require(
            len(reserves)
            == len(set(reserves))
            == counters["receipts"] + counters["failed_receipts"],
            "Reservation count mismatch",
        )
        require(
            len(settlements) == counters["receipts"]
            and sum(r["input_tokens"] for r in settlements) == total,
            "Settled usage mismatch",
        )
        require(
            len(maximums) == counters["failed_receipts"], "Missing conservative unknown charges"
        )
        require(
            {r["id"] for r in settlements}.isdisjoint({r["id"] for r in maximums}),
            "Unknown charge overwritten",
        )
        require(
            {r["id"] for r in settlements + maximums} == set(reserves), "Unaccounted reservation"
        )
        require(
            all(r["at"] > recovery["at"] for r in starts[len(rows(args.prior / "starts.jsonl")) :]),
            "New work before registration",
        )
    result = dict(
        status="passed",
        counters=counters,
        recorded_outputs=sum(len(records) for records in all_records.values()),
        scorer_attempts=counters["receipts"] + counters["failed_receipts"],
        persisted_full_vocabulary_zero_pairs=len(equivalence),
        source_segments=[
            read(path / "metadata.json")["source_revision"]
            for path in (args.original, args.prior, args.results)
            if path is not None
        ],
        input_hashes={
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(args.results.iterdir())
            if p.is_file()
        },
        selected_policy=selected,
        weights_unchanged=True,
        statistics=statistics,
        analysis_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    )
    with args.output.open("x") as f:
        json.dump(result, f, indent=2, allow_nan=False)
        f.write("\n")
    print(json.dumps({"status": "passed", **counters}))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--results", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--prior", type=Path)
    p.add_argument("--original", type=Path)
    p.add_argument("--ledger", type=Path)
    run(p.parse_args())
