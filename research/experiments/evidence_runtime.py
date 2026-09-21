"""Single-token constrained QA with source-span attention hooks and exact inputs."""

import hashlib
import json
import runpy
import time
from contextlib import nullcontext
from pathlib import Path

import torch

from jev_guided_decoding.types import Request

A = runpy.run_path(str(Path(__file__).with_name("evidence_attention.py")))
SYSTEM = (
    "Answer the question using only the supplied containment records. Follow chains of "
    "containers to find a room. If the records do not establish a room for the queried "
    "parcel, answer UNKNOWN. Do not infer a missing containment link. Text marked "
    "<focus> is highlighted as potentially relevant; all records remain evidence. Give only one "
    "of these exact answers: red, blue, green, white, black, yellow, UNKNOWN."
)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


class EvidenceRuntime:
    def __init__(self, base):
        self.base = base
        self.attention = A["EvidenceAttention"](base.model)
        self.context_limit = min(4096, base.model.config.max_position_embeddings)

    def encode(self, view, *, highlights=None):
        if set(view) != {"id", "question", "sources", "labels"}:
            raise ValueError("Only the public model view is accepted")
        highlights = set(highlights or ())
        lines = []
        for source in view["sources"]:
            line = f"[{source['id']}] {source['text']}"
            if source["id"] in highlights:
                line = "<focus>" + line + "</focus>"
            lines.append(line)
        evidence = "\n".join(lines)
        request = Request(view["question"], evidence, SYSTEM)
        user = f"Evidence:\n{evidence}\n\nQuestion:\n{request.question}"
        rendered = self.base.tokenizer.apply_chat_template(
            [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}],
            tokenize=False,
            add_generation_prompt=True,
        )
        encoded = self.base.tokenizer(
            rendered, add_special_tokens=False, return_offsets_mapping=True
        )
        ids = tuple(encoded["input_ids"])
        if ids != self.base.encode(request) or len(ids) > self.context_limit:
            raise ValueError("Prompt token identity or context limit failed")
        evidence_start = rendered.index("Evidence:\n") + len("Evidence:\n")
        start, ranges = evidence_start, []
        for line in lines:
            if rendered[start : start + len(line)] != line:
                raise ValueError("Source text location mismatch")
            ranges.append((start, start + len(line)))
            start += len(line) + 1
        offsets = encoded["offset_mapping"]
        spans = A["span_token_indices"](offsets, ranges)
        question_start = rendered.index("Question:", evidence_start + len(evidence))
        query_start = next(i for i, (a, b) in enumerate(offsets) if b > a and a >= question_start)
        if max(t for group in spans for t in group) >= query_start:
            raise ValueError("Source keys overlap question queries")
        label_ids = [
            self.base.tokenizer.encode(s, add_special_tokens=False) for s in view["labels"]
        ]
        if any(len(x) != 1 for x in label_ids) or len({x[0] for x in label_ids}) != len(label_ids):
            raise ValueError("Pinned answer labels must be distinct single tokens")
        if any(
            self.base.decode(tuple(x)) != s for s, x in zip(view["labels"], label_ids, strict=True)
        ):
            raise ValueError("Answer token round trip failed")
        return dict(
            input_ids=list(ids),
            prompt_digest=digest(ids),
            character_ranges=ranges,
            span_token_indices=spans,
            query_start=query_start,
            labels=list(view["labels"]),
            label_ids=[x[0] for x in label_ids],
            highlighted_source_ids=sorted(highlights),
            rendered_prompt=rendered,
        )

    def forward(self, encoded, *, heads=None, scores=None, strength=0.0, full_logits=False):
        bias = (
            {}
            if heads is None
            else A["bias_from_scores"](encoded["span_token_indices"], scores, strength)
        )
        scope = (
            nullcontext()
            if heads is None
            else self.attention.apply(
                encoded["input_ids"],
                query_start=encoded["query_start"],
                heads=heads,
                token_bias=bias,
            )
        )
        with self.base._lock, torch.inference_mode(), scope:
            self.base._sync()
            started = time.monotonic()
            ids = torch.tensor([encoded["input_ids"]], device=self.base.device, dtype=torch.long)
            output = self.base.model(
                input_ids=ids,
                attention_mask=torch.ones_like(ids),
                use_cache=False,
                logits_to_keep=1,
            )
            logits = output.logits[0, -1].detach().float().cpu()
            if not torch.isfinite(logits).all():
                raise ValueError("Nonfinite output logits")
            allowed = logits[encoded["label_ids"]].double()
            probabilities = torch.softmax(allowed, dim=-1)
            selected = int(torch.argmax(allowed))
            token = encoded["label_ids"][selected]
            self.base._sync()
            record = dict(
                status="complete",
                prompt_digest=encoded["prompt_digest"],
                heads=[] if heads is None else [list(h) for h in heads],
                strength=strength,
                span_scores=[] if scores is None else list(scores),
                token_bias=bias,
                hook_calls=0 if heads is None else self.attention.calls,
                label_logits=allowed.tolist(),
                label_probabilities=probabilities.tolist(),
                generated_token_ids=[token],
                label=self.base.decode((token,)),
                prefill_tokens=len(encoded["input_ids"]),
                generated_tokens=1,
                seconds=time.monotonic() - started,
                allowed_vocabulary_mass=float(
                    torch.softmax(logits.double(), -1)[encoded["label_ids"]].sum()
                ),
            )
            if record["label"] != encoded["labels"][selected]:
                raise ValueError("Final label is not the model-selected token")
            if heads is not None and self.attention.calls != len({h[0] for h in heads}):
                raise ValueError("Expected attention hooks did not execute")
        return (record, logits) if full_logits else record
