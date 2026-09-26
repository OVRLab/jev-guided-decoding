"""Reconstruct exact prompts, token decoding, EOS and coverage without inference."""

import argparse
import json
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
C = runpy.run_path(str(HERE / "common.py"))
R = runpy.run_path(str(HERE / "run.py"))


def audit(folder, output):
    from transformers import AutoTokenizer

    m = R["verify"](folder)
    start = json.loads((output / "start.json").read_text())
    if start["manifest_sha256"] != C["sha"](folder / "manifest.json"):
        raise ValueError("Run manifest mismatch")
    cases = {c["id"]: c for c in json.loads((folder / "cases.json").read_text())}
    rows = [json.loads(line) for line in (output / "outputs.jsonl").read_text().splitlines()]
    expected = {(name, ident) for name in m["models"] for ident in cases}
    seen, generated = set(), 0
    for name, config in m["models"].items():
        tok = AutoTokenizer.from_pretrained(
            config["id"], revision=config["revision"], trust_remote_code=False
        )
        hw = json.loads((output / (name + "-hardware.json")).read_text())
        if hw["model"] != config or hw["weights_require_grad"]:
            raise ValueError("Model configuration mismatch")
        eos = set(hw["eos_ids"])
        for r in [row for row in rows if row["model"] == name]:
            pair = (name, r["id"])
            if pair in seen or pair not in expected:
                raise ValueError("Duplicate or unexpected row")
            seen.add(pair)
            case = cases[r["id"]]
            C["verify_readout"](case, r, thinking=config["thinking"])
            kwargs = {"enable_thinking": True} if config["thinking"] else {}
            ids = tok.apply_chat_template(
                [{"role": "user", "content": case["prompt"]}],
                tokenize=True,
                add_generation_prompt=True,
                **kwargs,
            )
            if r["prompt_token_ids"] != ids:
                raise ValueError("Prompt token reconstruction failed")
            if r["status"] in ("input_limit", "generation_error"):
                continue
            tokens = r["generated_token_ids"]
            trimmed, stop = C["trim_ids"](tokens, eos)
            if (
                trimmed != tokens
                or stop != r["finish_reason"]
                or not 0 < len(tokens) <= config["max_new_tokens"]
            ):
                raise ValueError("Generated-token boundary mismatch")
            if stop == "length" and len(tokens) != config["max_new_tokens"]:
                raise ValueError("Unexpected short generation")
            body = tokens[:-1] if tokens[-1] in eos else tokens
            if tok.decode(body, skip_special_tokens=False) != r["raw"]:
                raise ValueError("Generated-token decoding mismatch")
            generated += 1
    if any(row["model"] not in m["models"] for row in rows):
        raise ValueError("Unexpected model")
    return {
        "passed": True,
        "planned": len(expected),
        "received": len(seen),
        "generated": generated,
        "missing": sorted(expected - seen),
        "complete": seen == expected,
        "manifest_sha256": C["sha"](folder / "manifest.json"),
        "output_sha256": C["sha"](output / "outputs.jsonl"),
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--freeze", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--save", type=Path, required=True)
    a = p.parse_args()
    C["dump"](a.save, audit(a.freeze, a.output))
