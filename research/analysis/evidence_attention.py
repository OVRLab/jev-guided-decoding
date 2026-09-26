"""Independent R14 token, source-span, control and graph-result reconstruction."""

import argparse
import ast
import hashlib
import json
import math
import random
import re
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def reference_for(target, edges):
    successors = {}
    for a, b in edges:
        require(a not in successors or successors[a] == b, "Nonfunctional containment graph")
        successors[a] = b
    seen = set()
    while target not in seen:
        if target.startswith("room "):
            return target[5:]
        seen.add(target)
        if target not in successors:
            break
        target = successors[target]
    return "UNKNOWN"


def visible_edges(sources):
    result = []
    for source in sources:
        direct = re.fullmatch(r"The (.+) is inside the (.+)\.", source["text"])
        reverse = re.fullmatch(r"The (.+) contains the (.+)\.", source["text"])
        require(direct is not None or reverse is not None, "Unknown visible record syntax")
        result.append(direct.groups() if direct else tuple(reversed(reverse.groups())))
    return result


def audit_decision(row, encoded):
    require(row["prompt_digest"] == encoded["prompt_digest"], "Output/input digest mismatch")
    logits = row["label_logits"]
    require(
        len(logits) == len(encoded["labels"]) and all(math.isfinite(x) for x in logits),
        "Invalid logits",
    )
    winner = max(range(len(logits)), key=lambda i: logits[i])
    require(
        row["generated_token_ids"] == [encoded["label_ids"][winner]],
        "Token not selected by Granite logits",
    )
    require(row["label"] == encoded["labels"][winner], "Label not generated token")
    weights = [math.exp(x - max(logits)) for x in logits]
    expected = [w / sum(weights) for w in weights]
    require(len(expected) == len(row["label_probabilities"]), "Wrong probability count")
    require(
        all(
            math.isclose(x, y, abs_tol=1e-10, rel_tol=1e-10)
            for x, y in zip(expected, row["label_probabilities"], strict=True)
        ),
        "Logit probability reconstruction failed",
    )


def audit_bias(row, encoded, heads, scores, strength):
    require(row["heads"] == [list(h) for h in heads], "Wrong intervened heads")
    require(row["span_scores"] == list(scores), "Wrong source scores")
    require(row["strength"] == strength, "Wrong intervention strength")
    actual = {int(k): v for k, v in row["token_bias"].items()}
    expected = {}
    if scores and max(scores) != min(scores) and strength:
        for group, score in zip(encoded["span_token_indices"], scores, strict=True):
            for position in group:
                require(position < encoded["query_start"], "Evidence bias touches query")
                value = strength * max(0.0, 2 * score - 1)
                if value:
                    expected[position] = value
    require(set(actual) == set(expected), "Wrong biased source coordinates")
    require(
        all(math.isclose(actual[k], v, rel_tol=1e-10, abs_tol=1e-10) for k, v in expected.items()),
        "Wrong bias magnitude",
    )
    require(row["hook_calls"] == len({h[0] for h in heads}), "Wrong hook execution count")


def read_rows(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines()]


def audit_inputs(records, cases, tokenizer, system):
    index = {}
    for record in records:
        case = cases[record["id"]]
        highlights = set(record["highlighted_source_ids"])
        require(highlights.issubset(s["id"] for s in case["sources"]), "Unknown highlighted source")
        lines = []
        for s in case["sources"]:
            line = f"[{s['id']}] {s['text']}"
            if s["id"] in highlights:
                line = "<focus>" + line + "</focus>"
            lines.append(line)
        evidence = "\n".join(lines)
        text = tokenizer.apply_chat_template(
            [
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": "Evidence:\n" + evidence + "\n\nQuestion:\n" + case["question"],
                },
            ],
            tokenize=False,
            add_generation_prompt=True,
        )
        encoded = tokenizer(text, add_special_tokens=False, return_offsets_mapping=True)
        require(
            record["rendered_prompt"] == text and record["input_ids"] == encoded["input_ids"],
            "Original prompt reconstruction failed",
        )
        digest = hashlib.sha256(
            json.dumps(encoded["input_ids"], sort_keys=True).encode()
        ).hexdigest()
        require(digest == record["prompt_digest"], "Input hash mismatch")
        location = text.index("Evidence:\n") + len("Evidence:\n")
        for line, bounds, token_indices in zip(
            lines, record["character_ranges"], record["span_token_indices"], strict=True
        ):
            require(bounds == [location, location + len(line)], "Source character span differs")
            expected = [
                i
                for i, (a, b) in enumerate(encoded["offset_mapping"])
                if b > a and b > location and a < location + len(line)
            ]
            require(token_indices == expected, "Source/token offset mismatch")
            location += len(line) + 1
        q = text.index("Question:", text.index("Evidence:\n") + len("Evidence:\n") + len(evidence))
        expected_query = next(
            i for i, (a, b) in enumerate(encoded["offset_mapping"]) if b > a and a >= q
        )
        require(record["query_start"] == expected_query, "Attention query boundary differs")
        require(
            all(
                tokenizer.decode([t], skip_special_tokens=True) == label
                for label, t in zip(record["labels"], record["label_ids"], strict=True)
            ),
            "Answer-token identity fails",
        )
        key = (record["id"], record["prompt_digest"])
        require(key not in index, "Duplicate input record")
        index[key] = record
    return index


