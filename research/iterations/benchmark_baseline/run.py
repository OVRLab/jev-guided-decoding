"""Serial native-baseline runner. Does not load reference answers or Jev keys."""

import argparse
import gc
import json
import os
import platform
import runpy
import time
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
C = runpy.run_path(str(HERE / "common.py"))
P = runpy.run_path(str(HERE / "prepare.py"))


def now():
    return datetime.now(UTC).isoformat()


def append(path, row):
    with path.open("a") as stream:
        stream.write(json.dumps(row, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def verify(folder):
    m = json.loads((folder / "manifest.json").read_text())
    if m["sources"] != P["sources"]():
        raise ValueError("Scientific source freeze mismatch")
    C["verify_files"](folder, m["datasets"])
    return m


def run(folder, output):
    import torch
    import transformers
    from huggingface_hub import snapshot_download
    from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig

    m = verify(folder)
    cases = json.loads((folder / "cases.json").read_text())
    for case in cases:
        C["validate_case"](case)
    if not torch.cuda.is_available():
        raise ValueError("Frozen R23 hardware requires CUDA")
    output.mkdir(parents=True, exist_ok=False)
    C["dump"](
        output / "start.json", {"at": now(), "manifest_sha256": C["sha"](folder / "manifest.json")}
    )
    started = time.monotonic()
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    for name, config in m["models"].items():
        try:
            load_start = time.monotonic()
            local = Path(
                snapshot_download(
                    config["id"],
                    revision=config["revision"],
                    allow_patterns=["*.json", "*.jinja", "*.txt", "*.safetensors"],
                )
            )
            tok = AutoTokenizer.from_pretrained(local, trust_remote_code=False)
            model = (
                AutoModelForCausalLM.from_pretrained(
                    local, trust_remote_code=False, dtype=torch.bfloat16, attn_implementation="sdpa"
                )
                .to("cuda")
                .eval()
            )
            model.requires_grad_(False)
            generation = GenerationConfig.from_pretrained(local)
            generation.update(
                **{
                    k: config[k]
                    for k in ("do_sample", "temperature", "top_p", "top_k", "max_new_tokens")
                    if k in config
                }
            )
            generation.use_cache = True
            eos = generation.eos_token_id
            eos = {eos} if isinstance(eos, int) else set(eos)
            generation.pad_token_id = tok.pad_token_id or min(eos)
            C["dump"](
                output / (name + "-hardware.json"),
                {
                    "at": now(),
                    "model": config,
                    "parameters": sum(p.numel() for p in model.parameters()),
                    "python": platform.python_version(),
                    "torch": torch.__version__,
                    "transformers": transformers.__version__,
                    "gpu": torch.cuda.get_device_name(),
                    "load_and_hash_seconds": time.monotonic() - load_start,
                    "files": {p.name: C["sha"](p) for p in sorted(local.iterdir()) if p.is_file()},
                    "generation_config": generation.to_dict(),
                    "eos_ids": sorted(eos),
                    "weights_require_grad": any(p.requires_grad for p in model.parameters()),
                },
            )
        except Exception as e:
            append(
                output / "events.jsonl",
                {
                    "model": name,
                    "status": "load_error",
                    "error_type": type(e).__name__,
                    "message": str(e),
                    "at": now(),
                },
            )
            raise
        for case in cases:
            if time.monotonic() - started >= m["max_seconds"]:
                raise TimeoutError("Stage deadline; unfinished cases remain missing")
            row = {
                "id": case["id"],
                "task": case["task"],
                "family": case["family"],
                "model": name,
                "prompt_sha256": C["digest_text"](case["prompt"]),
                "at": now(),
            }
            append(output / "events.jsonl", {**row, "status": "started"})
            try:
                kwargs = {"enable_thinking": True} if config["thinking"] else {}
                ids = tok.apply_chat_template(
                    [{"role": "user", "content": case["prompt"]}],
                    tokenize=True,
                    add_generation_prompt=True,
                    **kwargs,
                )
                if len(ids) > m["max_input_tokens"]:
                    row.update(status="input_limit", prompt_token_ids=ids)
                else:
                    torch.manual_seed(m["seed"])
                    torch.cuda.manual_seed_all(m["seed"])
                    x = torch.tensor([ids], device="cuda")
                    torch.cuda.reset_peak_memory_stats()
                    torch.cuda.synchronize()
                    t0 = time.monotonic()
                    with torch.inference_mode():
                        answer = model.generate(
                            input_ids=x,
                            attention_mask=torch.ones_like(x),
                            generation_config=generation,
                        )
                    torch.cuda.synchronize()
                    seconds = time.monotonic() - t0
                    if answer[0, : len(ids)].tolist() != ids:
                        raise ValueError("Generation altered input prefix")
                    tokens, finish = C["trim_ids"](answer[0, len(ids) :].tolist(), eos)
                    body = tokens[:-1] if tokens and tokens[-1] in eos else tokens
                    raw = tok.decode(body, skip_special_tokens=False)
                    final, status = C["final_text"](raw, thinking=config["thinking"])
                    row.update(
                        status=status,
                        prompt_token_ids=ids,
                        generated_token_ids=tokens,
                        raw=raw,
                        final=final,
                        finish_reason=finish,
                        seconds=seconds,
                        peak_allocated_bytes=torch.cuda.max_memory_allocated(),
                    )
            except Exception as e:
                row.update(status="generation_error", error_type=type(e).__name__, message=str(e))
                append(output / "outputs.jsonl", row)
                raise
            append(output / "outputs.jsonl", row)
            print(
                json.dumps(
                    {k: row.get(k) for k in ("model", "id", "status", "finish_reason", "seconds")}
                ),
                flush=True,
            )
        del model, tok
        gc.collect()
        torch.cuda.empty_cache()
    C["dump"](
        output / "completion.json",
        {
            "at": now(),
            "status": "completed",
            "seconds": time.monotonic() - started,
            "planned_outputs": len(cases) * len(m["models"]),
        },
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--freeze", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    run(a.freeze, a.output)
