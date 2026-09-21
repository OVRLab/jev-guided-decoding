"""Optional real-model token loop with a common syntax mask and isolated RNG."""

import math
import runpy
import time
from dataclasses import dataclass
from pathlib import Path

import torch

HERE = Path(__file__).parent
BASE = runpy.run_path(str(HERE / "logit_runtime.py"))
GRAMMAR = runpy.run_path(str(HERE / "claim_grammar.py"))


@dataclass(frozen=True)
class SyntaxState:
    probabilities: torch.Tensor
    options: tuple
    prefix_digest: str
    prefill_tokens: int
    seconds: float
    syntax_mass: float
    allowed_count: int


class StructuredRuntime(BASE["LogitTokenBackend"]):
    def __init__(self, base):
        super().__init__(base)
        self.before_forward = None

    def inspect(self, prompt, prefix, *, allowed, count=4):
        allowed = tuple(allowed)
        if (
            not allowed
            or len(set(allowed)) != len(allowed)
            or any(
                type(t) is not int
                or t < 0
                or t >= self.base.model.config.vocab_size
                or t == self.base.pad_id
                for t in allowed
            )
        ):
            raise ValueError("Invalid or empty syntax mask")
        if self.before_forward is not None:
            self.before_forward(len(prompt) + len(prefix))
        native = super().inspect(prompt, prefix, count=count)
        probabilities = torch.zeros_like(native.probabilities)
        indices = torch.tensor(allowed, dtype=torch.long)
        mass = native.probabilities[indices].sum().item()
        if not math.isfinite(mass) or mass <= 0:
            raise ValueError("Syntax mask has zero native probability mass")
        probabilities[indices] = native.probabilities[indices] / mass
        top = torch.topk(probabilities, min(count, len(allowed))).indices.tolist()
        options = tuple((token, probabilities[token].item()) for token in top)
        return SyntaxState(
            probabilities,
            options,
            native.prefix_digest,
            native.prefill_tokens,
            native.seconds,
            mass,
            len(allowed),
        )

    def continue_frame(
        self,
        prompt,
        prefix,
        *,
        frame_offset,
        grammar,
        max_tokens,
        seed,
        greedy,
        max_seconds=15,
        record=None,
    ):
        if record is None:
            record = {}
        prefix = tuple(prefix)
        generated = []
        started = time.monotonic()
        record.update(
            token_ids=generated,
            trace=[],
            generated_tokens=0,
            prefill_tokens=0,
            decode_token_slots=0,
            seconds=0.0,
            logprob_sum=0.0,
            finish_reason="length",
        )
        for position in range(max_tokens):
            if grammar.complete(prefix[frame_offset:]):
                record["finish_reason"] = "frame"
                break
            if time.monotonic() - started >= max_seconds:
                record["finish_reason"] = "time"
                break
            state = self.inspect(prompt, prefix, allowed=grammar.allowed(prefix[frame_offset:]))
            token = (
                state.options[0][0] if greedy else self.sample(state, {}, seed=seed + position)[0]
            )
            probability = state.probabilities[token].item()
            generated.append(token)
            record["generated_tokens"] += 1
            record["decode_token_slots"] += 1
            record["prefill_tokens"] += state.prefill_tokens
            record["logprob_sum"] += math.log(probability)
            record["trace"].append(
                {
                    "token": token,
                    "probability": probability,
                    "prefix_digest": state.prefix_digest,
                    "prefill_tokens": state.prefill_tokens,
                    "syntax_mass": state.syntax_mass,
                    "allowed_count": state.allowed_count,
                    "seconds": state.seconds,
                    "seed": None if greedy else seed + position,
                }
            )
            prefix += (token,)
        if grammar.complete(prefix[frame_offset:]):
            record["finish_reason"] = "frame"
        record["seconds"] = time.monotonic() - started
        return record

    def make_grammar(self, entities, properties):
        opening = self.base.encode_control("<step>")
        sequences = []
        for text in GRAMMAR["claim_texts"](entities, properties):
            ids = tuple(opening) + tuple(
                self.base.tokenizer.encode(text + "</step>", add_special_tokens=False)
            )
            if self.base.decode(ids) != "<step>" + text + "</step>":
                raise ValueError("Tokenizer cannot round-trip canonical claim syntax")
            sequences.append(ids)
        return GRAMMAR["TokenTrie"](sequences), opening
