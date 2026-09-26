"""Exact-prefix serial decoding and supervised adapter loss for the R22 pilot."""

import runpy
import time
from contextlib import nullcontext
from pathlib import Path

import torch
import torch.nn.functional as F

B = runpy.run_path(str(Path(__file__).with_name("bridge.py")))
FINAL_SYSTEM = (
    "The intermediate courier-name phase is finished. For this final phase, answer "
    "the badge-color question using the supplied records. Return only the color, "
    "without a courier name or explanation."
)
COLORS = {"red", "blue", "green", "yellow", "orange", "purple", "black", "white"}


def final_prefix(tokenizer, prompt_ids, draft_ids, question):
    end = tokenizer.convert_tokens_to_ids("<|end_of_text|>")
    closure = [] if draft_ids and draft_ids[-1] == end else [end]
    suffix = (
        "\n<|start_of_role|>system<|end_of_role|>"
        + FINAL_SYSTEM
        + "<|end_of_text|>\n<|start_of_role|>user<|end_of_role|>"
        + question
        + "<|end_of_text|>\n<|start_of_role|>assistant<|end_of_role|>"
    )
    framing = closure + tokenizer.encode(suffix, add_special_tokens=False)
    return {"ids": list(prompt_ids) + list(draft_ids) + framing, "framing_ids": framing}


def grade(reference, text):
    answer = text.strip().rstrip(".").casefold()
    return {"correct": answer == reference, "valid_color": answer in COLORS}


def generate(base, ids, *, limit, adapter=None, feedback=(0.5, 0.5), layer=19):
    if not ids or not 1 <= limit <= 24:
        raise ValueError("Invalid generation request")
    model, device = base.model, base.device
    pending, accepted, past = list(ids), [], 0
    cache = B["new_cache"](model)
    traces, calls, processed = [], 0, 0
    started = time.monotonic()
    context = (
        B["scope"](model, adapter, feedback, start=len(ids) - 1, layer=layer, trace=traces)
        if adapter is not None
        else nullcontext()
    )
    with torch.no_grad(), context:
        for _ in range(limit):
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
            calls += 1
            processed += len(pending)
            past += len(pending)
            cache = out.past_key_values
            token = int(out.logits[0, -1].argmax())
            accepted.append(token)
            if token in base.eos_ids:
                break
            pending = [token]
    return dict(
        token_ids=accepted,
        text=base.tokenizer.decode(accepted, skip_special_tokens=True),
        finish_reason="eos" if accepted[-1] in base.eos_ids else "length",
        seconds=time.monotonic() - started,
        forwards=calls,
        processed_tokens=processed,
        prefill_tokens=len(ids),
        adapter_events=traces,
    )


def loss_for(model, adapter, prompt, target, feedback, *, layer=19):
    if not prompt or not target:
        raise ValueError("Empty training input/target")
    device = next(model.parameters()).device
    x = torch.tensor([list(prompt) + list(target[:-1])], device=device)
    with B["scope"](model, adapter, feedback, start=len(prompt) - 1, layer=layer):
        output = model(x, use_cache=False, logits_to_keep=len(target))
    y = torch.tensor(target, device=device)
    return F.cross_entropy(output.logits[0], y)


def mechanical_admission(base, prompt, layer=19):
    """Real-checkpoint parity, gradient ownership and cached/full agreement."""
    torch.manual_seed(2200)
    model = base.model
    adapter = B["Bridge"](model.config.hidden_size).to(base.device)
    x = torch.tensor([prompt], device=base.device)
    with torch.no_grad():
        native = model(x, use_cache=False, logits_to_keep=1).logits
        with B["scope"](model, adapter, [0.1, 0.9], start=len(prompt) - 1, layer=layer):
            zero = model(x, use_cache=False, logits_to_keep=1).logits
    if not torch.equal(native, zero):
        raise ValueError("Zero bridge parity failure")
    loss = loss_for(model, adapter, prompt, [base.tokenizer.eos_token_id], [0.1, 0.9], layer=layer)
    loss.backward()
    if not float(adapter.up.weight.grad.abs().sum()) > 0 or any(
        p.grad is not None or p.requires_grad for p in model.parameters()
    ):
        raise ValueError("Gradient ownership failure")
    with torch.no_grad():
        adapter.up.weight.normal_(std=0.01)
        full_ids = prompt + [int(native[0, -1].argmax())]
        full_x = torch.tensor([full_ids], device=base.device)
        with B["scope"](model, adapter, [0.1, 0.9], start=len(prompt) - 1, layer=layer):
            full = model(full_x, use_cache=False, logits_to_keep=1).logits
            cache = B["new_cache"](model)
            first = model(
                x,
                use_cache=True,
                past_key_values=cache,
                cache_position=torch.arange(len(prompt), device=base.device),
                logits_to_keep=1,
            )
            cached = model(
                full_x[:, -1:],
                use_cache=True,
                past_key_values=first.past_key_values,
                cache_position=torch.tensor([len(prompt)], device=base.device),
                logits_to_keep=1,
            ).logits
    error = float((full - cached).abs().max())
    if not torch.allclose(full, cached, atol=1e-4, rtol=1e-4):
        raise ValueError(f"Cached/full bridge parity failure: {error}")
    return {
        "passed": True,
        "zero_logit_difference": 0,
        "cached_full_max_logit_difference": error,
        "original_gradients_absent": True,
        "adapter_gradients_present": True,
    }
