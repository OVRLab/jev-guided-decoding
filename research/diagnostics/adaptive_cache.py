"""Numerical diagnostic only; no Jev, selection or held-out quality evaluation."""

import json
import runpy
import sys
import time
from pathlib import Path

import torch

from jev_guided_decoding.backends.transformers import TransformersBackend

ROOT = Path(__file__).resolve().parents[2]
R = runpy.run_path(str(ROOT / "research/iterations/adaptive_attention/runtime.py"))
D = runpy.run_path(str(ROOT / "research/iterations/adaptive_attention/data.py"))
P = runpy.run_path(str(ROOT / "research/iterations/adaptive_attention/policies.py"))
torch.set_num_threads(1)
torch.set_num_interop_threads(1)
out = Path(sys.argv[1])
out.mkdir(exist_ok=False, parents=True)
cases = []
for name in ["development", "admission"]:
    cases += json.loads(
        (ROOT / f"research/protocols/adaptive-attention-v1/{name}.json").read_text()
    )[:3]
for dtype in ["bfloat16", "float32"]:
    base = TransformersBackend.load(
        "ibm-granite/granite-4.0-1b",
        revision="6a7381ba1f54d684ff508d991aeb7dc580157103",
        device="cuda",
        dtype=dtype,
        local_files_only=True,
    )
    runtime = R["Runtime"](base)
    for case in cases:
        e = R["encode"](base.tokenizer, D["public_view"](case), "open_explicit")
        for mode in ["native", "r15"]:
            bias = (
                {}
                if mode == "native"
                else P["token_maps"](
                    P["r15"](),
                    e["span_token_indices"],
                    [float(i % 2 == 0) for i in range(len(case["sources"]))],
                )
            )
            session = runtime.session(e)
            session.generate(2, "check", maps=bias)
            start = time.monotonic()
            a = session.logits(bias)
            ids = torch.tensor([session.ids], device=base.device)
            with (
                torch.inference_mode(),
                runtime.hook.apply(session.ids, query_start=e["query_start"], maps=bias),
            ):
                b = (
                    base.model(
                        input_ids=ids,
                        attention_mask=torch.ones_like(ids),
                        use_cache=False,
                        logits_to_keep=1,
                    )
                    .logits[0, -1]
                    .float()
                )
            torch.cuda.synchronize()
            ap, bp = torch.log_softmax(a.double(), -1), torch.log_softmax(b.double(), -1)
            row = {
                "dtype": dtype,
                "mode": mode,
                "case": case["id"],
                "tokens": len(session.ids),
                "max_difference": float((a - b).abs().max()),
                "mean_difference": float((a - b).abs().mean()),
                "cached_argmax": int(a.argmax()),
                "full_argmax": int(b.argmax()),
                "kl_full_to_cached": float((bp.exp() * (bp - ap)).sum()),
                "cached_top": torch.topk(a, 2).values.tolist(),
                "full_top": torch.topk(b, 2).values.tolist(),
                "seconds": time.monotonic() - start,
            }
            print(json.dumps(row), flush=True)
            with (out / "checks.jsonl").open("a") as f:
                f.write(json.dumps(row) + "\n")
            del a, b, session, ids
    del base, runtime
    torch.cuda.empty_cache()
