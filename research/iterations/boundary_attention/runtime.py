"""Serial native prefill with a once-only, asynchronous Jev bridge before a layer."""

import asyncio
import math
import runpy
import threading
import time
from contextlib import contextmanager
from pathlib import Path

import torch
from transformers.models.granitemoehybrid.modeling_granitemoehybrid import ALL_ATTENTION_FUNCTIONS

HERE = Path(__file__).resolve().parent
OLD = runpy.run_path(str(HERE.parent / "selective_attention/runtime.py"))
F = runpy.run_path(str(HERE / "features.py"))
P = runpy.run_path(str(HERE / "policies.py"))
encode = OLD["encode"]


def cache_lengths(cache):
    return [x.shape[-2] if x.ndim == 4 else 0 for x in cache.key_cache]


def signatures(cache, boundary):
    return [
        (x.data_ptr(), x._version if not x.is_inference() else None, tuple(x.shape))
        for name in ("key_cache", "value_cache")
        for x in getattr(cache, name)[:boundary]
    ]


class Runtime:
    def __init__(self, base, boundary=19):
        self.base, self.boundary, self.busy = base, boundary, False
        self.layers = base.model.model.layers
        self.attentions = OLD["A"]["SelectiveAttention"](base.model).modules
        if not 1 <= boundary < len(self.layers) or len(self.attentions) != len(self.layers):
            raise ValueError("Boundary requires a dense all-attention Granite model")

    @contextmanager
    def scope(self, session, pending, callback):
        original = ALL_ATTENTION_FUNCTIONS["sdpa"]
        if getattr(original, "_r17_controlled", False) or getattr(
            original, "_r18_controlled", False
        ):
            raise RuntimeError("Attention request already active")
        override = "sdpa" in ALL_ATTENTION_FUNCTIONS._local_mapping
        owner = threading.get_ident()
        past, total = session.processed, len(session.ids)
        handles = []
        per_forward_calls = 0

        def bind(module, args, kwargs):
            observed = kwargs.get("input_ids", args[0] if args else None)
            if (
                observed is None
                or observed.tolist() != [pending]
                or kwargs.get("past_key_values") is not session.cache
            ):
                raise ValueError("Input/cache binding mismatch")
            if cache_lengths(session.cache) != [past] * len(self.layers):
                raise ValueError("Cache length binding mismatch")
            if kwargs["cache_position"].tolist() != list(range(past, total)):
                raise ValueError("Position binding mismatch")

        def layer_hook(index):
            def enter(module, args, kwargs):
                if threading.get_ident() != owner:
                    raise RuntimeError("Concurrent model execution unsupported")
                if index == self.boundary and past == 0:
                    if session.boundary_record is not None or session.observation is None:
                        raise ValueError("Boundary observation/order mismatch")
                    lengths = cache_lengths(session.cache)
                    if lengths != [total] * self.boundary + [0] * (
                        len(self.layers) - self.boundary
                    ):
                        raise ValueError("Boundary lower/upper cache mismatch")
                    before = signatures(session.cache, self.boundary)
                    record = dict(
                        decisions=1,
                        layer=self.boundary,
                        observer_layer=self.boundary - 1,
                        lower_cache_lengths=lengths[: self.boundary],
                        upper_cache_lengths=lengths[self.boundary :],
                        layer_calls_before=list(session.layer_calls),
                        observation=session.observation,
                    )
                    callback(session.observation["features"])
                    record["lower_cache_unchanged_during_wait"] = before == signatures(
                        session.cache, self.boundary
                    )
                    if not record["lower_cache_unchanged_during_wait"]:
                        raise ValueError("Native cache changed during provider wait")
                    session.boundary_record = record
                session.layer_calls[index] += 1
                session.layer_tokens[index] += len(pending)

            return enter

        def interface(module, query, key, value, attention_mask, **kwargs):
            nonlocal per_forward_calls
            if (
                threading.get_ident() != owner
                or self.attentions.get(module.layer_idx) is not module
            ):
                raise RuntimeError("Unbound attention execution")
            if module.layer_idx == self.boundary - 1 and past == 0:
                self.base._sync()
                start = time.monotonic()
                session.observation = F["observe"](
                    query,
                    key,
                    attention_mask,
                    session.encoded["span_token_indices"],
                    kwargs.get("scaling") or query.shape[-1] ** -0.5,
                )
                self.base._sync()
                session.feature_seconds += time.monotonic() - start
            bias = session.maps.get(module.layer_idx)
            if bias:
                attention_mask = OLD["A"]["controlled_mask"](
                    query,
                    key,
                    attention_mask,
                    positions=list(range(past, total)),
                    query_start=session.encoded["query_start"],
                    source_keys=session.source_keys,
                    head_bias=bias,
                    scaling=kwargs.get("scaling") or query.shape[-1] ** -0.5,
                    conserve=False,
                )
                per_forward_calls += 1
            return original(module, query, key, value, attention_mask, **kwargs)

        interface._r18_controlled = True
        interface._r17_controlled = True
        try:
            handles.append(self.base.model.register_forward_pre_hook(bind, with_kwargs=True))
            for index, layer in enumerate(self.layers):
                handles.append(layer.register_forward_pre_hook(layer_hook(index), with_kwargs=True))
            ALL_ATTENTION_FUNCTIONS["sdpa"] = interface
            yield
        finally:
            if override:
                ALL_ATTENTION_FUNCTIONS["sdpa"] = original
            else:
                del ALL_ATTENTION_FUNCTIONS["sdpa"]
            for handle in handles:
                handle.remove()
            session.last_hook_calls = per_forward_calls


