"""Isolated judge process: reads only anonymous packets, records raw outputs once."""

import argparse
import hashlib
import json
import platform
import runpy
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
J = runpy.run_path(str(HERE / "judge.py"))


def record(p, input_ids, output_ids, text, seconds):
    try:
        result = J["parse"](text) if len(output_ids) < 128 else None
    except ValueError:
        result = None
    return dict(
        id=p["id"],
        packet_digest=p["packet_digest"],
        result=result,
        budget_exhausted=len(output_ids) >= 128,
        raw_text=text,
        input_ids=input_ids,
        output_ids=output_ids,
        seconds=seconds,
        prompt_ids_sha256=hashlib.sha256(json.dumps(input_ids).encode()).hexdigest(),
    )


def run(packets_path, output_path, *, device="cuda"):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    if output_path.exists():
        raise FileExistsError("Judge output already exists; never replay an attempted packet")
    packets = json.loads(packets_path.read_text())
    if len({p["id"] for p in packets}) != len(packets):
        raise ValueError("Duplicate opaque IDs")
    for p in packets:
        if J["digest"](p["packet"]) != p["packet_digest"]:
            raise ValueError("Packet digest mismatch")
        J["messages"](p["packet"])
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.manual_seed(20230923)
    tok = AutoTokenizer.from_pretrained(
        J["MODEL"], revision=J["REVISION"], local_files_only=True, trust_remote_code=False
    )
    model = (
        AutoModelForCausalLM.from_pretrained(
            J["MODEL"],
            revision=J["REVISION"],
            local_files_only=True,
            trust_remote_code=False,
            dtype=torch.bfloat16,
            attn_implementation="sdpa",
        )
        .to(device)
        .eval()
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    meta = dict(
        model=J["MODEL"],
        revision=J["REVISION"],
        dtype="bfloat16",
        device=device,
        python=platform.python_version(),
        torch=torch.__version__,
        rubric_sha256=hashlib.sha256(J["RUBRIC"].encode()).hexdigest(),
        packets_sha256=hashlib.sha256(packets_path.read_bytes()).hexdigest(),
        max_new_tokens=128,
        greedy=True,
        enable_thinking=False,
    )
    output_path.with_suffix(".metadata.json").write_text(json.dumps(meta, indent=2) + "\n")
    began = time.monotonic()
    with output_path.open("x") as f, output_path.with_suffix(".starts.jsonl").open("x") as starts:
        for i, p in enumerate(packets):
            if time.monotonic() - began > 9000:
                raise TimeoutError("Judge process limit")
            rendered = tok.apply_chat_template(
                J["messages"](p["packet"]),
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False,
            )
            inputs = tok(rendered, return_tensors="pt", add_special_tokens=False).to(device)
            ids = inputs["input_ids"][0].tolist()
            if len(ids) > 8192:
                raise ValueError("Judge context limit; no truncation")
            starts.write(json.dumps(dict(id=p["id"], packet_digest=p["packet_digest"])) + "\n")
            starts.flush()
            torch.cuda.synchronize() if device == "cuda" else None
            start = time.monotonic()
            with torch.inference_mode():
                out = model.generate(
                    **inputs,
                    do_sample=False,
                    max_new_tokens=128,
                    pad_token_id=tok.eos_token_id,
                    temperature=None,
                    top_p=None,
                    top_k=None,
                )
            torch.cuda.synchronize() if device == "cuda" else None
            generated = out[0, len(ids) :].tolist()
            text = tok.decode(
                generated, skip_special_tokens=True, clean_up_tokenization_spaces=False
            )
            row = record(p, ids, generated, text, time.monotonic() - start)
            f.write(json.dumps(row) + "\n")
            f.flush()
            if i % 20 == 0:
                print(json.dumps(dict(graded=i + 1, total=len(packets))), flush=True)
    output_path.with_suffix(".complete.json").write_text(
        json.dumps(
            dict(
                packets=len(packets),
                outputs_sha256=hashlib.sha256(output_path.read_bytes()).hexdigest(),
                completed_at=__import__("datetime")
                .datetime.now(__import__("datetime").timezone.utc)
                .isoformat(),
            )
        )
        + "\n"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packets", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()
    run(args.packets, args.output, device=args.device)


if __name__ == "__main__":
    main()