def independent_statistics(rows, cases, arms, controls, draws):
    import numpy as np

    worlds = list(dict.fromkeys(c["world_id"] for c in cases))
    lookup = {(r["id"], r["mode"]): r for r in rows}
    require(len(lookup) == len(rows), "Duplicate output")
    scores = np.zeros((len(worlds), len(arms)))
    counts = np.zeros(len(worlds))
    for case in cases:
        wi = worlds.index(case["world_id"])
        counts[wi] += 1
        for mi, mode in enumerate(arms):
            row = lookup.get((case["id"], mode), {})
            scores[wi, mi] += (
                row.get("status") == "complete" and row.get("label") == case["reference"]
            )
    scores /= counts[:, None]
    result = {"accuracy": dict(zip(arms, scores.mean(0).tolist(), strict=True)), "comparisons": {}}
    if draws:
        rng = random.Random(140920261)
        indices = np.array(
            [rng.choices(range(len(worlds)), k=len(worlds)) for _ in range(draws)], dtype=np.int32
        )
        for mode in controls:
            delta = scores[:, arms.index("jev")] - scores[:, arms.index(mode)]
            means = np.sort(delta[indices].mean(1))
            result["comparisons"][mode] = {
                "difference": float(delta.mean()),
                "interval": [
                    float(means[int(draws * 0.00625)]),
                    float(means[min(draws - 1, int(draws * 0.99375))]),
                ],
            }
    return result


