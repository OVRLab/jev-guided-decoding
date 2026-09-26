"""Device-specific single-memory mechanics, with no task quality or API call."""

import runpy
import time
from pathlib import Path

import torch

HERE = Path(__file__).resolve().parent
R = runpy.run_path(str(HERE / "runtime.py"))
S = runpy.run_path(str(HERE / "single.py"))


def admission(model, memory_ids, positions, repair_ids, *, layer=19, rank=32):
    if (
        not R["valid_ids"](model, repair_ids)
        or len(repair_ids) + 1 > min(4096, model.config.max_position_embeddings)
        or repair_ids[: len(memory_ids)] != memory_ids
        or len(repair_ids) <= len(memory_ids)
    ):
        raise ValueError("Invalid exact-prefix admission inputs")
    before = R["weight_digest"](model)
    device = next(model.parameters()).device
    tick = time.monotonic()
    extracted = R["extract"](model, memory_ids, positions, layer=layer)
    if torch.allclose(extracted["embedding"], extracted["contextual"]):
        raise ValueError("Indistinguishable admission memory types")
    memory, p = S["as_three_slots"](extracted["contextual"], 0.3)
    values = p.tolist()
    torch.manual_seed(3200)
    adapter = R["B"]["Repair"](model.config.hidden_size, rank).to(device).eval()
    x = torch.tensor([repair_ids], device=device)
    with torch.no_grad():
        original = model(x, use_cache=False, logits_to_keep=1).logits
        with R["B"]["scope"](
            model, adapter, memory, values, start=len(repair_ids) - 1, layer=layer
        ):
            initial = model(x, use_cache=False, logits_to_keep=1).logits
        if not torch.equal(initial, original):
            raise ValueError("Initial single-memory identity failed")
        adapter.up.weight.normal_(std=0.01)
        with R["B"]["scope"](
            model, adapter, memory, [1, 1, 1], start=len(repair_ids) - 1, layer=layer
        ):
            off = model(x, use_cache=False, logits_to_keep=1).logits
        token = int(original[0, -1].argmax())
        full_x = torch.tensor([repair_ids + [token]], device=device)
        with R["B"]["scope"](
            model, adapter, memory, values, start=len(repair_ids) - 1, layer=layer
        ):
            full = model(full_x, use_cache=False, logits_to_keep=1).logits
            first = model(
                x, use_cache=True, past_key_values=R["new_cache"](model), logits_to_keep=1
            )
            cached = model(
                full_x[:, -1:],
                use_cache=True,
                past_key_values=first.past_key_values,
                cache_position=torch.tensor([len(repair_ids)], device=device),
                logits_to_keep=1,
            ).logits
    error = float((full - cached).abs().max())
    after = R["weight_digest"](model)
    if (
        not torch.equal(original, off)
        or not torch.isfinite(full).all()
        or not torch.isfinite(cached).all()
        or error > 0.001
        or int(full[0, -1].argmax()) != int(cached[0, -1].argmax())
        or before != after
        or any(p.requires_grad or p.grad is not None for p in model.parameters())
    ):
        raise ValueError("Single-memory cache/off/weight ownership failed")
    R["idle_frozen"](model)
    return dict(
        passed=True,
        device=str(device),
        api_calls=0,
        initial_identity=True,
        off_identity=True,
        cache_max_logit_error=error,
        cache_argmax_equal=True,
        backbone_gradients_absent=True,
        backbone_before=before,
        backbone_after=after,
        memory_shape=list(extracted["contextual"].shape),
        extraction_processed_tokens=extracted["processed_tokens"],
        extraction_seconds=extracted["seconds"],
        seconds=time.monotonic() - tick,
        dummy_adapter_parameters=sum(p.numel() for p in adapter.parameters()),
    )
