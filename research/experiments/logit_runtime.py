"""Experimental explicit token selector, after the frozen model's returned logits.

Optional Torch/Transformers dependencies. Re-prefill is the correctness reference;
this is not a retained-cache serving implementation or a hidden-layer intervention.
"""

import hashlib
import inspect
import json
import math
import time
from dataclasses import dataclass

import torch


@dataclass(frozen=True)
class TokenState:
    probabilities: torch.Tensor
    options: tuple
    prefix_digest: str
    prefill_tokens: int
    seconds: float


class LogitTokenBackend:
    def __init__(self, base):
        if base.top_p != 1:
            raise ValueError("The initial logit experiment requires top_p=1")
        self.base = base

    def inspect(self, prompt, prefix, *, count=4):
        ids = tuple(prompt) + tuple(prefix)
        if not ids or type(count) is not int or count < 1:
            raise ValueError("Nonempty token context and positive candidate count required")
        maximum = self.base.model.config.max_position_embeddings
        if len(ids) > maximum:
            raise ValueError("Model context limit exceeded")
        with self.base._lock, torch.inference_mode():
            self.base._sync()
            started = time.monotonic()
            inputs = torch.tensor([ids], dtype=torch.long, device=self.base.device)
            kwargs = {}
            if "logits_to_keep" in inspect.signature(self.base.model.forward).parameters:
                kwargs["logits_to_keep"] = 1
            output = self.base.model(
                input_ids=inputs, attention_mask=torch.ones_like(inputs), use_cache=False, **kwargs
            )
            # The model has already applied its logit scaling. Temperature is applied once here.
            logits = output.logits[0, -1].detach().float().cpu().double() / self.base.temperature
            if not torch.isfinite(logits).all():
                raise ValueError("Nonfinite model logits")
            logits[self.base.pad_id] = -torch.inf
            probabilities = torch.softmax(logits, dim=-1)
            top = torch.topk(probabilities, min(count, probabilities.numel() - 1)).indices.tolist()
            options = tuple((token, probabilities[token].item()) for token in top)
            self.base._sync()
            digest = hashlib.sha256(json.dumps(ids).encode()).hexdigest()
            return TokenState(probabilities, options, digest, len(ids), time.monotonic() - started)

    @staticmethod
    def distribution(state, bias):
        for token, value in bias.items():
            if type(token) is not int or not 0 <= token < state.probabilities.numel():
                raise ValueError("Invalid biased token")
            if type(value) not in (int, float) or not math.isfinite(value) or abs(value) > 20:
                raise ValueError("Invalid logit bias")
        if not bias:
            return state.probabilities
        adjusted = state.probabilities.clone()
        for token, value in bias.items():
            adjusted[token] *= math.exp(value)
        return adjusted / adjusted.sum()

    def sample(self, state, bias, *, seed):
        if type(seed) is not int or not 0 <= seed < 2**63:
            raise ValueError("Invalid sampling seed")
        probabilities = self.distribution(state, bias)
        # Explicit per-position CPU generator: shadow generation cannot consume this stream.
        generator = torch.Generator(device="cpu").manual_seed(seed)
        token = torch.multinomial(probabilities, 1, generator=generator).item()
        return token, state.probabilities[token].item(), probabilities[token].item()

    def lookahead(self, prompt, prefix, *, first_token, max_tokens, seed, max_seconds):
        if max_tokens < 1:
            raise ValueError("Lookahead token limit must include the forced first token")
        if first_token in self.base.eos_ids or max_tokens == 1:
            return {
                "token_ids": (first_token,),
                "finish_reason": "eos" if first_token in self.base.eos_ids else "length",
                "generated_tokens": 0,
                "decode_token_slots": 0,
                "prefill_tokens": 0,
                "seconds": 0.0,
                "rest_mean_logprob": 0.0,
                "forced_tokens": 1,
            }
        proposal = self.base.propose_frames(
            tuple(prompt),
            tuple(prefix) + (first_token,),
            count=1,
            max_tokens=max_tokens - 1,
            seed=seed,
            greedy=True,
            max_seconds=max_seconds,
        )
        if len(proposal.candidates) != 1:
            raise ValueError("Lookahead backend returned the wrong candidate count")
        candidate = proposal.candidates[0]
        return {
            "token_ids": (first_token,) + candidate.token_ids,
            "finish_reason": candidate.finish_reason,
            "generated_tokens": proposal.generated_tokens,
            "decode_token_slots": proposal.decode_token_slots,
            "prefill_tokens": proposal.prefill_tokens,
            "seconds": proposal.seconds,
            "rest_mean_logprob": candidate.mean_logprob,
            "forced_tokens": 1,
        }