def run(args):
    from transformers import AutoTokenizer

    D = runpy.run_path(str(ROOT / "research/experiments/evidence_data.py"))
    S = runpy.run_path(str(ROOT / "research/experiments/evidence_study.py"))
    E = runpy.run_path(str(ROOT / "research/experiments/evidence_scorer.py"))
    manifest = json.loads((args.manifest / "manifest.json").read_text())
    metadata = json.loads((args.results / "metadata.json").read_text())
    completion = json.loads((args.results / "completion.json").read_text())
    require(metadata["source_hashes"] == manifest["source_hashes"], "Execution source mismatch")
    require(
        completion["weights_before"] == completion["weights_after"] == metadata["weights_before"],
        "Model weights changed",
    )
    all_cases, splits = {}, {}
    for split in ("profile", "calibration", "test"):
        path = args.manifest / f"{split}.json"
        require(
            hashlib.sha256(path.read_bytes()).hexdigest() == manifest["dataset_hashes"][split],
            "Data changed",
        )
        worlds = json.loads(path.read_text())
        cases = [
            D["context"](w, condition) for w in worlds for condition in ("clean", "distracted")
        ]
        for c in cases:
            edges = visible_edges(c["sources"])
            require(edges == [tuple(e) for e in c["edges"]], "Visible facts disagree with graph")
            require(
                c["question"] == f"Which room contains the {c['target']}?", "Wrong queried parcel"
            )
            require(
                reference_for(c["target"], edges) == c["reference"],
                "Independent graph grade differs",
            )
            all_cases[c["id"]] = c
        splits[split] = cases
    tokenizer = AutoTokenizer.from_pretrained(
        manifest["model"], revision=manifest["revision"], local_files_only=True
    )
    tree = ast.parse((ROOT / "research/experiments/evidence_runtime.py").read_text())
    system = next(
        ast.literal_eval(node.value)
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "SYSTEM" for t in node.targets)
    )
    inputs = audit_inputs(read_rows(args.results / "inputs.jsonl"), all_cases, tokenizer, system)
    policy = json.loads((args.results / "selected-policy.json").read_text())
    ranking = json.loads((args.results / "head-ranking.json").read_text())
    ranked_heads = [r["head"] for r in ranking]
    counters = {
        "inputs": len(inputs),
        "decisions": 0,
        "biases": 0,
        "zero_pairs": 0,
        "scorer_receipts": 0,
    }
    summaries = {}
    profile_totals = {tuple(r["head"]): 0.0 for r in ranking}
    profile_native = {}
    for stage in ("profile", "calibration", "pilot", "test"):
        rows = read_rows(args.results / f"{stage}.jsonl")
        if not rows:
            continue
        cases = (
            splits["profile"]
            if stage == "profile"
            else splits["test"]
            if stage == "test"
            else splits["calibration"][:12]
            if stage == "pilot"
            else splits["calibration"]
        )
        order = {c["id"]: i for i, c in enumerate(cases)}
        receipts = {}
        for score_row in read_rows(args.results / f"{stage}-scores.jsonl"):
            require(score_row["id"] not in receipts, "Repeated Jev context")
            if score_row["status"] != "complete":
                receipts[score_row["id"]] = None
                continue
            c = all_cases[score_row["id"]]
            require(
                score_row["payload"] == E["payload_for"](D["model_view"](c), manifest["jev_model"]),
                "Scorer payload differs",
            )
            evaluation = score_row["evaluation"]
            values = [
                evaluation["raw_response"]["answers"][f"relevance_{i}"]["noul"]
                for i in range(len(c["sources"]))
            ]
            require(
                values == evaluation["scores"] and evaluation["model"] == manifest["jev_model"],
                "Scorer receipt differs",
            )
            receipts[c["id"]] = evaluation
            counters["scorer_receipts"] += 1
        seen, by_key = set(), {}
        if stage == "profile":
            modes = ["native", "zero"] + [
                f"head_{layer}_{head}" for layer in range(40) for head in range(16)
            ]
            expected_keys = {
                (c["id"], m) for c in cases if c["condition"] == "distracted" for m in modes
            }
        elif stage == "calibration":
            modes = ["native"] + [
                f"oracle_{n}_{strength:.6f}"
                for n in manifest["head_counts"]
                for strength in manifest["strengths"]
            ]
            expected_keys = {(c["id"], m) for c in cases for m in modes}
        else:
            expected_keys = {(c["id"], m) for c in cases for m in S["ARMS"]}
        for row in rows:
            c = all_cases[row["id"]]
            mode = row["mode"]
            key = (row["id"], mode)
            require(key not in seen, "Repeated generation job")
            require(key in expected_keys, "Unplanned generation job")
            seen.add(key)
            by_key[key] = row
            if row["status"] != "complete":
                continue
            encoded = inputs[(row["id"], row["prompt_digest"])]
            audit_decision(row, encoded)
            counters["decisions"] += 1
            require(row["correct"] == (row["label"] == c["reference"]), "Recorded grade differs")
            lp = math.log(row["label_probabilities"][encoded["labels"].index(c["reference"])])
            require(
                math.isclose(lp, row["reference_logprob"], rel_tol=1e-10, abs_tol=1e-10),
                "Reference diagnostic differs",
            )
            heads, scores, strength = [], [], 0.0
            if mode == "native":
                if stage == "profile":
                    profile_native[c["id"]] = lp
            elif stage == "profile":
                heads = [[0, 0]] if mode == "zero" else [[int(x) for x in mode.split("_")[1:]]]
                scores = c["oracle_scores"]
                strength = 0 if mode == "zero" else math.log(4)
                if mode != "zero":
                    profile_totals[tuple(heads[0])] += lp - profile_native[c["id"]]
            elif stage == "calibration":
                _, count, encoded_strength = mode.split("_")
                heads = ranked_heads[: int(count)]
                strength = next(v for v in manifest["strengths"] if f"{v:.6f}" == encoded_strength)
                scores = c["oracle_scores"]
            else:
                if mode in S["DEPENDENT"]:
                    require(
                        receipts.get(c["id"]) is not None, "Guidance lacks a successful receipt"
                    )
                if mode == "prompt":
                    expected_highlights = sorted(
                        s["id"]
                        for s, r in zip(c["sources"], receipts[c["id"]]["scores"], strict=True)
                        if r > 0.5
                    )
                    require(
                        encoded["highlighted_source_ids"] == expected_highlights,
                        "Prompt emphasis differs",
                    )
                elif mode != "native":
                    heads = policy["random_heads"] if mode == "random_heads" else policy["heads"]
                    strength = 0 if mode == "zero" else policy["strength"]
                    if mode == "zero":
                        scores = [0.0] * len(c["sources"])
                    elif mode == "oracle":
                        scores = c["oracle_scores"]
                    elif mode == "lexical":
                        scores = D["lexical_scores"](D["model_view"](c))
                    else:
                        scores = list(receipts[c["id"]]["scores"])
                        if mode == "shuffled":
                            random.Random(14000 + order[c["id"]]).shuffle(scores)
            if mode != "prompt":
                require(not encoded["highlighted_source_ids"], "Attention arm changed source text")
            audit_bias(row, encoded, heads, scores, strength)
            counters["biases"] += 1
        require(seen == expected_keys, f"Incomplete {stage} schedule")
        if stage == "calibration":
            buckets = {}
            for row in rows:
                buckets.setdefault(row["mode"], []).append(row)

            def metrics(bucket):
                clean = [r for r in bucket if r["condition"] == "clean"]
                return (
                    sum(r["correct"] for r in bucket) / len(bucket),
                    sum(r["reference_logprob"] for r in bucket) / len(bucket),
                    sum(r["correct"] for r in clean) / len(clean),
                )

            candidates = []
            for n in manifest["head_counts"]:
                for strength in manifest["strengths"]:
                    acc, lp, clean = metrics(buckets[f"oracle_{n}_{strength:.6f}"])
                    candidates.append((acc, lp, -n, -strength, clean))
            winner = max(candidates, key=lambda x: x[:4])
            native_acc, _, native_clean = metrics(buckets["native"])
            admitted = (
                winner[0] - native_acc >= 0.03 - 1e-12 and winner[4] - native_clean >= -0.03 - 1e-12
            )
            require(
                policy["count"] == -winner[2] and policy["strength"] == -winner[3],
                "Selected policy differs",
            )
            require(
                policy["heads"] == ranked_heads[: policy["count"]]
                and policy["admitted"] == admitted,
                "Policy/headroom gate differs",
            )
        for c in cases:
            native, zero = (by_key.get((c["id"], m)) for m in ("native", "zero"))
            if native and zero and native["status"] == zero["status"] == "complete":
                require(
                    native["label_logits"] == zero["label_logits"]
                    and native["generated_token_ids"] == zero["generated_token_ids"],
                    "Zero/native identity differs",
                )
                counters["zero_pairs"] += 1
        if stage in ("pilot", "test"):
            summary = S["summarize"](
                rows, cases, draws=manifest["bootstrap_draws"] if stage == "test" else 0
            )
            published = json.loads((args.results / f"{stage}-summary.json").read_text())
            require(
                summary["arms"] == published["arms"]
                and summary["comparisons"] == published["comparisons"],
                "Runner summary does not reproduce",
            )
            independent = independent_statistics(
                rows,
                cases,
                list(S["ARMS"]),
                list(S["CONTROLS"]),
                manifest["bootstrap_draws"] if stage == "test" else 0,
            )
            for mode, accuracy in independent["accuracy"].items():
                require(
                    math.isclose(accuracy, summary["arms"][mode]["accuracy"], abs_tol=1e-12),
                    "Independent accuracy differs",
                )
            for mode, contrast in independent["comparisons"].items():
                require(
                    all(
                        math.isclose(x, y, abs_tol=1e-12)
                        for x, y in zip(
                            contrast["interval"],
                            summary["comparisons"][mode]["interval"],
                            strict=True,
                        )
                    ),
                    "Independent bootstrap differs",
                )
            summaries[stage] = {"summary": summary, "independent_statistics": independent}
    expected_ranking = sorted(profile_totals, key=lambda h: (-profile_totals[h], h))
    require(
        [list(h) for h in expected_ranking] == ranked_heads, "Head ranking fails reconstruction"
    )
    result = dict(
        status="passed",
        counters=counters,
        weights_unchanged=True,
        stages=summaries,
        oracle_admitted=policy["admitted"],
        analysis_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    )
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"status": "passed", **counters}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args())
