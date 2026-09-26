"""Device-specific mechanical checks on an exposed draft; no quality inference."""

import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
M = runpy.run_path(str(HERE / "memory.py"))


def admission(model, tok, case, native, eos, *, layer=19, rank=32):
    import torch

    R = runpy.run_path(str(HERE.parent / "structured_correction/runtime.py"))
    if len(eos) != 1:
        raise ValueError("Admission requires one EOS")
    before = R["weight_digest"](model)
    device = next(model.parameters()).device
    aligned = M["positions_for"](tok, case, native, eos=eos[0])
    memory = M["memories"](model, aligned["ids"], aligned["slots"], layer=layer)
    if (
        memory["contextual"].shape != memory["embedding"].shape
        or torch.allclose(memory["contextual"], memory["embedding"])
        or any(memory[k].requires_grad for k in ("contextual", "embedding"))
    ):
        raise ValueError("Invalid or indistinguishable admission memories")
    ids = M["C"]["repair_prefix"](tok, native["prompt_token_ids"], native["generated_token_ids"])
    torch.manual_seed(3100)
    adapter = R["B"]["Repair"](model.config.hidden_size, rank).to(device)
    x = torch.tensor([ids], device=device)
    values = [0.2, 0.6, 0.9]
    with torch.no_grad():
        original = model(x, use_cache=False, logits_to_keep=1).logits
        with R["B"]["scope"](
            model, adapter, memory["contextual"], values, start=len(ids) - 1, layer=layer
        ):
            initial = model(x, use_cache=False, logits_to_keep=1).logits
    if not torch.equal(initial, original):
        raise ValueError("Contextual initial identity failed")
    R["loss_for"](
        model, adapter, ids, [eos[0]], memory["contextual"], values, layer=layer
    ).backward()
    if not float(adapter.up.weight.grad.abs().sum()) > 0 or any(
        p.grad is not None or p.requires_grad for p in model.parameters()
    ):
        raise ValueError("Contextual gradient ownership failed")
    with torch.no_grad():
        adapter.up.weight.normal_(std=0.01)
        with R["B"]["scope"](
            model, adapter, memory["contextual"], [1, 1, 1], start=len(ids) - 1, layer=layer
        ):
            off = model(x, use_cache=False, logits_to_keep=1).logits
        token = int(original[0, -1].argmax())
        full_x = torch.tensor([ids + [token]], device=device)
        with R["B"]["scope"](
            model, adapter, memory["contextual"], values, start=len(ids) - 1, layer=layer
        ):
            full = model(full_x, use_cache=False, logits_to_keep=1).logits
            first = model(
                x, use_cache=True, past_key_values=R["B"]["new_cache"](model), logits_to_keep=1
            )
            cached = model(
                full_x[:, -1:],
                use_cache=True,
                past_key_values=first.past_key_values,
                logits_to_keep=1,
            ).logits
    error = float((full - cached).abs().max())
    if (
        not torch.equal(off, original)
        or error > 0.001
        or int(full[0, -1].argmax()) != int(cached[0, -1].argmax())
        or R["weight_digest"](model) != before
        or any(b._forward_hooks for b in model.model.layers)
        or getattr(model, "_jev_feedback_active", False)
    ):
        raise ValueError("Contextual off/cache identity or cleanup failed")
    return dict(
        passed=True,
        device=str(device),
        case_id=case["id"],
        api_calls=0,
        initial_identity=True,
        off_identity=True,
        backbone_gradients_absent=True,
        cache_argmax_equal=True,
        cache_max_logit_error=error,
        extraction_processed_tokens=memory["processed_tokens"],
        extraction_seconds=memory["seconds"],
        contextual_memory_shape=list(memory["contextual"].shape),
        parameters=sum(p.numel() for p in adapter.parameters()),
        backbone_before=before,
        backbone_after=before,
    )
