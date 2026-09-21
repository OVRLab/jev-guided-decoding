"""Real-checkpoint mechanical controls using exact, already received Jev scores."""

import argparse
import hashlib
import json
import os
import runpy
import subprocess
import time
from dataclasses import asdict
from pathlib import Path

from jev_guided_decoding.framing import parse_frame
from jev_guided_decoding.types import Request

FORK = runpy.run_path(str(Path(__file__).with_name("claim_forks.py")))
CONTROL = runpy.run_path(str(Path(__file__).with_name("logit_controller.py")))
ROOT, sha, write_json = FORK["ROOT"], FORK["sha"], FORK["write_json"]
MODES = ("native", "zero", "jev", "shuffled", "synthetic")


def bound_judgments(row):
    if row["status"] != "complete" or row.get("evaluation", {}).get("model") != "jev-1.13.0":
        raise ValueError("Replay requires a successful, exact-model score record")
    roots = [token for token, probability in row["root_options"]]
    if roots != [c["token_ids"][0] for c in row["candidates"]]:
        raise ValueError("Score record branch roots do not match")
    return {c["token_ids"][0]: c["judgment"] for c in row["candidates"]}


def source_hashes():
    hashes = FORK["source_hashes"]()
    for name in ("logit_controller.py", "logit_mechanism.py"):
        path = Path(__file__).with_name(name)
        hashes[str(path.relative_to(ROOT))] = sha(path)
    return hashes


def weight_digest(base):
    import torch

    digest = hashlib.sha256()
    for name, tensor in base.model.state_dict().items():
        digest.update(name.encode())
        digest.update(str((tuple(tensor.shape), str(tensor.dtype))).encode())
        raw = tensor.detach().cpu().contiguous().view(torch.uint8).numpy()
        digest.update(memoryview(raw).cast("B"))
    return digest.hexdigest()


def finish(base, case, accepted, manifest, *, seed):
    """Same explicit final-phase prompt and exact retained tokens in every control."""
    step_text = base.decode(accepted)
    frame = parse_frame(step_text)
    retained = accepted if frame and frame.kind == "step" else ()
    request = Request(
        f"Classify the target: {case['target']}", case["evidence"], manifest["final_system"]
    )
    prompt = base.encode(request)
    control = base.encode_control("\n<final>")
    proposal = base.propose_frames(
        prompt,
        retained + control,
        count=1,
        max_tokens=manifest["final_tokens"],
        seed=seed,
        greedy=True,
        max_seconds=15,
    )
    ids = proposal.candidates[0].token_ids
    if proposal.candidates[0].full_text != base.decode(retained + control + ids):
        raise ValueError("Final model-token provenance mismatch")
    final_text = base.decode(control + ids)
    return {
        "step_text": step_text,
        "step_valid": bool(retained),
        "final_request": asdict(request),
        "final_prompt_ids": prompt,
        "retained_step_ids": retained,
        "final_control_ids": control,
        "final_proposal": asdict(proposal),
        "final_token_ids": ids,
        "final_text": final_text,
        "final_frame_valid": parse_frame(final_text) is not None,
    }


def prepare(args):
    rows = [json.loads(line) for line in args.prior.read_text().splitlines()]
    selected = [r for r in rows if r["status"] == "complete" and "evaluation" in r]
    if len(selected) != 4:
        raise ValueError("Expected the four pre-interruption score batches")
    write_json(
        args.manifest,
        {
            "schema": "logit-mechanism-v1",
            "source_hashes": source_hashes(),
            "source_revision": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "prior_sha256": sha(args.prior),
            "ids": [r["id"] for r in selected],
            "modes": MODES,
            "seed_base": 672919,
            "distribution_draws": 64,
            "stage_seconds": 600,
            "tail_tokens": 32,
            "final_tokens": 64,
            "no_paid_calls": True,
            "final_system": "Use only the supplied original evidence and forward implications. "
            "Any preceding intermediate claim is tentative reasoning, not an additional premise. "
            "Finish the supplied final frame with TRUE if the target follows, "
            "FALSE if its explicit "
            "negation follows, otherwise UNKNOWN. Add a short reason, then close </final>.",
            "purpose": "Mechanism/provenance checks on exposed development prefixes; "
            "replayed scores, not live hosted calls or independent answer-quality evaluation.",
        },
    )


