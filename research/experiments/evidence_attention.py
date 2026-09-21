"""Scoped source-token attention emphasis; optional Torch/Transformers research code."""

import math
from contextlib import contextmanager

import torch
from transformers.models.granitemoehybrid.modeling_granitemoehybrid import GraniteMoeHybridAttention


def span_token_indices(offsets, ranges):
    result = []
    for start, end in ranges:
        if type(start) is not int or type(end) is not int or not 0 <= start < end:
            raise ValueError("Invalid character span")
        indices = [i for i, (a, b) in enumerate(offsets) if b > a and a < end and b > start]
        if not indices or offsets[indices[0]][0] > start or offsets[indices[-1]][1] < end:
            raise ValueError("Source span is not covered by token offsets")
        if result and set(indices).intersection(t for group in result for t in group):
            raise ValueError("Source spans share a boundary token")
        result.append(indices)
    return result


def bias_from_scores(spans, scores, strength):
    if len(spans) != len(scores) or not scores:
        raise ValueError("One relevance score per span required")
    if not math.isfinite(strength) or not 0 <= strength <= 3:
        raise ValueError("Invalid attention strength")
    if any(type(r) not in (int, float) or not math.isfinite(r) or not 0 <= r <= 1 for r in scores):
        raise ValueError("Invalid relevance probability")
    if strength == 0 or max(scores) == min(scores):
        return {}
    result = {}
    for indices, relevance in zip(spans, scores, strict=True):
        value = strength * max(0.0, 2 * relevance - 1)
        if value:
            for token in indices:
                if type(token) is not int or token < 0 or token in result:
                    raise ValueError("Invalid or overlapping span tokens")
                result[token] = value
    return result


def steered_mask(original, *, heads, num_heads, length, query_start, token_bias, device, dtype):
    """Preserve causality and padding; alter only specified source keys/query heads."""
    if not token_bias:
        return original
    minimum = torch.finfo(dtype).min
    if original is None:
        mask = torch.full((length, length), minimum, device=device, dtype=dtype).triu(1)
        mask = mask[None, None]
    else:
        if original.ndim != 4 or original.shape[0] != 1 or original.shape[1] not in (1, num_heads):
            raise ValueError("Expected single-request 4D causal mask")
        if original.shape[-2] not in (1, length) or original.shape[-1] != length:
            raise ValueError("Incremental or incompatible mask")
        if original.dtype == torch.bool:
            mask = torch.where(original, 0.0, minimum).to(device=device, dtype=dtype)
        else:
            mask = original.to(device=device, dtype=dtype)
    mask = mask.expand(1, num_heads, length, length).clone()
    keys = torch.tensor(list(token_bias), device=device, dtype=torch.long)
    values = torch.tensor(list(token_bias.values()), device=device, dtype=dtype)
    for head in heads:
        mask[0, head, query_start:, keys] += values
    return mask


class EvidenceAttention:
    """Single-owner hooks with exact prefix binding and no mutable cache support."""

    def __init__(self, model):
        self.model = model
        self.modules = {
            m.layer_idx: m for m in model.modules() if isinstance(m, GraniteMoeHybridAttention)
        }
        if not self.modules or model.config._attn_implementation != "sdpa":
            raise ValueError("This prototype requires Granite attention with SDPA")
        self.active = False
        self.calls = 0

    @contextmanager
    def apply(self, prefix, *, query_start, heads, token_bias):
        if self.active:
            raise RuntimeError("Attention request already active")
        prefix = tuple(prefix)
        if not prefix or not 0 < query_start < len(prefix):
            raise ValueError("Invalid attention query boundary")
        selected = {}
        for layer, head in heads:
            module = self.modules.get(layer)
            if module is None or type(head) is not int or not 0 <= head < module.num_heads:
                raise ValueError("Invalid attention head")
            if head in selected.setdefault(layer, []):
                raise ValueError("Duplicate attention head")
            selected[layer].append(head)
        if not selected:
            raise ValueError("At least one attention head required")
        bias = dict(token_bias)
        if any(
            type(k) is not int
            or not 0 <= k < query_start
            or type(v) not in (int, float)
            or not math.isfinite(v)
            or not 0 < v <= 3
            for k, v in bias.items()
        ):
            raise ValueError("Invalid source token bias")
        handles = []
        self.active, self.calls = True, 0

        def bind(module, args, kwargs):
            ids = kwargs.get("input_ids", args[0] if args else None)
            if (
                ids is None
                or ids.ndim != 2
                or ids.shape[0] != 1
                or tuple(ids[0].tolist())[: len(prefix)] != prefix
            ):
                raise ValueError("Attention request prefix mismatch")
            if kwargs.get("use_cache", True) or kwargs.get("past_key_values") is not None:
                raise ValueError("Attention reference rejects cache use")

        def steer(module, args, kwargs):
            hidden = kwargs.get("hidden_states", args[0] if args else None)
            if hidden is None or hidden.shape[0] != 1 or hidden.shape[1] < len(prefix):
                raise ValueError("Invalid attention query states")
            self.calls += 1
            if not bias:
                return args, kwargs
            kwargs = dict(kwargs)
            kwargs["attention_mask"] = steered_mask(
                kwargs.get("attention_mask"),
                heads=selected[module.layer_idx],
                num_heads=module.num_heads,
                length=hidden.shape[1],
                query_start=query_start,
                token_bias=bias,
                device=hidden.device,
                dtype=hidden.dtype,
            )
            return args, kwargs

        try:
            handles.append(self.model.register_forward_pre_hook(bind, with_kwargs=True))
            for layer in selected:
                handles.append(
                    self.modules[layer].register_forward_pre_hook(steer, with_kwargs=True)
                )
            yield self
        finally:
            for handle in handles:
                handle.remove()
            self.active = False