class Session:
    def __init__(self, runtime, encoded):
        self.runtime, self.base, self.encoded = runtime, runtime.base, encoded
        self.ids = list(encoded["input_ids"])
        self.source_keys = sorted(t for span in encoded["span_token_indices"] for t in span)
        if (
            not self.ids
            or not 0 < encoded["query_start"] < len(self.ids)
            or len(set(self.source_keys)) != len(self.source_keys)
            or any(
                type(k) is not int or not 0 <= k < encoded["query_start"] for k in self.source_keys
            )
        ):
            raise ValueError("Invalid evidence/input binding")
        self.cache = OLD["A"]["new_cache"](self.base.model)
        self.maps = {}
        self.strength = 0.0
        self.processed = self.forwards = self.last_hook_calls = self.hook_calls = 0
        self.seconds = self.feature_seconds = self.wait_seconds = 0.0
        self.layer_calls = [0] * len(runtime.layers)
        self.layer_tokens = [0] * len(runtime.layers)
        self.observation = self.boundary_record = None
        self.tokens, self.full_logits = [], []
        self.finish_reason = "token_limit"
        self.first_token_seconds = None

    def run(self, callback, *, limit, cancel, capture):
        start_all = time.monotonic()
        for _ in range(limit):
            if cancel.is_set():
                raise InterruptedError("Cancelled inference drained")
            pending, past = self.ids[self.processed :], self.processed
            self.base._sync()
            start = time.monotonic()
            waited = self.wait_seconds
            with torch.inference_mode(), self.runtime.scope(self, pending, callback):
                output = self.base.model(
                    input_ids=torch.tensor([pending], device=self.base.device),
                    attention_mask=torch.ones(
                        (1, len(self.ids)), device=self.base.device, dtype=torch.long
                    ),
                    past_key_values=self.cache,
                    use_cache=True,
                    cache_position=torch.arange(past, len(self.ids), device=self.base.device),
                    logits_to_keep=1,
                )
                logits = output.logits[0, -1].detach().float()
                if not torch.isfinite(logits).all():
                    raise ValueError("Nonfinite model output")
                if capture:
                    self.full_logits.append(logits.clone())
                logp, selected, top = (
                    torch.log_softmax(logits, -1),
                    int(logits.argmax()),
                    torch.topk(logits, 2),
                )
                token = dict(
                    token_id=selected,
                    argmax_id=selected,
                    selected_logit=float(logits[selected]),
                    top_ids=top.indices.tolist(),
                    top_logits=top.values.tolist(),
                    probability=float(logp[selected].exp()),
                    entropy=float(-(logp.exp() * logp).sum()),
                    active_heads=sum(len(v) for v in self.maps.values()),
                    strength=self.strength,
                )
            self.base._sync()
            self.seconds += time.monotonic() - start - (self.wait_seconds - waited)
            self.forwards += 1
            self.hook_calls += self.last_hook_calls
            token["hook_calls"] = self.last_hook_calls
            self.processed = len(self.ids)
            if cache_lengths(self.cache) != [self.processed] * len(self.runtime.layers):
                raise ValueError("Post-forward cache mismatch")
            token["cache_lengths"] = cache_lengths(self.cache)
            self.ids.append(selected)
            self.tokens.append(token)
            if self.first_token_seconds is None:
                self.first_token_seconds = time.monotonic() - start_all
            if selected in self.base.eos_ids:
                self.finish_reason = "eos"
                break
        ids = [t["token_id"] for t in self.tokens]
        return dict(
            token_ids=ids,
            tokens=self.tokens,
            input_and_output_ids=list(self.ids),
            text=self.base.tokenizer.decode(
                ids, skip_special_tokens=True, clean_up_tokenization_spaces=False
            ),
            model_seconds=self.seconds,
            model_forwards=self.forwards,
            processed_tokens=self.processed,
            prompt_tokens=len(self.encoded["input_ids"]),
            finish_reason=self.finish_reason,
            hook_calls=self.hook_calls,
        )


