"""Single-question mechanics; no paid study or source-checkpoint choice here."""

import math
import runpy
import time
from contextlib import nullcontext
from pathlib import Path

import torch
from transformers import TemperatureLogitsWarper, TopKLogitsWarper, TopPLogitsWarper
from transformers.modeling_utils import ALL_ATTENTION_FUNCTIONS

R = runpy.run_path(str(Path(__file__).resolve().parents[1] / "structured_correction/runtime.py"))
B, weight_digest = R["B"], R["weight_digest"]


def idle_frozen(model):
    if model.training or any(p.requires_grad or p.grad is not None for p in model.parameters()):
        raise ValueError("Runtime requires a frozen evaluation backbone")
    attention = ALL_ATTENTION_FUNCTIONS["sdpa"]
    if (
        getattr(model, "_jev_feedback_active", False)
        or getattr(attention, "_r17_controlled", False)
        or getattr(attention, "_r18_controlled", False)
        or any(b._forward_hooks for b in model.model.layers)
    ):
        raise RuntimeError("Model intervention already active")


def valid_ids(model, ids):
    return (
        isinstance(ids, list)
        and bool(ids)
        and all(type(i) is int and 0 <= i < model.config.vocab_size for i in ids)
    )


def sample_setup(sampling, device):
    if sampling is None:
        return None, [], None
    if (
        not isinstance(sampling, dict)
        or set(sampling) != {"seed", "temperature", "top_p"}
        or type(sampling["seed"]) is not int
        or not 0 <= sampling["seed"] < 2**63
        or any(
            type(sampling[k]) not in (int, float) or not math.isfinite(sampling[k])
            for k in ("temperature", "top_p")
        )
        or not 0 < sampling["temperature"] <= 2
        or not 0 < sampling["top_p"] <= 1
    ):
        raise ValueError("Invalid sampling settings")
    # Match the Transformers default top_k=50 explicitly; never inherit mutable
    # generation_config defaults. The future protocol must name this setting.
    settings = dict(sampling, top_k=50)
    generator = torch.Generator(device=device).manual_seed(settings["seed"])
    warpers = [
        TemperatureLogitsWarper(float(settings["temperature"])),
        TopKLogitsWarper(50),
        TopPLogitsWarper(float(settings["top_p"])),
    ]
    return generator, warpers, settings


def generate(
    model,
    tok,
    ids,
    *,
    limit,
    eos,
    context_limit=16384,
    sampling=None,
    adapter=None,
    memory=None,
    probabilities=None,
    layer=19,
    deadline=None,
):
    idle_frozen(model)
    if (
        not valid_ids(model, ids)
        or not valid_ids(model, eos)
        or len(eos) != len(set(eos))
        or type(limit) is not int
        or not 1 <= limit <= 8192
        or type(context_limit) is not int
        or not 1 <= context_limit <= 16384
        or context_limit > model.config.max_position_embeddings
        or len(ids) + limit > context_limit
    ):
        raise ValueError("Invalid tokens, generation limit or context")
    if (adapter is None) != (memory is None) or (adapter is None) != (probabilities is None):
        raise ValueError("Incomplete intervention binding")
    device = next(model.parameters()).device
    generator, warpers, settings = sample_setup(sampling, device)
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
            logits = out.logits[:, -1, :].float()
            if not torch.isfinite(logits).all():
                raise ValueError("Nonfinite generation logits")
            if generator is None:
                token = int(logits[0].argmax())
            else:
                for warper in warpers:
                    logits = warper(None, logits)
                token = int(
                    torch.multinomial(torch.softmax(logits, dim=-1), 1, generator=generator)[0, 0]
                )
            accepted.append(token)
            if token in eos:
                break
            pending = [token]
    body = accepted[:-1] if accepted[-1] in eos else accepted
    return dict(
        prompt_token_ids=list(ids),
        generated_token_ids=accepted,
        text=tok.decode(body, skip_special_tokens=False, clean_up_tokenization_spaces=False),
        finish_reason="eos" if accepted[-1] in eos else "length",
        processed_tokens=len(ids) + len(accepted) - 1,
        seconds=time.monotonic() - tick,
        events=traces,
        sampling=settings,
    )


def extract(model, ids, positions, *, layer=19):
    """One unmodified full prefill, one pooled vector per representation type."""
    idle_frozen(model)
    if (
        not valid_ids(model, ids)
        or len(ids) > min(4096, model.config.max_position_embeddings)
        or type(layer) is not int
        or not 0 <= layer < len(model.model.layers)
        or not positions
        or any(type(p) is not int or not 0 <= p < len(ids) for p in positions)
        or sorted(set(positions)) != positions
    ):
        raise ValueError("Invalid extraction tokens or positions")
    captured, handle = [], None

    def pool(h):
        if h.shape != (len(ids), model.config.hidden_size) or not torch.isfinite(h).all():
            raise ValueError("Invalid extraction hidden states")
        return h[positions].float().mean(0).detach()

    def capture(_module, _args, output):
        h = output[0] if isinstance(output, tuple) else output
        if h.shape[0] != 1:
            raise ValueError("Extraction owns one prefix")
        captured.append(pool(h[0]))

    tick = time.monotonic()
    model._jev_feedback_active = True
    try:
        with torch.no_grad():
            device = next(model.parameters()).device
            tokens = torch.tensor([ids], device=device)
            embedding = pool(model.get_input_embeddings()(tokens)[0])
            handle = model.model.layers[layer].register_forward_hook(capture)
            out = model(input_ids=tokens, use_cache=False, logits_to_keep=1)
            if not torch.isfinite(out.logits).all() or len(captured) != 1:
                raise ValueError("Incomplete or nonfinite extraction")
    finally:
        if handle is not None:
            handle.remove()
        delattr(model, "_jev_feedback_active")
    return dict(
        embedding=embedding,
        contextual=captured[0],
        positions=list(positions),
        processed_tokens=len(ids),
        seconds=time.monotonic() - tick,
        layer=layer,
    )


def repair_prefix(tok, prompt, draft):
    end = tok.convert_tokens_to_ids("<|end_of_text|>")
    if (
        not prompt
        or not draft
        or type(end) is not int
        or end < 0
        or any(type(i) is not int or i < 0 for i in list(prompt) + list(draft))
        or end in draft[:-1]
    ):
        raise ValueError("Invalid repair prefix")
    instruction = (
        "Check your answer against the original story and question. Correct it if mistaken "
        "and preserve it if already correct. End with exactly one final line in the form "
        "ANSWER: <choice number>."
    )
    suffix = (
        "\n<|start_of_role|>user<|end_of_role|>"
        + instruction
        + "<|end_of_text|>\n<|start_of_role|>assistant<|end_of_role|>"
    )
    return (
        list(prompt)
        + list(draft)
        + ([] if draft[-1] == end else [end])
        + tok.encode(suffix, add_special_tokens=False)
    )
