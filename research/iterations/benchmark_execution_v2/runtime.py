"""R27 serial generation with declared terminal stopping and exact work records."""

import copy
import runpy
import time
from contextlib import nullcontext
from pathlib import Path

import torch
from transformers import GenerationConfig, StoppingCriteria, StoppingCriteriaList

B = runpy.run_path(str(Path(__file__).resolve().parents[1] / "gated_repair/bridge.py"))
K = runpy.run_path(str(Path(__file__).with_name("contract.py")))


def new_cache(model, batch_size):
    if model.config.model_type != "granitemoehybrid":
        from transformers import DynamicCache

        return DynamicCache(config=model.config)
    from transformers.models.granitemoehybrid.modeling_granitemoehybrid import (
        HybridMambaAttentionDynamicCache,
    )

    if any(kind != "attention" for kind in model.config.layer_types):
        raise ValueError("Only the dense all-attention Granite checkpoint is admitted")
    p = next(model.parameters())
    cache = HybridMambaAttentionDynamicCache(
        model.config, batch_size=batch_size, dtype=p.dtype, device=p.device
    )
    for layer in cache.transformer_layers:
        shape = (
            batch_size,
            model.config.num_key_value_heads,
            0,
            model.config.hidden_size // model.config.num_attention_heads,
        )
        cache.key_cache[layer] = torch.empty(shape, dtype=p.dtype, device=p.device)
        cache.value_cache[layer] = torch.empty_like(cache.key_cache[layer])
    return cache


def final_text(text, thinking):
    if thinking:
        if "</think>" not in text:
            return "", "unfinished_thinking"
        text = text.rsplit("</think>", 1)[1]
    text = text.strip()
    return text, "complete" if text else "empty"


def generate_batch(
    model,
    tokenizer,
    prompts,
    *,
    limit,
    eos,
    seed,
    profile=None,
    adapter=None,
    gate=0.5,
    layer=19,
    deadline=None,
    kind="free",
    thinking=False,
):
    if len(prompts) != 1:
        raise ValueError("This protocol requires serial generation")
    if kind not in K["KINDS"] or type(thinking) is not bool:
        raise ValueError("Invalid terminal contract")
    if (
        not prompts
        or any(not p or len(p) > 16384 for p in prompts)
        or type(limit) is not int
        or not 1 <= limit <= 16384
        or not eos
        or len(prompts) > 16
    ):
        raise ValueError("Invalid generation limits or input")
    if adapter is not None and len(prompts) != 1:
        raise ValueError("Repair adapter owns one request at a time")
    if deadline:
        deadline()
    device = next(model.parameters()).device
    width = max(map(len, prompts))
    pad = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else min(eos)
    padded = [[pad] * (width - len(p)) + list(p) for p in prompts]
    masks = [[0] * (width - len(p)) + [1] * len(p) for p in prompts]
    x = torch.tensor(padded, device=device)
    attention = torch.tensor(masks, device=device)
    config = (
        copy.deepcopy(model.generation_config)
        if hasattr(model, "generation_config")
        else GenerationConfig()
    )
    config.update(
        max_new_tokens=limit,
        do_sample=False,
        num_beams=1,
        use_cache=True,
        eos_token_id=list(eos),
        pad_token_id=pad,
    )
    if profile:
        allowed = {"do_sample", "temperature", "top_p", "top_k", "min_p"}
        if not set(profile) <= allowed:
            raise ValueError("Unknown sampling profile")
        config.update(**profile)
    torch.manual_seed(seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(seed)
        torch.cuda.synchronize()
    work = dict(
        batch_size=len(prompts),
        padded_prompt_tokens=width * len(prompts),
        forwards=0,
        processed_token_slots=0,
    )
    events = []
    terminal = False

    def count(module, args, kwargs):
        ids = kwargs.get("input_ids", args[0] if args else None)
        if ids is None:
            raise ValueError("Missing explicit input token IDs")
        work["forwards"] += 1
        work["processed_token_slots"] += ids.numel()

    class Deadline(StoppingCriteria):
        def __call__(self, input_ids, scores, **kwargs):
            nonlocal terminal
            if deadline:
                deadline()
            terminal = K["terminal_line"](
                tokenizer.decode(input_ids[0, width:].tolist(), skip_special_tokens=False),
                kind,
                thinking,
            )
            return torch.tensor([terminal], dtype=torch.bool, device=input_ids.device)

    scope = (
        B["scope"](model, adapter, gate, start=width - 1, layer=layer, trace=events)
        if adapter is not None
        else nullcontext()
    )
    handle = model.register_forward_pre_hook(count, with_kwargs=True)
    tick = time.monotonic()
    try:
        with torch.inference_mode(), scope:
            output = model.generate(
                input_ids=x,
                attention_mask=attention,
                generation_config=config,
                past_key_values=new_cache(model, len(prompts)),
                stopping_criteria=StoppingCriteriaList([Deadline()]),
            )
        if device.type == "cuda":
            torch.cuda.synchronize()
    finally:
        handle.remove()
    work["seconds"] = time.monotonic() - tick
    if output[:, :width].tolist() != padded:
        raise ValueError("Generation changed exact input prefixes")
    rows = []
    for prompt, full in zip(prompts, output[:, width:].tolist(), strict=True):
        found = next((i for i, token in enumerate(full) if token in eos), None)
        tokens = full if found is None else full[: found + 1]
        body = tokens if found is None else tokens[:-1]
        rows.append(
            dict(
                prompt_token_ids=list(prompt),
                generated_token_ids=tokens,
                text=tokenizer.decode(body, skip_special_tokens=False),
                finish_reason="eos"
                if found is not None
                else ("terminal_line" if terminal else "length"),
                events=events if adapter is not None else [],
            )
        )
    work["generated_token_slots"] = len(prompts) * len(output[0, width:])
    return rows, work