async def generate(runtime, encoded, view, policy, receipt, *, gate, limit=32, capture=False):
    if runtime.busy:
        raise RuntimeError("Runtime request already active")
    if set(view) != {"id", "question", "sources", "family"} or len(view["sources"]) != len(
        encoded["span_token_indices"]
    ):
        raise ValueError("Public source binding required")
    if type(limit) is not int or not 1 <= limit <= 32:
        raise ValueError("Invalid token limit")
    if (
        policy["mode"] != "additive"
        or policy["envelope"] != "all"
        or any(layer < runtime.boundary for layer, _ in policy["heads"])
    ):
        raise ValueError("Policy must begin at or after the boundary")
    if any(
        layer not in runtime.attentions or not 0 <= head < runtime.attentions[layer].num_heads
        for layer, head in policy["heads"]
    ):
        raise ValueError("Invalid policy head")
    OLD["P"]["strength"](policy, 0)
    runtime.busy = True
    loop, cancel = asyncio.get_running_loop(), threading.Event()
    started = time.monotonic()
    result = dict(
        logical_jev_calls=0,
        receipt_key=None,
        provider_status="unasked",
        guided_path=False,
        raw_scores=None,
        applied_scores=None,
        gate_requested=False,
        call_decision=False,
    )

    def worker():
        session = Session(runtime, encoded)

        def boundary(features):
            if cancel.is_set():
                raise InterruptedError("Cancelled before boundary dispatch")
            requested = P["decision"](gate, features, view["id"])
            result["call_decision"] = requested
            if not requested:
                return
            result.update(logical_jev_calls=1, gate_requested=True)
            runtime.base._sync()
            start = time.monotonic()
            response = asyncio.run_coroutine_threadsafe(receipt(view), loop).result()
            session.wait_seconds += time.monotonic() - start
            result["receipt_key"] = response["key"]
            if response["status"] == "failed":
                result["provider_status"] = "failed_fallback"
                return
            scores = response.get("scores")
            if (
                response["status"] != "complete"
                or not isinstance(scores, list)
                or len(scores) != len(view["sources"])
                or any(
                    type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 1
                    for v in scores
                )
            ):
                raise ValueError("Invalid provider scores")
            result.update(
                provider_status="complete",
                guided_path=True,
                raw_scores=list(scores),
                applied_scores=list(scores),
            )
            session.strength = policy["strength"]
            prior = OLD["OLD"]["P"]["identified"](
                dict(
                    heads=policy["heads"],
                    weights=[policy["strength"]] * len(policy["heads"]),
                    mapping="threshold",
                    threshold=policy["threshold"],
                )
            )
            maps = OLD["OLD"]["P"]["token_maps"](prior, encoded["span_token_indices"], scores)
            for (layer, head), values in maps.items():
                if values:
                    session.maps.setdefault(layer, {})[head] = values

        final = session.run(boundary, limit=limit, cancel=cancel, capture=capture)
        row = dict(
            **result,
            status="complete",
            final=final,
            text=final["text"],
            features=session.observation["features"],
            boundary=session.boundary_record,
            gate=gate,
            model_forwards=session.forwards,
            model_seconds=session.seconds,
            provider_wait_seconds=session.wait_seconds,
            feature_seconds=session.feature_seconds,
            first_token_seconds=session.first_token_seconds,
            layer_calls=session.layer_calls,
            layer_token_counts=session.layer_tokens,
            prefills=1,
            discarded_tokens=0,
            wall_seconds=time.monotonic() - started,
            prompt_digest=encoded["prompt_digest"],
            intervention_used=bool(session.maps),
            pilot=None,
            pilot_reused=False,
        )
        if capture:
            row["_debug"] = dict(logits=session.full_logits, cache=session.cache)
        return row

    task = asyncio.create_task(asyncio.to_thread(worker))
    try:
        return await asyncio.shield(task)
    except asyncio.CancelledError:
        cancel.set()
        while not task.done():
            try:
                await asyncio.shield(task)
            except asyncio.CancelledError:
                continue
            except Exception:
                break
        if task.done() and not task.cancelled():
            task.exception()
        raise
    finally:
        # Cancellation drains the owned worker above before making this model reusable.
        runtime.busy = False
