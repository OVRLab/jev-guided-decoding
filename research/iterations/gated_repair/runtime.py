"""Auditable serial full-vocabulary generation and supervised frozen-backbone repair."""

import hashlib
import runpy
import time
from contextlib import nullcontext
from pathlib import Path

import torch
import torch.nn.functional as F

B = runpy.run_path(str(Path(__file__).with_name("bridge.py")))


def weight_digest(model):
    digest = hashlib.sha256()
    for name, p in model.state_dict().items():
        digest.update(name.encode())
        digest.update(p.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes())
    return digest.hexdigest()


def generate(model, tok, ids, *, limit, eos, adapter=None, gate=0.5, layer=19, deadline=None):
    if not ids or type(limit) is not int or not 1 <= limit <= 1024 or len(ids) > 8192:
        raise ValueError("Invalid generation request")
    device = next(model.parameters()).device
    pending, accepted, past = list(ids), [], 0
    cache = B["new_cache"](model)
    traces = []
    tick = time.monotonic()
    ctx = (
        B["scope"](model, adapter, gate, start=len(ids) - 1, layer=layer, trace=traces)
        if adapter is not None
        else nullcontext()
    )
    with torch.no_grad(), ctx:
        for _ in range(limit):
            if deadline is not None:
                deadline()
            x = torch.tensor([pending], device=device)
            out = model(
                input_ids=x,
                attention_mask=torch.ones(
                    (1, past + len(pending)), device=device, dtype=torch.long
                ),
                past_key_values=cache,
                use_cache=True,
                cache_position=torch.arange(past, past + len(pending), device=device),
                logits_to_keep=1,
            )
            past += len(pending)
            cache = out.past_key_values
            token = int(out.logits[0, -1].argmax())
            accepted.append(token)
            if token in eos:
                break
            pending = [token]
    body = accepted[:-1] if accepted[-1] in eos else accepted
    return dict(
        prompt_token_ids=list(ids),
        generated_token_ids=accepted,
        text=tok.decode(body, skip_special_tokens=False),
        finish_reason="eos" if accepted[-1] in eos else "length",
        seconds=time.monotonic() - tick,
        forwards=len(accepted),
        processed_tokens=len(ids) + len(accepted) - 1,
        events=traces,
    )


def loss_for(model, adapter, prompt, target, gate, *, layer=19):
    if not prompt or not target or len(prompt) + len(target) > 8192 or len(target) > 768:
        raise ValueError("Invalid or oversized training example")
    x = torch.tensor([prompt + target[:-1]], device=next(model.parameters()).device)
    with B["scope"](model, adapter, gate, start=len(prompt) - 1, layer=layer):
        output = model(x, use_cache=False, logits_to_keep=len(target))
    return F.cross_entropy(output.logits[0].float(), torch.tensor(target, device=x.device))


def admission(model, tok, ids, eos, layer):
    torch.manual_seed(2500)
    adapter = B["Repair"](model.config.hidden_size).to(next(model.parameters()).device)
    x = torch.tensor([ids], device=next(model.parameters()).device)
    with torch.no_grad():
        native = model(x, use_cache=False, logits_to_keep=1).logits
        with B["scope"](model, adapter, 0.7, start=len(ids) - 1, layer=layer):
            zero = model(x, use_cache=False, logits_to_keep=1).logits
    if not torch.equal(native, zero):
        raise ValueError("Initial zero-output parity failure")
    loss_for(model, adapter, ids, [eos[0]], 0.7, layer=layer).backward()
    if not float(adapter.up.weight.grad.abs().sum()) > 0 or any(
        p.requires_grad or p.grad is not None for p in model.parameters()
    ):
        raise ValueError("Gradient ownership failure")
    with torch.no_grad():
        adapter.up.weight.normal_(std=0.01)
        with B["scope"](model, adapter, 0.0, start=len(ids) - 1, layer=layer):
            off = model(x, use_cache=False, logits_to_keep=1).logits
        token = int(native[0, -1].argmax())
        full_x = torch.tensor([ids + [token]], device=x.device)
        with B["scope"](model, adapter, 0.7, start=len(ids) - 1, layer=layer):
            full = model(full_x, use_cache=False, logits_to_keep=1).logits
            first = model(
                x,
                use_cache=True,
                past_key_values=B["new_cache"](model),
                cache_position=torch.arange(len(ids), device=x.device),
                logits_to_keep=1,
            )
            cached = model(
                full_x[:, -1:],
                use_cache=True,
                past_key_values=first.past_key_values,
                cache_position=torch.tensor([len(ids)], device=x.device),
                logits_to_keep=1,
            ).logits
    if not torch.equal(native, off):
        raise ValueError("Trained gate-zero parity failure")
    # BF16 kernel dispatch can differ between full and single-token matrix shapes.
    error = float((full - cached).abs().max())
    if error > 0.125 or int(full[0, -1].argmax()) != int(cached[0, -1].argmax()):
        raise ValueError(f"Cached/full admission failure: {error}")
    return dict(
        passed=True,
        zero_gate_exact=True,
        zero_initial_exact=True,
        base_gradients_absent=True,
        cached_full_max_abs_logit_difference=error,
        cached_full_argmax_equal=True,
        note="BF16 tolerance 0.125 and same argmax on admission fixture; not bitwise parity",
    )
