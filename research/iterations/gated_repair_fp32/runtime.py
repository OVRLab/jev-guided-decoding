"""Unchanged R25 runtime, with strict full-precision numerical admission."""

import runpy
from pathlib import Path

import torch

BASE = runpy.run_path(str(Path(__file__).resolve().parents[1] / "gated_repair/runtime.py"))
generate, loss_for, weight_digest, B = (
    BASE[k] for k in ("generate", "loss_for", "weight_digest", "B")
)
ADMISSION_ATOL = ADMISSION_RTOL = 1e-4


def comparison(model, ids, adapter=None, gate=0.7, layer=19):
    from contextlib import nullcontext

    x = torch.tensor([ids], device=next(model.parameters()).device)
    context = (
        B["scope"](model, adapter, gate, start=len(ids) - 1, layer=layer)
        if adapter is not None
        else nullcontext()
    )
    with torch.no_grad(), context:
        first = model(
            x,
            use_cache=True,
            past_key_values=B["new_cache"](model),
            cache_position=torch.arange(len(ids), device=x.device),
            logits_to_keep=1,
        )
        token = int(first.logits[0, -1].argmax())
        full_x = torch.tensor([ids + [token]], device=x.device)
        full = model(full_x, use_cache=False, logits_to_keep=1).logits
        cached = model(
            full_x[:, -1:],
            use_cache=True,
            past_key_values=first.past_key_values,
            cache_position=torch.tensor([len(ids)], device=x.device),
            logits_to_keep=1,
        ).logits
    return dict(
        max_abs=float((full - cached).abs().max()),
        argmax_equal=int(full[0, -1].argmax()) == int(cached[0, -1].argmax()),
        allclose=bool(torch.allclose(full, cached, atol=ADMISSION_ATOL, rtol=ADMISSION_RTOL)),
    )


def admission(model, tok, ids, eos, layer):
    if next(model.parameters()).dtype != torch.float32:
        raise ValueError("Full precision admission required")
    torch.manual_seed(2500)
    adapter = B["Repair"](model.config.hidden_size).to(next(model.parameters()).device)
    x = torch.tensor([ids], device=next(model.parameters()).device)
    with torch.no_grad():
        native = model(x, use_cache=False, logits_to_keep=1).logits
        with B["scope"](model, adapter, 0.7, start=len(ids) - 1, layer=layer):
            zero = model(x, use_cache=False, logits_to_keep=1).logits
    if not torch.equal(native, zero):
        raise ValueError("Initial parity failure")
    loss_for(model, adapter, ids, [eos[0]], 0.7, layer=layer).backward()
    if not float(adapter.up.weight.grad.abs().sum()) > 0 or any(
        p.requires_grad or p.grad is not None for p in model.parameters()
    ):
        raise ValueError("Gradient ownership failure")
    with torch.no_grad():
        adapter.up.weight.normal_(std=0.01)
        with B["scope"](model, adapter, 0.0, start=len(ids) - 1, layer=layer):
            off = model(x, use_cache=False, logits_to_keep=1).logits
    if not torch.equal(native, off):
        raise ValueError("Gate-zero identity failure")
    result = comparison(model, ids, adapter, 0.7, layer)
    if not result["allclose"] or not result["argmax_equal"]:
        raise ValueError(f"Float32 cached/full admission failure: {result}")
    return dict(
        passed=True,
        zero_gate_exact=True,
        zero_initial_exact=True,
        base_gradients_absent=True,
        precision="float32",
        atol=ADMISSION_ATOL,
        rtol=ADMISSION_RTOL,
        comparison=result,
    )
