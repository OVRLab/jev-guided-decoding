"""Non-mutating native likelihood observation around the frozen R27 runtime."""

import math
import runpy
from pathlib import Path

import torch

BASE = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "benchmark_execution_v2/runtime.py")
)


def generate(model, tokenizer, prompt, *, observe=False, **kwargs):
    observed = []

    def collect(module, args, output):
        logits = output.logits[0, -1].float()
        token = int(logits.argmax())
        observed.append((token, float(torch.log_softmax(logits, dim=-1)[token])))

    hook = model.register_forward_hook(collect) if observe else None
    try:
        rows, work = BASE["generate_batch"](model, tokenizer, [prompt], **kwargs)
    finally:
        if hook is not None:
            hook.remove()
    row = rows[0]
    if observe:
        if [i for i, _ in observed] != row["generated_token_ids"]:
            raise ValueError("Likelihood observations disagree with generated tokens")
        values = [p for i, p in observed if i not in kwargs["eos"]]
        if any(not math.isfinite(p) or p > 0 for _, p in observed):
            raise ValueError("Nonfinite native log probability")
        row["log_probabilities"] = [p for _, p in observed]
        row["mean_log_probability"] = sum(values) / len(values) if values else None
    return row, work
