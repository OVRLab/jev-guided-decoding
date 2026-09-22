"""Native pilot, conditional one-shot Jev, and phase-dependent exact-token generation."""

import hashlib
import json
import random
import runpy
import time
from pathlib import Path

import torch

HERE = Path(__file__).resolve().parent
A = runpy.run_path(str(HERE / "attention.py"))
P = runpy.run_path(str(HERE / "policies.py"))
OLD = runpy.run_path(str(HERE.parent / "adaptive_attention/runtime.py"))
D = runpy.run_path(str(HERE.parent / "adaptive_attention/data.py"))


def encode(tokenizer, view):
    # Same instruction and framing as R16 open-explicit; only the length ceiling changes.
    if set(view) != {"id", "question", "sources", "family"}:
        raise ValueError("Only reference-free public input accepted")
    lines = [f"[{s['id']}] {s['text']}" for s in view["sources"]]
    user = "Evidence:\n" + "\n".join(lines) + "\n\nQuestion:\n" + view["question"]
    rendered = tokenizer.apply_chat_template(
        [{"role": "system", "content": OLD["EXPLICIT"]}, {"role": "user", "content": user}],
        tokenize=False,
        add_generation_prompt=True,
    )
    inputs = tokenizer(rendered, add_special_tokens=False, return_offsets_mapping=True)
    start = rendered.index("Evidence:\n") + len("Evidence:\n")
    ranges = []
    for line in lines:
        if rendered[start : start + len(line)] != line:
            raise ValueError("Source character binding mismatch")
        ranges.append((start, start + len(line)))
        start += len(line) + 1
    spans = OLD["SPANS"]["span_token_indices"](inputs["offset_mapping"], ranges)
    question = rendered.index("Question:", start - 1)
    query_start = next(
        i for i, (a, b) in enumerate(inputs["offset_mapping"]) if b > a and a >= question
    )
    ids = inputs["input_ids"]
    if max(t for span in spans for t in span) >= query_start or len(ids) > 3072:
        raise ValueError("Input context limit")
    return dict(
        input_ids=ids,
        span_token_indices=spans,
        query_start=query_start,
        prompt_digest=hashlib.sha256(json.dumps(ids).encode()).hexdigest(),
        rendered_prompt=rendered,
        character_ranges=ranges,
    )


class Runtime:
    def __init__(self, base):
        self.base, self.hook = base, A["SelectiveAttention"](base.model)

    def session(self, encoded):
        return Session(self, encoded)


