"""Reference-free frozen context memory and a position-matched embedding control."""

import re
import runpy
import time
from pathlib import Path

import torch
from transformers.modeling_utils import ALL_ATTENTION_FUNCTIONS

C = runpy.run_path(str(Path(__file__).resolve().parents[1] / "structured_correction/common.py"))


def decoded_spans(tok, ids):
    """Keep original IDs, grouping incomplete Unicode bytes at stable boundaries."""
    kwargs = dict(skip_special_tokens=False, clean_up_tokenization_spaces=False)
    text = tok.decode(ids, **kwargs)
    spans, previous_token, previous_character = [], 0, 0
    for end in range(1, len(ids) + 1):
        prefix = tok.decode(ids[:end], **kwargs)
        if text.startswith(prefix) and len(prefix) >= previous_character:
            spans.extend([(previous_character, len(prefix))] * (end - previous_token))
            previous_token, previous_character = end, len(prefix)
    if previous_token != len(ids) or len(spans) != len(ids):
        raise ValueError("Unstable token/text alignment")
    return text, spans


def positions_for(tok, case, native, *, eos):
    C["validate_case"](case)
    prompt = tok.apply_chat_template(
        [dict(role="user", content=case["prompt"])], tokenize=True, add_generation_prompt=True
    )
    if native["prompt_token_ids"] != prompt:
        raise ValueError("Native prompt token mismatch")
    generated = native["generated_token_ids"]
    if not generated or eos in generated[:-1]:
        raise ValueError("Invalid draft token sequence")
    body = generated[:-1] if generated[-1] == eos else generated
    kwargs = dict(skip_special_tokens=False, clean_up_tokenization_spaces=False)
    if tok.decode(body, **kwargs) != native["text"]:
        raise ValueError("Native draft text mismatch")
    ids = prompt + body
    if len(ids) > 2048 or any(type(i) is not int or i < 0 for i in ids):
        raise ValueError("Invalid memory input tokens")
    text, spans = decoded_spans(tok, ids)
    prefix = tok.decode(prompt, **kwargs)
    if text != prefix + native["text"]:
        raise ValueError("Unstable prompt/draft boundary")
    answers = C["fields"](native["text"])
    matches = list(re.finditer(r"(?m)^\s*(\d+)[.)]\s*(.*?)\s*$", native["text"]))
    slots = []
    for index, question in enumerate(case["questions"], 1):
        if not question or prefix.count(question) != 1:
            raise ValueError("Missing or ambiguous question span")
        start = prefix.index(question)
        intervals = [(start, start + len(question))]
        found = [m for m in matches if int(m[1]) == index]
        if answers.get(index) and len(found) == 1:
            intervals.append(tuple(len(prefix) + x for x in found[0].span(2)))
        positions = [
            i
            for i, (a, b) in enumerate(spans)
            if a < b and any(a < end and b > begin for begin, end in intervals)
        ]
        if not positions:
            raise ValueError("Empty question memory")
        slots.append(positions)
    return dict(ids=ids, slots=slots)


def memories(model, ids, slots, *, layer=19):
    """One unmodified prefill; no labels, persistent cache, or trainable extractor."""
    if (
        not ids
        or len(ids) > 2048
        or any(type(i) is not int or not 0 <= i < model.config.vocab_size for i in ids)
        or type(layer) is not int
        or not 0 <= layer < len(model.model.layers)
        or len(slots) != 3
        or any(
            not s
            or any(type(i) is not int or not 0 <= i < len(ids) for i in s)
            or sorted(set(s)) != s
            for s in slots
        )
    ):
        raise ValueError("Invalid contextual memory positions or input")
    if model.training or any(p.requires_grad or p.grad is not None for p in model.parameters()):
        raise ValueError("Context extraction requires an evaluation-mode frozen backbone")
    block = model.model.layers[layer]
    sdpa = ALL_ATTENTION_FUNCTIONS["sdpa"]
    if (
        getattr(model, "_jev_feedback_active", False)
        or getattr(sdpa, "_r17_controlled", False)
        or getattr(sdpa, "_r18_controlled", False)
        or any(b._forward_hooks for b in model.model.layers)
    ):
        raise RuntimeError("Model intervention already active")
    captured = []

    def pool(h):
        if h.shape != (len(ids), model.config.hidden_size) or not torch.isfinite(h).all():
            raise ValueError("Invalid memory hidden states")
        return torch.stack([h[s].float().mean(0) for s in slots]).detach()

    def capture(_module, _args, output):
        h = output[0] if isinstance(output, tuple) else output
        if h.shape[0] != 1:
            raise ValueError("Context memory supports one native prefix")
        captured.append(pool(h[0]))

    handle = None
    tick = time.monotonic()
    model._jev_feedback_active = True
    try:
        with torch.no_grad():
            device = next(model.parameters()).device
            tokens = torch.tensor([ids], device=device)
            embedding = pool(model.get_input_embeddings()(tokens)[0])
            handle = block.register_forward_hook(capture)
            model(input_ids=tokens, use_cache=False, logits_to_keep=1)
            if len(captured) != 1:
                raise ValueError("Context extraction did not capture exactly one forward")
    finally:
        if handle is not None:
            handle.remove()
        delattr(model, "_jev_feedback_active")
    return dict(
        embedding=embedding,
        contextual=captured[0],
        positions=[list(s) for s in slots],
        processed_tokens=len(ids),
        seconds=time.monotonic() - tick,
        layer=layer,
    )
