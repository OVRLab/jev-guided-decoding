"""Native/intervened precision diagnostic on three registered training prompts only."""

import argparse
import gc
import json
import runpy
from pathlib import Path


def run(folder, output):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    here = Path(__file__).resolve().parent
    c = runpy.run_path(str(here / "common.py"))
    r = runpy.run_path(str(here / "runtime.py"))
    m = c["verify"](folder)
    output.mkdir(parents=True, exist_ok=False)
    cases = [v for v in json.loads((folder / "cases.json").read_text()) if v["split"] == "train"][
        :3
    ]
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    tok = AutoTokenizer.from_pretrained(m["model"], revision=m["revision"], trust_remote_code=False)
    records = []
    for name, dtype in [("bfloat16", torch.bfloat16), ("float32", torch.float32)]:
        model = (
            AutoModelForCausalLM.from_pretrained(
                m["model"],
                revision=m["revision"],
                dtype=dtype,
                attn_implementation="sdpa",
                trust_remote_code=False,
            )
            .to("cuda")
            .eval()
            .requires_grad_(False)
        )
        torch.manual_seed(2500)
        adapter = r["B"]["Repair"](model.config.hidden_size).to("cuda")
        with torch.no_grad():
            adapter.up.weight.normal_(std=0.01)
        for case in cases:
            ids = tok.apply_chat_template(
                [dict(role="user", content=case["prompt"])],
                tokenize=True,
                add_generation_prompt=True,
            )
            row = dict(
                id=case["id"],
                precision=name,
                native=r["comparison"](model, ids),
                intervened=r["comparison"](model, ids, adapter, layer=m["layer"]),
            )
            c["dump"](output / f"{name}-{len(records)}.json", row)
            records.append(row)
            print(json.dumps(row), flush=True)
        del model, adapter
        gc.collect()
        torch.cuda.empty_cache()
    passed = all(
        x[k]["allclose"] and x[k]["argmax_equal"]
        for x in records
        if x["precision"] == "float32"
        for k in ("native", "intervened")
    )
    c["dump"](
        output / "summary.json",
        dict(
            passed=passed,
            records=records,
            atol=1e-4,
            rtol=1e-4,
            note="BF16 diagnostic only; all FP32 native/intervened fixtures must pass",
        ),
    )
    if not passed:
        raise ValueError("Float32 diagnostic failed; do not start study")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--freeze", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    run(a.freeze, a.output)
