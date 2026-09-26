"""Serial exact-prefix generation and supervised training for the R29 branch."""

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
    for name, parameter in model.state_dict().items():
        digest.update(name.encode())
        digest.update(parameter.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes())
    return digest.hexdigest()


def generate(
    model,
    tok,
    ids,
    *,
    limit,
    eos,
    adapter=None,
    memory=None,
    probabilities=None,
    layer=19,
    deadline=None,
):
    if not ids or type(limit) is not int or not 1 <= limit <= 128 or len(ids) > 2048:
        raise ValueError("Invalid generation limits")
    device = next(model.parameters()).device
    pending, accepted, past = list(ids), [], 0
    cache, traces = B["new_cache"](model), []
    context = (
        B["scope"](
            model, adapter, memory, probabilities, start=len(ids) - 1, layer=layer, trace=traces
        )
        if adapter is not None
        else nullcontext()
    )
    tick = time.monotonic()
    with torch.no_grad(), context:
        for _ in range(limit):
            if deadline:
                deadline()
            out = model(
                input_ids=torch.tensor([pending], device=device),
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
        processed_tokens=len(ids) + len(accepted) - 1,
        events=traces,
    )


def loss_for(model, adapter, prompt, target, memory, probabilities, *, layer=19):
    if not prompt or not target or len(prompt) + len(target) > 2048 or len(target) > 256:
        raise ValueError("Oversized or empty training example")
    x = torch.tensor([prompt + target[:-1]], device=next(model.parameters()).device)
    with B["scope"](model, adapter, memory, probabilities, start=len(prompt) - 1, layer=layer):
        out = model(x, use_cache=False, logits_to_keep=len(target))
    return F.cross_entropy(out.logits[0].float(), torch.tensor(target, device=x.device))


def admission(model, tok, case, eos, *, layer=19, rank=32):
    torch.manual_seed(2900)
    device = next(model.parameters()).device
    adapter = B["Repair"](model.config.hidden_size, rank).to(device)
    memory = B["memory_for"](model, tok, case, "1. kitchen\n2. office\n3. garage")
    ids = tok.apply_chat_template(
        [dict(role="user", content=case["prompt"])], tokenize=True, add_generation_prompt=True
    )
    x = torch.tensor([ids], device=device)
    with torch.no_grad():
        native = model(x, use_cache=False, logits_to_keep=1).logits
        with B["scope"](model, adapter, memory, [0.2, 0.6, 0.9], start=len(ids) - 1, layer=layer):
            zero = model(x, use_cache=False, logits_to_keep=1).logits
    if not torch.equal(native, zero):
        raise ValueError("Initial parity failed")
    loss_for(model, adapter, ids, [eos[0]], memory, [0.2, 0.6, 0.9], layer=layer).backward()
    if not float(adapter.up.weight.grad.abs().sum()) > 0 or any(
        p.requires_grad or p.grad is not None for p in model.parameters()
    ):
        raise ValueError("Gradient ownership failed")
    with torch.no_grad():
        adapter.up.weight.normal_(std=0.01)
        with B["scope"](model, adapter, memory, [1, 1, 1], start=len(ids) - 1, layer=layer):
            off = model(x, use_cache=False, logits_to_keep=1).logits
        token = int(native[0, -1].argmax())
        full_x = torch.tensor([ids + [token]], device=device)
        with B["scope"](model, adapter, memory, [0.2, 0.6, 0.9], start=len(ids) - 1, layer=layer):
            full = model(full_x, use_cache=False, logits_to_keep=1).logits
            first = model(
                x, use_cache=True, past_key_values=B["new_cache"](model), logits_to_keep=1
            )
            cached = model(
                full_x[:, -1:],
                use_cache=True,
                past_key_values=first.past_key_values,
                logits_to_keep=1,
            ).logits
    error = float((full - cached).abs().max())
    if (
        not torch.equal(native, off)
        or error > 0.001
        or int(full[0, -1].argmax()) != int(cached[0, -1].argmax())
    ):
        raise ValueError(f"Off/cache parity failed: {error}")
    return dict(
        passed=True,
        initial_identity=True,
        off_identity=True,
        backbone_gradients_absent=True,
        cache_max_logit_error=error,
        cache_argmax_equal=True,
        trainable_parameters=sum(p.numel() for p in adapter.parameters()),
    )
