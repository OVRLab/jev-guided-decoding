"""Offline R13 token reconstruction and descriptive critic/resource diagnostics."""

import argparse
import hashlib
import json
import runpy
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace

from jev_guided_decoding.framing import parse_frame

ROOT = Path(__file__).resolve().parents[1]
STUDY = runpy.run_path(str(ROOT / "research/experiments/structured_study.py"))


def digest(ids):
    return hashlib.sha256(json.dumps(ids).encode()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def audit_input(row, case, manifest, tokenizer):
    """Bind recorded text and prompt tokens to the frozen case, not its ID alone."""
    request = {
        "question": f"Determine whether this target follows: {case['target']}",
        "evidence": case["evidence"],
        "system": manifest["system"],
    }
    require(row["id"] == case["id"], "Input case ID mismatch")
    require(row["request"] == request, "Frozen request mismatch")
    user = f"Evidence:\n{request['evidence']}\n\nQuestion:\n{request['question']}"
    if tokenizer.chat_template:
        expected = tokenizer.apply_chat_template(
            [
                {"role": "system", "content": request["system"]},
                {"role": "user", "content": user},
            ],
            tokenize=True,
            add_generation_prompt=True,
        )
    else:
        expected = tokenizer.encode(f"{request['system']}\n\n{user}\n\nAnswer:")
    require(row["prompt_ids"] == list(expected), "Frozen prompt token mismatch")
    return True


def audit_tokens(row, base):
    require(row["status"] == "complete", "Cannot certify incomplete generation")
    prompt, accepted = list(row["prompt_ids"]), []
    for step in row["steps"]:
        require(step["before_ids"] == accepted, "Step prefix mismatch")
        prefix = accepted + step["opening_ids"]
        cp = step.get("checkpoint")
        for trace in step["trace"]:
            require(trace["prefix_digest"] == digest(prompt + prefix), "Trace prefix mismatch")
            if cp and cp["prefix_digest"] == trace["prefix_digest"]:
                require(cp["prefix_ids"] == prefix, "Scored prefix mismatch")
                roots = dict(cp["root_options"])
                require(len(roots) == len(cp["branches"]), "Root count mismatch")
                for branch in cp["branches"]:
                    require(branch["root"] in roots, "Unproposed root")
                    if "body" not in branch:
                        continue
                    ids = branch["token_ids"]
                    require(ids[0] == branch["root"], "Branch root mismatch")
                    require(ids[1:] == branch["continuation"]["token_ids"], "Tail token mismatch")
                    frame = parse_frame(base.decode(tuple((prefix + ids)[len(accepted) :])))
                    require(
                        frame is not None and frame.body == branch["body"], "Claim text mismatch"
                    )
                    tail_prefix = prefix + [ids[0]]
                    for tail_trace in branch["continuation"]["trace"]:
                        require(
                            tail_trace["prefix_digest"] == digest(prompt + tail_prefix),
                            "Lookahead prefix mismatch",
                        )
                        tail_prefix.append(tail_trace["token"])
                selection = cp.get("selection")
                if selection:
                    require(
                        selection["prefix_digest"] == cp["prefix_digest"],
                        "Selection binding mismatch",
                    )
                    require(
                        trace["committed_ids"][0] == selection["token"], "Committed root mismatch"
                    )
                    if row["mode"] != "soft_step":
                        require(len(trace["committed_ids"]) == 1, "Multi-token root commit")
                    else:
                        selected = next(
                            (b for b in cp["branches"] if b["root"] == selection["token"]), None
                        )
                        if selected:
                            require(
                                trace["committed_ids"] == selected["token_ids"],
                                "Soft-step branch mismatch",
                            )
            prefix.extend(trace.get("committed_ids", []))
        if step.get("finish_reason") == "frame":
            require(prefix[len(accepted) :] == step["token_ids"], "Accepted step mismatch")
            require(base.decode(tuple(step["token_ids"])) == step["text"], "Accepted text mismatch")
            accepted = prefix
    require(accepted == row["accepted_ids"], "Final accepted prefix mismatch")
    final = row["final"]
    require(final["prefix_ids"] == accepted + final["opening_ids"], "Final prefix mismatch")
    ids = tuple(final["candidate"]["token_ids"])
    final_trace = final.get("token_trace")
    if final_trace is not None:
        prefix = list(final["prefix_ids"])
        for trace in final_trace["trace"]:
            require(
                trace["prefix_digest"] == digest(prompt + prefix), "Final trace prefix mismatch"
            )
            prefix.append(trace["token"])
        require(prefix[len(final["prefix_ids"]) :] == list(ids), "Final trace token mismatch")
    raw = base.decode(ids)
    require(
        base.decode(tuple(final["prefix_ids"]) + ids) == final["candidate"]["full_text"],
        "Final token mismatch",
    )
    require(raw == final["decoded_tokens"], "Final raw text mismatch")
    require(
        STUDY["CONTROL"]["FINAL_LABEL"](raw, final["candidate"]["finish_reason"]) == row["label"],
        "Final label mismatch",
    )
    return True


def diagnostics(rows):
    arms = defaultdict(lambda: defaultdict(float))
    confusion = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    strata = defaultdict(lambda: defaultdict(lambda: dict(jobs=0, correct=0)))
    for row in rows:
        arm = arms[row["mode"]]
        if "reference_label" in row:
            confusion[row["mode"]][row["reference_label"]][row.get("label") or "INVALID"] += 1
            for field in ("depth", "motif", "reference_label"):
                if field in row:
                    group = strata[row["mode"]][f"{field}:{row[field]}"]
                    group["jobs"] += 1
                    group["correct"] += (
                        row.get("status") == "complete"
                        and row.get("label") == row["reference_label"]
                    )
        arm["jobs"] += 1
        arm["seconds"] += row.get("seconds", 0)
        for k, v in row.get("work", {}).items():
            arm[k] += v
        for k in ("generated_tokens", "decode_token_slots", "prefill_tokens"):
            arm["final_" + k] += row.get("final", {}).get(k, 0)
        for step in row.get("steps", []):
            oracle = step.get("oracle")
            if oracle:
                arm["accepted_claims"] += 1
                arm["supported_accepted_claims"] += oracle["correct"]
            cp = step.get("checkpoint")
            if not cp:
                continue
            plan = cp.get("selection", {}).get("plan", {})
            arm["checkpoints"] += 1
            arm["nonzero_bias"] += bool(plan.get("bias"))
            arm["max_kl"] = max(arm["max_kl"], plan.get("kl", 0))
            evaluation = cp.get("evaluation")
            if not evaluation:
                continue
            arm["api_calls"] += evaluation["attempts"]
            arm["api_seconds"] += evaluation["seconds"]
            arm["api_input_tokens"] += evaluation["input_tokens"]
            candidates = cp["branches"]
            judgments = evaluation["judgments"]
            for b, j in zip(candidates, judgments, strict=True):
                if b.get("oracle") is None:
                    continue
                y, p = int(b["oracle"]["correct"]), j["support"]
                arm["graded_scores"] += 1
                arm["brier_sum"] += (p - y) ** 2
                arm["true_claims" if y else "false_claims"] += 1
                arm["true_support_sum" if y else "false_support_sum"] += p
            if (
                all(b.get("oracle") is not None for b in candidates)
                and len({b["oracle"]["correct"] for b in candidates}) == 2
            ):
                arm["mixed_batches"] += 1
                jev = max(range(len(candidates)), key=lambda i: judgments[i]["support"])
                ll = max(range(len(candidates)), key=lambda i: candidates[i]["mean_logprob"])
                arm["mixed_jev_top_correct"] += candidates[jev]["oracle"]["correct"]
                arm["mixed_likelihood_top_correct"] += candidates[ll]["oracle"]["correct"]
    for arm in arms.values():
        arm["mean_seconds"] = arm["seconds"] / arm["jobs"]
        for numerator, denominator, name in (
            ("brier_sum", "graded_scores", "brier"),
            ("true_support_sum", "true_claims", "mean_true_support"),
            ("false_support_sum", "false_claims", "mean_false_support"),
        ):
            arm[name] = arm[numerator] / arm[denominator] if arm[denominator] else None
    first = dict(pairs=0, identical=0)
    grouped = defaultdict(dict)
    for row in rows:
        grouped[(row["id"], row["seed"])][row["mode"]] = row
    for group in grouped.values():
        for arm in ("jev", "shuffled", "zero", "soft_step"):
            a, b = group.get("likelihood"), group.get(arm)
            if not a or not b or not a.get("steps") or not b.get("steps"):
                continue
            ca, cb = a["steps"][0].get("checkpoint"), b["steps"][0].get("checkpoint")
            if ca and cb:
                first["pairs"] += 1
                first["identical"] += (
                    ca["prefix_ids"] == cb["prefix_ids"]
                    and ca["root_options"] == cb["root_options"]
                    and [x.get("token_ids") for x in ca["branches"]]
                    == [x.get("token_ids") for x in cb["branches"]]
                )
    return dict(
        arms=dict(arms),
        first_branch_pool_identity=first,
        confusion=json.loads(json.dumps(confusion)),
        strata=json.loads(json.dumps(strata)),
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--split", choices=["development", "test"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    from transformers import AutoTokenizer

    manifest = json.loads((args.manifest / "manifest.json").read_text())
    cases = json.loads((args.manifest / f"{args.split}.json").read_text())
    by_id = {c["id"]: c for c in cases}
    rows = [json.loads(line) for line in args.runs.read_text().splitlines()]
    tokenizer = AutoTokenizer.from_pretrained(
        manifest["model"], revision=manifest["revision"], local_files_only=True
    )
    base = SimpleNamespace(
        decode=lambda ids: tokenizer.decode(
            list(ids), skip_special_tokens=True, clean_up_tokenization_spaces=False
        )
    )
    certified = input_certified = 0
    for row in rows:
        case = by_id[row["id"]]
        require(STUDY["DATA"]["truth"](case) == row["reference_label"], "Reference mismatch")
        if row["status"] == "complete" or row.get("request") is not None:
            input_certified += audit_input(row, case, manifest, tokenizer)
        if row["status"] == "complete":
            certified += audit_tokens(row, base)
        for step in row.get("steps", []):
            for branch in step.get("checkpoint", {}).get("branches", []):
                if branch.get("body"):
                    require(
                        STUDY["DATA"]["grade_claim"](case, branch["body"]) == branch["oracle"],
                        "Oracle mismatch",
                    )
    result = STUDY["summarize"](
        rows,
        cases,
        manifest["seeds"][args.split],
        manifest["arms"],
        bootstrap=5000 if args.split == "test" else 0,
    )
    result.update(
        independent_input_audits=input_certified,
        independent_token_audits=certified,
        diagnostics=diagnostics(rows),
        raw_sha256=STUDY["sha"](args.runs),
        analysis_sha256=STUDY["sha"](Path(__file__)),
    )
    STUDY["write"](args.output, result)
    print(json.dumps({"audited": certified, "recorded": len(rows)}))


if __name__ == "__main__":
    main()
