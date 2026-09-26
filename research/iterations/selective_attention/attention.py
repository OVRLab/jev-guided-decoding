"""Serial scoped SDPA control; optional preservation of total source attention mass."""

import math
import runpy
import threading
from contextlib import contextmanager
from pathlib import Path

import torch
from transformers.models.granitemoehybrid.modeling_granitemoehybrid import (
    ALL_ATTENTION_FUNCTIONS,
    GraniteMoeHybridAttention,
)

OLD = runpy.run_path(str(Path(__file__).resolve().parents[1] / "adaptive_attention/attention.py"))
new_cache = OLD["new_cache"]


def controlled_mask(
    query, key, original, *, positions, query_start, source_keys, head_bias, scaling, conserve
):
    mask = OLD["make_mask"](
        original,
        num_heads=query.shape[1],
        query_positions=positions,
        key_length=key.shape[-2],
        query_start=query_start,
        head_bias=head_bias,
        device=query.device,
        dtype=query.dtype,
    )
    if not conserve or not head_bias:
        return mask
    qidx = [i for i, p in enumerate(positions) if p >= query_start]
    if not qidx:
        return mask
    keys = torch.tensor(source_keys, device=query.device)
    rows = torch.tensor(qidx, device=query.device)
    groups = query.shape[1] // key.shape[1]
    for h, bias in head_bias.items():
        scores = (query[0, h, rows].float() @ key[0, h // groups, keys].float().T) * scaling
        if original is not None:
            old = original[0, 0 if original.shape[1] == 1 else h]
            offset = old[rows[:, None], keys[None, :]]
            scores = scores + (
                torch.where(offset, 0.0, -torch.inf) if offset.dtype == torch.bool else offset
            )
        added = torch.tensor(
            [bias.get(int(k), 0.0) for k in source_keys], device=query.device, dtype=torch.float32
        )
        correction = torch.logsumexp(scores + added, -1) - torch.logsumexp(scores, -1)
        if not torch.isfinite(correction).all():
            raise ValueError("Invalid evidence partition")
        mask[0, h, rows[:, None], keys[None, :]] -= correction[:, None].to(mask.dtype)
    return mask


class SelectiveAttention:
    def __init__(self, model):
        self.model = model
        self.modules = {
            m.layer_idx: m for m in model.modules() if isinstance(m, GraniteMoeHybridAttention)
        }
        if not self.modules or model.config._attn_implementation != "sdpa":
            raise ValueError("Granite SDPA required")
        self.active, self.calls = False, 0

    @contextmanager
    def apply(self, ids, *, query_start, source_keys, maps, mode, past_length=0):
        if self.active or getattr(ALL_ATTENTION_FUNCTIONS["sdpa"], "_r17_controlled", False):
            raise RuntimeError("Attention request already active")
        if mode not in ("additive", "conserve") or not ids or past_length < 0:
            raise ValueError("Invalid request")
        total = past_length + len(ids)
        if (
            not 0 < query_start < total
            or not source_keys
            or len(set(source_keys)) != len(source_keys)
        ):
            raise ValueError("Invalid evidence positions")
        if any(type(k) is not int or not 0 <= k < query_start for k in source_keys):
            raise ValueError("Evidence must precede controlled queries")
        layers = {}
        for (layer, head), values in maps.items():
            if layer not in self.modules or not 0 <= head < self.modules[layer].num_heads:
                raise ValueError("Invalid head")
            if any(
                k not in source_keys
                or type(v) not in (int, float)
                or not math.isfinite(v)
                or not 0 < v <= 5
                for k, v in values.items()
            ):
                raise ValueError("Invalid evidence bias")
            if values:
                layers.setdefault(layer, {})[head] = dict(values)
        original = ALL_ATTENTION_FUNCTIONS["sdpa"]
        had_override = "sdpa" in ALL_ATTENTION_FUNCTIONS._local_mapping
        owner = threading.get_ident()
        self.calls, self.active = 0, True

        def bind(module, args, kwargs):
            observed = kwargs.get("input_ids", args[0] if args else None)
            cache = kwargs.get("past_key_values")
            if observed is None or observed.tolist() != [list(ids)]:
                raise ValueError("Input binding mismatch")
            if (cache.get_seq_length() if cache is not None else 0) != past_length:
                raise ValueError("Cache binding mismatch")
            cp = kwargs.get("cache_position")
            if cp is not None and cp.tolist() != list(range(past_length, total)):
                raise ValueError("Position binding mismatch")

        def interface(module, query, key, value, attention_mask, **kwargs):
            if threading.get_ident() != owner or self.modules.get(module.layer_idx) is not module:
                raise RuntimeError("Concurrent/unbound attention is unsupported")
            bias = layers.get(module.layer_idx)
            if bias:
                self.calls += 1
                attention_mask = controlled_mask(
                    query,
                    key,
                    attention_mask,
                    positions=list(range(past_length, total)),
                    query_start=query_start,
                    source_keys=source_keys,
                    head_bias=bias,
                    scaling=kwargs.get("scaling") or query.shape[-1] ** -0.5,
                    conserve=mode == "conserve",
                )
            return original(module, query, key, value, attention_mask, **kwargs)

        interface._r17_controlled = True
        handle = None
        try:
            handle = self.model.register_forward_pre_hook(bind, with_kwargs=True)
            if layers:
                ALL_ATTENTION_FUNCTIONS["sdpa"] = interface
            yield self
        finally:
            if layers:
                if had_override:
                    ALL_ATTENTION_FUNCTIONS["sdpa"] = original
                else:
                    del ALL_ATTENTION_FUNCTIONS["sdpa"]
            if handle is not None:
                handle.remove()
            self.active = False
