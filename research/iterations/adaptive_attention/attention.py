"""Per-head source bias with explicit absolute positions and isolated cached calls."""

import math
from contextlib import contextmanager

import torch
from transformers.models.granitemoehybrid.modeling_granitemoehybrid import GraniteMoeHybridAttention


def new_cache(model):
    from transformers.models.granitemoehybrid.modeling_granitemoehybrid import (
        HybridMambaAttentionDynamicCache,
    )

    parameter = next(model.parameters())
    cache = HybridMambaAttentionDynamicCache(
        model.config, batch_size=1, dtype=parameter.dtype, device=parameter.device
    )
    # v4.57.1 initializes (batch, 0), whose shape[-2] incorrectly reports one
    # token to get_seq_length(). Use an actual zero-length attention sequence.
    for layer in cache.transformer_layers:
        shape = (
            1,
            model.config.num_key_value_heads,
            0,
            model.config.hidden_size // model.config.num_attention_heads,
        )
        cache.key_cache[layer] = torch.empty(shape, dtype=parameter.dtype, device=parameter.device)
        cache.value_cache[layer] = torch.empty_like(cache.key_cache[layer])
    return cache


def make_mask(
    original, *, num_heads, query_positions, key_length, query_start, head_bias, device, dtype
):
    if not head_bias:
        return original
    q = torch.tensor(query_positions, device=device)
    if q.ndim != 1 or not len(q) or int(q[-1]) >= key_length:
        raise ValueError("Invalid absolute query positions")
    shape = (1, num_heads, len(q), key_length)
    minimum = torch.finfo(dtype).min
    if original is None:
        blocked = torch.arange(key_length, device=device)[None, :] > q[:, None]
        mask = torch.zeros((len(q), key_length), device=device, dtype=dtype)
        mask.masked_fill_(blocked, minimum)
        mask = mask[None, None]
    else:
        if original.ndim != 4 or original.shape[0] != 1 or original.shape[1] not in (1, num_heads):
            raise ValueError("Unsupported attention mask")
        if original.shape[-2:] != (len(q), key_length):
            raise ValueError("Mask position mismatch")
        mask = (
            torch.where(original, 0.0, minimum) if original.dtype == torch.bool else original
        ).to(device=device, dtype=dtype)
    mask = mask.expand(shape).clone()
    queries = torch.nonzero(q >= query_start).flatten()
    for head, bias in head_bias.items():
        keys = torch.tensor(list(bias), device=device, dtype=torch.long)
        values = torch.tensor(list(bias.values()), device=device, dtype=dtype)
        mask[0, head, queries[:, None], keys[None, :]] += values[None, :]
    return mask


class AdaptiveAttention:
    def __init__(self, model):
        self.model = model
        self.modules = {
            m.layer_idx: m for m in model.modules() if isinstance(m, GraniteMoeHybridAttention)
        }
        if not self.modules or model.config._attn_implementation != "sdpa":
            raise ValueError("Granite SDPA required")
        self.active = False
        self.calls = 0

    @contextmanager
    def apply(self, input_ids, *, query_start, maps, past_length=0):
        if self.active:
            raise RuntimeError("Attention request already active")
        ids = tuple(input_ids)
        total = past_length + len(ids)
        if not ids or not 0 < query_start < total or past_length < 0:
            raise ValueError("Invalid request positions")
        layers = {}
        for (layer, head), bias in maps.items():
            if layer not in self.modules or not 0 <= head < self.modules[layer].num_heads:
                raise ValueError("Invalid head")
            if any(
                type(k) is not int
                or not 0 <= k < query_start
                or type(v) not in (int, float)
                or not math.isfinite(v)
                or not 0 < v <= 5
                for k, v in bias.items()
            ):
                raise ValueError("Invalid source bias")
            if bias:
                layers.setdefault(layer, {})[head] = dict(bias)
        handles = []
        self.active, self.calls = True, 0

        def bind(module, args, kwargs):
            actual = kwargs.get("input_ids", args[0] if args else None)
            if actual is None or actual.ndim != 2 or actual.shape[0] != 1:
                raise ValueError("Input binding mismatch")
            if tuple(actual[0].tolist()) != ids:
                raise ValueError("Input binding mismatch")
            cache = kwargs.get("past_key_values")
            observed = cache.get_seq_length() if cache is not None else 0
            if observed != past_length:
                raise ValueError("Cache binding mismatch")
            positions = kwargs.get("cache_position")
            if positions is not None and positions.tolist() != list(range(past_length, total)):
                raise ValueError("Position binding mismatch")

        def steer(module, args, kwargs):
            hidden = kwargs.get("hidden_states", args[0] if args else None)
            if hidden is None or tuple(hidden.shape[:2]) != (1, len(ids)):
                raise ValueError("Query binding mismatch")
            self.calls += 1
            updated = dict(kwargs)
            updated["attention_mask"] = make_mask(
                kwargs.get("attention_mask"),
                num_heads=module.num_heads,
                query_positions=list(range(past_length, total)),
                key_length=total,
                query_start=query_start,
                head_bias=layers[module.layer_idx],
                device=hidden.device,
                dtype=hidden.dtype,
            )
            return args, updated

        try:
            handles.append(self.model.register_forward_pre_hook(bind, with_kwargs=True))
            for layer in layers:
                handles.append(
                    self.modules[layer].register_forward_pre_hook(steer, with_kwargs=True)
                )
            yield self
        finally:
            for handle in handles:
                handle.remove()
            self.active = False
