"""Small conditional residual intervention; original decoder weights stay frozen."""

import math
import runpy
from contextlib import contextmanager
from pathlib import Path

import torch
from torch import nn
from transformers.modeling_utils import ALL_ATTENTION_FUNCTIONS

# Reuse the documented Transformers 4.57.1 empty-attention-cache repair.
new_cache = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "adaptive_attention/attention.py")
)["new_cache"]


class Bridge(nn.Module):
    def __init__(self, width, rank=16):
        super().__init__()
        if type(width) is not int or type(rank) is not int or not 1 <= rank <= width:
            raise ValueError("Invalid bridge dimensions")
        self.down = nn.Linear(width, rank, bias=False)
        self.condition = nn.Linear(2, rank, bias=False)
        self.up = nn.Linear(rank, width, bias=False)
        nn.init.zeros_(self.up.weight)

    def forward(self, h, feedback):
        scale = h.square().mean(-1, keepdim=True).clamp_min(1e-12).sqrt()
        features = self.down(h / scale) + self.condition(2 * feedback - 1)
        return h + 0.1 * scale * torch.tanh(self.up(torch.tanh(features)))


@contextmanager
def scope(model, adapter, feedback, *, start, layer=19, trace=None):
    if (
        type(start) is not int
        or start < 0
        or type(layer) is not int
        or not 0 <= layer < len(model.model.layers)
        or len(feedback) != 2
        or any(
            type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 1 for v in feedback
        )
    ):
        raise ValueError("Invalid bridge scope")
    block = model.model.layers[layer]
    original = ALL_ATTENTION_FUNCTIONS["sdpa"]
    if (
        getattr(model, "_jev_feedback_active", False)
        or getattr(original, "_r17_controlled", False)
        or getattr(original, "_r18_controlled", False)
        or block._forward_hooks
    ):
        raise RuntimeError("Model intervention already active")
    parameter = next(adapter.parameters())
    signal = torch.tensor(feedback, device=parameter.device, dtype=parameter.dtype)
    model._jev_feedback_active = True

    def modify(module, args, kwargs, output):
        h = output[0]
        if h.shape[0] != 1:
            raise ValueError("Prototype owns one request at a time")
        positions = kwargs.get("cache_position")
        if positions is None or positions.numel() != h.shape[1]:
            raise ValueError("Explicit cache positions required")
        selected = positions >= start
        if not selected.any():
            return output
        result = h.clone()
        result[:, selected] = adapter(h[:, selected], signal)
        if trace is not None:
            delta = result[:, selected] - h[:, selected]
            trace.append(
                dict(
                    layer=layer,
                    positions=positions[selected].detach().cpu().tolist(),
                    relative_delta=float(
                        (delta.norm() / h[:, selected].norm().clamp_min(1e-12)).detach()
                    ),
                    feedback=list(feedback),
                )
            )
        return (result, *output[1:])

    handle = None
    try:
        handle = block.register_forward_hook(modify, with_kwargs=True)
        yield
    finally:
        if handle is not None:
            handle.remove()
        delattr(model, "_jev_feedback_active")
