"""New multiplicatively gated repair branch; frozen backbone and scoped positions."""

import runpy
from contextlib import contextmanager
from pathlib import Path

import torch
from torch import nn

HERE = Path(__file__).resolve().parent
C = runpy.run_path(str(HERE / "common.py"))
B = runpy.run_path(str(HERE.parent / "learned_feedback/bridge.py"))
new_cache = B["new_cache"]


class Repair(nn.Module):
    def __init__(self, width, rank=64):
        super().__init__()
        if type(width) is not int or type(rank) is not int or not 1 <= rank <= width:
            raise ValueError("Invalid repair dimensions")
        self.down = nn.Linear(width, rank, bias=False)
        self.up = nn.Linear(rank, width, bias=False)
        nn.init.zeros_(self.up.weight)

    def forward(self, h, signal):
        # R22 scope passes a two-value tensor; only the explicit gate is used.
        gate = signal[0] if isinstance(signal, torch.Tensor) and signal.ndim else signal
        dtype = h.dtype
        h = h.float()
        scale = h.square().mean(-1, keepdim=True).clamp_min(1e-12).sqrt()
        delta = 0.5 * scale * torch.tanh(self.up(torch.tanh(self.down(h / scale))))
        return (h + gate * delta).to(dtype)


@contextmanager
def scope(model, adapter, gate, *, start, layer=19, trace=None):
    C["gate_value"](gate)
    with B["scope"](model, adapter, [gate, gate], start=start, layer=layer, trace=trace):
        yield