class Session:
    def __init__(self, runtime, encoded):
        self.runtime, self.base, self.encoded = runtime, runtime.base, encoded
        self.ids = list(encoded["input_ids"])
        self.source_keys = sorted(t for span in encoded["span_token_indices"] for t in span)
        self.cache = A["new_cache"](self.base.model)
        self.processed = self.forwards = self.hook_calls = 0
        self.seconds = 0.0
        self.tokens = []
        self.finish_reason = "token_limit"

    def extend(self, limit, policy=None, scores=None):
        if type(limit) is not int or not 1 <= limit <= 32 or len(self.tokens) + limit > 32:
            raise ValueError("Invalid token budget")
        if self.finish_reason == "eos":
            return
        for _ in range(limit):
            step, maps, scale = len(self.tokens), {}, 0.0
            if policy is not None:
                scale = P["strength"](policy, step)
                prior = OLD["P"]["identified"](
                    dict(
                        heads=policy["heads"],
                        weights=[scale] * len(policy["heads"]),
                        mapping="threshold",
                        threshold=policy["threshold"],
                    )
                )
                maps = OLD["P"]["token_maps"](prior, self.encoded["span_token_indices"], scores)
            pending, past = self.ids[self.processed :], self.processed
            self.base._sync()
            start = time.monotonic()
            with (
                torch.inference_mode(),
                self.runtime.hook.apply(
                    pending,
                    query_start=self.encoded["query_start"],
                    source_keys=self.source_keys,
                    maps=maps,
                    mode=policy["mode"] if policy else "additive",
                    past_length=past,
                ),
            ):
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
                logp = torch.log_softmax(logits, -1)
                selected = int(logits.argmax())
                top = torch.topk(logits, 2)
                token = dict(
                    token_id=selected,
                    argmax_id=selected,
                    selected_logit=float(logits[selected]),
                    top_ids=top.indices.tolist(),
                    top_logits=top.values.tolist(),
                    probability=float(logp[selected].exp()),
                    entropy=float(-(logp.exp() * logp).sum()),
                    strength=scale,
                    active_heads=len(maps),
                    hook_calls=self.runtime.hook.calls,
                )
            self.base._sync()
            self.seconds += time.monotonic() - start
            self.forwards += 1
            self.hook_calls += self.runtime.hook.calls
            self.processed = len(self.ids)
            if self.cache.get_seq_length() != self.processed:
                raise ValueError("Cache length mismatch")
            self.ids.append(selected)
            self.tokens.append(token)
            if selected in self.base.eos_ids:
                self.finish_reason = "eos"
                break

    def result(self):
        ids = [t["token_id"] for t in self.tokens]
        return dict(
            token_ids=ids,
            tokens=list(self.tokens),
            input_and_output_ids=list(self.ids),
            text=self.base.tokenizer.decode(
                ids, skip_special_tokens=True, clean_up_tokenization_spaces=False
            ),
            model_seconds=self.seconds,
            model_forwards=self.forwards,
            hook_calls=self.hook_calls,
            processed_tokens=self.processed,
            prompt_tokens=len(self.encoded["input_ids"]),
            finish_reason=self.finish_reason,
        )


async def generate(runtime, encoded, view, policy, receipt, *, gate=None, score_mode="jev"):
    if score_mode not in ("jev", "lexical", "shuffled"):
        raise ValueError("Invalid scoring control")
    if set(view) != {"id", "question", "sources", "family"}:
        raise ValueError("Only public input accepted")
    start = time.monotonic()
    native = runtime.session(encoded)
    pilot, observed, decision = None, None, policy is not None
    if gate is not None:
        native.extend(8)
        pilot = native.result()
        observed = P["features"](pilot["tokens"], pilot["text"], view)
        decision = P["gate_decision"](gate, observed, view["id"])
    scores = raw_scores = None
    key, provider_status, logical_calls = None, "unasked", 0
    call_decision = decision
    if decision:
        if score_mode == "lexical":
            scores = D["lexical"](view)
        else:
            logical_calls = 1
            result = await receipt(view)
            key = result["key"]
            provider_status = result["status"]
            if result["status"] == "complete":
                scores = list(result["scores"])
            else:
                provider_status = "failed_fallback"
                decision = False
        raw_scores = None if scores is None else list(scores)
        if scores is not None and score_mode == "shuffled":
            random.Random("r17-shuffle/" + view["id"]).shuffle(scores)
    if decision:
        final = runtime.session(encoded)
        final.extend(32, policy, scores)
    else:
        final = native
        if len(final.tokens) < 32 and final.finish_reason != "eos":
            final.extend(32 - len(final.tokens))
    result = final.result()
    discarded = pilot if decision and pilot else None
    return dict(
        status="complete",
        final=result,
        pilot=pilot,
        pilot_reused=pilot is not None and not decision,
        gate=gate,
        features=observed,
        gate_requested=logical_calls == 1,
        call_decision=call_decision,
        guided_path=decision,
        intervention_used=any(t["active_heads"] for t in result["tokens"]),
        raw_scores=raw_scores,
        applied_scores=scores,
        receipt_key=key,
        provider_status=provider_status,
        logical_jev_calls=logical_calls,
        model_forwards=result["model_forwards"] + (discarded["model_forwards"] if discarded else 0),
        model_seconds=result["model_seconds"] + (discarded["model_seconds"] if discarded else 0),
        wall_seconds=time.monotonic() - start,
        prompt_digest=encoded["prompt_digest"],
        text=result["text"],
    )
