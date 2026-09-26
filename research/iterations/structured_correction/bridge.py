"""Slot-conditioned internal repair with original backbone weights frozen."""

import math
import runpy
from contextlib import contextmanager
from pathlib import Path

import torch
from torch import nn

C = runpy.run_path(str(Path(__file__).with_name("common.py")))
B = runpy.run_path(str(Path(__file__).resolve().parents[1] / "learned_feedback/bridge.py"))
new_cache = B["new_cache"]


class Repair(nn.Module):
    def __init__(self, width, rank=32):
        super().__init__()
        if type(width) is not int or type(rank) is not int or not 1 <= rank <= width:
            raise ValueError("Invalid repair dimensions")
        self.down = nn.Linear(width, rank, bias=False)
        self.key = nn.Linear(width, rank, bias=False)
        self.value = nn.Linear(width, rank, bias=False)
        self.up = nn.Linear(rank, width, bias=False)
        nn.init.zeros_(self.up.weight)

    def forward(self, h, memory, probabilities):
        dtype, raw = h.dtype, h.float()
        scale = raw.square().mean(-1, keepdim=True).clamp_min(1e-12).sqrt()
        m = memory.float()
        m = m / m.square().mean(-1, keepdim=True).clamp_min(1e-12).sqrt()
        q = self.down(raw / scale)
        weights = torch.softmax(q @ self.key(m).T / math.sqrt(q.shape[-1]), dim=-1)
        values = (1 - probabilities[:, None]) * torch.tanh(self.value(m))
        condition = weights @ values
        delta = 0.5 * scale * torch.tanh(self.up(torch.tanh(q) * condition))
        return (raw + delta).to(dtype)


@contextmanager
def scope(model, adapter, memory, probabilities, *, start, layer=19, trace=None):
    values = C["probabilities"](probabilities)
    if memory.shape != (3, adapter.down.in_features) or not torch.isfinite(memory).all():
        raise ValueError("Invalid feedback memory")
    if memory.requires_grad:
        raise ValueError("Feedback memory must be frozen")

    class Bound(nn.Module):
        def __init__(self):
            super().__init__()
            self.adapter = adapter
            self.register_buffer("memory", memory.detach())
            self.register_buffer("scores", torch.tensor(values, device=memory.device))

        def forward(self, h, _unused):
            return self.adapter(h, self.memory, self.scores)

    events = [] if trace is not None else None
    try:
        with B["scope"](model, Bound(), [0.5, 0.5], start=start, layer=layer, trace=events):
            yield
    finally:
        if trace is not None:
            trace.extend({**event, "feedback": values} for event in events)


def memory_for(model, tok, case, draft):
    """Encode actual question/answer text spans; no reference or extra model pass."""
    C["validate_case"](case)
    spans = C["fields"](draft)
    embed = model.get_input_embeddings()
    with torch.no_grad():
        vectors = []
        for i, question in enumerate(case["questions"]):
            text = question + "\nDraft answer: " + spans.get(i + 1, "(missing)")
            ids = tok.encode(text, add_special_tokens=False)
            vectors.append(embed(torch.tensor(ids, device=embed.weight.device)).float().mean(0))
        return torch.stack(vectors).detach()
