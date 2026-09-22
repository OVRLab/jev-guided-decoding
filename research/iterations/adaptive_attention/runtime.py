"""Exact-token unrestricted generation with per-request Granite caches and head biases."""

import hashlib
import json
import runpy
import time
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
A = runpy.run_path(str(HERE / "attention.py"))
OLD = runpy.run_path(str(ROOT / "research/experiments/evidence_runtime.py"))
SPANS = runpy.run_path(str(ROOT / "research/experiments/evidence_attention.py"))
P = runpy.run_path(str(HERE / "policies.py"))
COMMON = "Answer the question using only the supplied evidence. Combine stated facts as needed. "
EXPLICIT = COMMON + (
    "If the evidence does not establish an answer, explain that briefly in your own words. "
    "Give only a short answer, without explanation when an answer is established."
)
NEUTRAL = COMMON + "Give only a short answer."
STAGED = COMMON + (
    "Work through relevant facts briefly when asked for reasoning. When asked for the final "
    "answer, give only a short answer. If the evidence does not establish an answer, "
    "explain that briefly in your own words."
)
SYSTEMS = {
    "constrained": OLD["SYSTEM"],
    "open_explicit": EXPLICIT,
    "open_neutral": NEUTRAL,
    "staged": STAGED,
}


def encode(tokenizer, view, contract):
    if set(view) != {"id", "question", "sources", "family"} or contract not in SYSTEMS:
        raise ValueError("Invalid public input/contract")
    lines = [f"[{s['id']}] {s['text']}" for s in view["sources"]]
    evidence = "\n".join(lines)
    user = f"Evidence:\n{evidence}\n\nQuestion:\n{view['question']}"
    rendered = tokenizer.apply_chat_template(
        [{"role": "system", "content": SYSTEMS[contract]}, {"role": "user", "content": user}],
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
    offsets = inputs["offset_mapping"]
    spans = SPANS["span_token_indices"](offsets, ranges)
    question = rendered.index("Question:", start - 1)
    query_start = next(i for i, (a, b) in enumerate(offsets) if b > a and a >= question)
    if max(t for s in spans for t in s) >= query_start:
        raise ValueError("Sources overlap controlled queries")
    ids = inputs["input_ids"]
    if len(ids) > 2200:
        raise ValueError("Input context limit")
    return dict(
        input_ids=ids,
        span_token_indices=spans,
        query_start=query_start,
        prompt_digest=hashlib.sha256(json.dumps(ids).encode()).hexdigest(),
        rendered_prompt=rendered,
        character_ranges=ranges,
        contract=contract,
    )


class Runtime:
    def __init__(self, base):
        self.base = base
        self.hook = A["AdaptiveAttention"](base.model)

    def session(self, encoded):
        return Session(self, encoded)


class Session:
    def __init__(self, runtime, encoded):
        self.runtime, self.base, self.encoded = runtime, runtime.base, encoded
        self.ids = list(encoded["input_ids"])
        self.cache = A["new_cache"](self.base.model)
        self.processed = self.forwards = self.hook_calls = 0
        self.seconds = 0.0
        self.frames, self.phases, self.maps_history = [], [], []

    def frame(self, token_ids, name):
        if not token_ids or any(type(i) is not int or i < 0 for i in token_ids):
            raise ValueError("Invalid framing tokens")
        self.frames.append({"name": name, "start": len(self.ids), "token_ids": list(token_ids)})
        self.ids.extend(token_ids)

    def logits(self, maps):
        pending = self.ids[self.processed :]
        if not pending or len(self.ids) > 2400:
            raise ValueError("Invalid generation prefix")
        past = self.processed
        self.base._sync()
        start = time.monotonic()
        with (
            torch.inference_mode(),
            self.runtime.hook.apply(
                pending, query_start=self.encoded["query_start"], maps=maps, past_length=past
            ),
        ):
            ids = torch.tensor([pending], device=self.base.device, dtype=torch.long)
            output = self.base.model(
                input_ids=ids,
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
        self.base._sync()
        self.seconds += time.monotonic() - start
        self.forwards += 1
        self.hook_calls += self.runtime.hook.calls
        self.processed = len(self.ids)
        if self.cache.get_seq_length() != self.processed:
            raise ValueError("Cache length does not match exact prefix")
        return logits

    def generate(self, limit, phase, *, maps, allowed=None, stop_newline=False):
        if type(limit) is not int or not 1 <= limit <= 96:
            raise ValueError("Invalid generation budget")
        start_position = len(self.ids)
        records, generated, reason = [], [], "token_limit"
        for _ in range(limit):
            logits = self.logits(maps)
            argmax = int(logits.argmax())
            if allowed is None:
                selected = argmax
            else:
                selected = allowed[int(logits[allowed].argmax())]
            top = torch.topk(logits, 2)
            record = dict(
                token_id=selected,
                argmax_id=argmax,
                selected_logit=float(logits[selected]),
                top_ids=top.indices.tolist(),
                top_logits=top.values.tolist(),
            )
            if allowed is not None:
                label_logits = logits[allowed].double()
                record.update(
                    allowed_ids=list(allowed),
                    label_logits=label_logits.tolist(),
                    label_logprobs=torch.log_softmax(label_logits, -1).tolist(),
                )
            records.append(record)
            generated.append(selected)
            self.ids.append(selected)
            if selected in self.base.eos_ids:
                reason = "eos"
                break
            if stop_newline and "\n" in self.base.tokenizer.decode(
                generated, skip_special_tokens=True
            ):
                reason = "newline"
                break
        result = {
            "phase": phase,
            "start": start_position,
            "token_ids": generated,
            "tokens": records,
            "text": self.base.tokenizer.decode(
                generated, skip_special_tokens=True, clean_up_tokenization_spaces=False
            ),
            "finish_reason": reason,
            "maps": [
                {
                    "head": list(h),
                    "keys": len(b),
                    "maximum": max(b.values()),
                    "bias_sha256": hashlib.sha256(
                        json.dumps(sorted(b.items())).encode()
                    ).hexdigest(),
                }
                for h, b in maps.items()
            ],
        }
        self.phases.append(result)
        return result

    def result(self):
        return dict(
            status="complete",
            phases=self.phases,
            framing=self.frames,
            final_input_and_output_ids=self.ids,
            model_seconds=self.seconds,
            model_forwards=self.forwards,
            processed_tokens=self.processed,
            prompt_tokens=len(self.encoded["input_ids"]),
            generated_tokens=sum(len(p["token_ids"]) for p in self.phases),
            hook_calls=self.hook_calls,
            text=self.phases[-1]["text"] if self.phases else "",
        )