def run(args):
    manifest = json.loads(args.manifest.read_text())
    if manifest["source_hashes"] != source_hashes() or sha(args.prior) != manifest["prior_sha256"]:
        raise ValueError("Frozen source or replay input changed")
    records = [json.loads(line) for line in args.prior.read_text().splitlines()]
    selected = [r for r in records if r["id"] in manifest["ids"]]
    if [r["id"] for r in selected] != manifest["ids"]:
        raise ValueError("Replay row mismatch")
    from jev_guided_decoding.backends.transformers import TransformersBackend

    runtime_class = runpy.run_path(str(Path(__file__).with_name("logit_runtime.py")))[
        "LogitTokenBackend"
    ]
    args.output.mkdir(parents=True, exist_ok=False)
    loaded = time.monotonic()
    base = TransformersBackend.load(
        FORK["GATE"]["MODEL"],
        revision=FORK["GATE"]["REVISION"],
        device="mps",
        temperature=1,
        top_p=1,
        local_files_only=True,
    )
    runtime = runtime_class(base)
    loading = time.monotonic() - loaded
    weights_before = weight_digest(base)
    write_json(
        args.output / "metadata.json",
        {
            "manifest_sha256": sha(args.manifest),
            "model": base.metadata(),
            "loading_seconds": loading,
            "weights_before_sha256": weights_before,
            "paid_calls": 0,
            "replayed_scores": True,
        },
    )
    rows, started = [], time.monotonic()
    with (args.output / "runs.jsonl").open("x") as stream:
        for index, prior in enumerate(selected):
            if time.monotonic() - started >= manifest["stage_seconds"]:
                break
            row = {"id": prior["id"], "status": "started", "modes": []}
            try:
                judgments = bound_judgments(prior)
                prompt, prefix = tuple(prior["prompt_token_ids"]), tuple(prior["prefix_token_ids"])
                if base.encode(Request(**prior["request"])) != prompt:
                    raise ValueError("Replayed prompt tokenization differs")
                rebuilt = tuple(prior["opening_token_ids"]) + tuple(
                    t["token"] for t in prior["prefix_trace"] if "token" in t
                )
                if rebuilt != prefix:
                    raise ValueError("Recorded native prefix provenance failed")
                state = runtime.inspect(prompt, prefix, count=4)
                scored_digest = prior["prefix_trace"][-1]["prefix_digest"]
                if state.prefix_digest != scored_digest or [t for t, p in state.options] != [
                    t for t, p in prior["root_options"]
                ]:
                    raise ValueError("Replayed checkpoint differs")
                row["root_probability_max_difference"] = max(
                    abs(p - old[1])
                    for (t, p), old in zip(state.options, prior["root_options"], strict=True)
                )
                if row["root_probability_max_difference"] > 1e-7:
                    raise ValueError("Replayed native probabilities differ")
                row["checkpoint_prefill_tokens"] = state.prefill_tokens
                row["checkpoint_seconds"] = state.seconds
                native_draws = [
                    runtime.sample(state, {}, seed=seed)[0]
                    for seed in range(manifest["distribution_draws"])
                ]
                # Deliberately consume global/shadow RNG and model work between controls.
                shadow = runtime.lookahead(
                    prompt,
                    prefix,
                    first_token=state.options[0][0],
                    max_tokens=32,
                    seed=888,
                    max_seconds=15,
                )
                row["extra_shadow"] = shadow
                after_shadow = runtime.inspect(prompt, prefix, count=4)
                row["shadow_check_prefill_tokens"] = after_shadow.prefill_tokens
                row["shadow_check_seconds"] = after_shadow.seconds
                row["shadow_distribution_identical"] = bool(
                    state.probabilities.equal(after_shadow.probabilities)
                )
                for mode in MODES:
                    if time.monotonic() - started >= manifest["stage_seconds"]:
                        raise TimeoutError("Mechanism stage time exhausted")
                    chosen = CONTROL["choose"](
                        runtime,
                        after_shadow,
                        judgments,
                        scored_prefix_digest=scored_digest,
                        seed=manifest["seed_base"] + index,
                        mode=mode,
                    )
                    row["modes"].append(chosen)
                    bias = chosen["plan"]["bias"]
                    adjusted = runtime.distribution(after_shadow, bias)
                    mask = after_shadow.probabilities > 0
                    kl = (
                        (
                            adjusted[mask]
                            * (adjusted[mask].log() - after_shadow.probabilities[mask].log())
                        )
                        .sum()
                        .item()
                    )
                    chosen["measured_kl"] = kl
                    if kl > 0.020000001 or abs(kl - chosen["plan"]["kl"]) > 1e-9:
                        raise ValueError("Full-distribution KL check failed")
                    chosen["top_probabilities"] = {
                        token: [p, adjusted[token].item()] for token, p in state.options
                    }
                    chosen["changed_draws_of_64"] = sum(
                        runtime.sample(after_shadow, bias, seed=seed)[0] != native
                        for seed, native in enumerate(native_draws)
                    )
                    if mode == "zero" and chosen["changed_draws_of_64"] != 0:
                        raise ValueError("Zero bias changed sampled root sequence")
                    tail = runtime.lookahead(
                        prompt,
                        prefix,
                        first_token=chosen["token"],
                        max_tokens=manifest["tail_tokens"],
                        seed=manifest["seed_base"] + index,
                        max_seconds=15,
                    )
                    chosen["tail"] = tail
                    accepted = prefix + tuple(tail["token_ids"])
                    chosen["step_token_ids"] = accepted
                    chosen.update(
                        finish(
                            base,
                            prior["case"],
                            accepted,
                            manifest,
                            seed=manifest["seed_base"] + index,
                        )
                    )
                native, zero = row["modes"][:2]
                row["native_zero_paths_identical"] = all(
                    native[key] == zero[key]
                    for key in ("token", "step_token_ids", "final_token_ids")
                )
                if (
                    not row["native_zero_paths_identical"]
                    or not row["shadow_distribution_identical"]
                ):
                    raise ValueError("No-op identity failed")
                row["status"] = "complete"
            except Exception as exc:
                row.update(
                    status="mechanism_error",
                    error_type=type(exc).__name__,
                    error=str(exc),
                    failed_operation_compute_unknown=True,
                )
            stream.write(json.dumps(row, allow_nan=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
            rows.append(row)
            print(
                json.dumps({"done": len(rows), "planned": 4, "status": row["status"]}), flush=True
            )
            if row["status"] != "complete":
                break
    weights_after = weight_digest(base)
    write_json(
        args.output / "summary.json",
        {
            "planned": 4,
            "recorded": len(rows),
            "complete": sum(r["status"] == "complete" for r in rows),
            "weights_after_sha256": weights_after,
            "weights_unchanged": weights_after == weights_before,
            "passed": len(rows) == 4
            and all(r["status"] == "complete" for r in rows)
            and weights_after == weights_before,
            "paid_calls": 0,
            "replayed_scores": True,
            "answer_quality_evaluated": False,
            "seconds": time.monotonic() - started,
            "runs_sha256": sha(args.output / "runs.jsonl"),
        },
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "run"])
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--prior", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args)
    elif args.output is None:
        parser.error("run requires --output")
    else:
        run(args)


if __name__ == "__main__":
    main()
