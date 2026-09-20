from __future__ import annotations

import math
import re
import threading
import time
from typing import Any

import torch
import transformers
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    GenerationConfig,
    StoppingCriteria,
    StoppingCriteriaList,
)

from ..framing import frame_boundary
from ..types import Candidate, Proposal, Request

_ENDING = re.compile(r"""[.!?]["')\]]*\s*$|\n\s*\n$""")
_ABBREVIATION = re.compile(r"\b(?:Mr|Mrs|Ms|Dr|Prof|St|vs|etc|e\.g|i\.e)\.$", re.I)


def sentence_boundary(text: str) -> bool:
    """Conservative English heuristic, not a linguistic sentence parser."""
    stripped = text.rstrip()
    if not _ENDING.search(text) or _ABBREVIATION.search(stripped):
        return False
    # A period after a digit may be the start of a decimal or a numbered item.
    if re.search(r"\d\.$", stripped):
        return False
    return bool(stripped)


class ChunkStop(StoppingCriteria):
    def __init__(self, tokenizer: Any, prefix_length: int, count: int, deadline: float):
        self.tokenizer = tokenizer
        self.prefix_length = prefix_length
        self.stopped_at: list[int | None] = [None] * count
        self.reasons = ["length"] * count
        self.deadline = deadline

    def __call__(self, input_ids: torch.Tensor, scores: Any, **kwargs: Any) -> torch.Tensor:
        rows = input_ids[:, self.prefix_length :].tolist()
        timed_out = time.monotonic() >= self.deadline
        for i, ids in enumerate(rows):
            if self.stopped_at[i] is None:
                if timed_out:
                    self.stopped_at[i] = len(ids)
                    self.reasons[i] = "time"
                elif sentence_boundary(self.tokenizer.decode(ids, skip_special_tokens=True)):
                    self.stopped_at[i] = len(ids)
                    self.reasons[i] = "sentence"
        return torch.tensor([n is not None for n in self.stopped_at], device=input_ids.device)


class FrameStop(ChunkStop):
    def __init__(self, tokenizer, prefix_length, count, deadline, cancel_event=None):
        super().__init__(tokenizer, prefix_length, count, deadline)
        self.cancel_event = cancel_event

    def __call__(self, input_ids, scores, **kwargs):
        rows = input_ids[:, self.prefix_length :].tolist()
        cancelled = self.cancel_event is not None and self.cancel_event.is_set()
        timed_out = time.monotonic() >= self.deadline
        for i, ids in enumerate(rows):
            if self.stopped_at[i] is not None:
                continue
            if cancelled or timed_out:
                self.stopped_at[i] = len(ids)
                self.reasons[i] = "cancelled" if cancelled else "time"
            elif frame_boundary(self.tokenizer.decode(ids, skip_special_tokens=True)):
                self.stopped_at[i] = len(ids)
                self.reasons[i] = "frame"
        return torch.tensor([n is not None for n in self.stopped_at], device=input_ids.device)


class TransformersBackend:
    """Frozen causal LM, batched proposals, exact token-prefix continuation.

    Each propose() uses an independent HF generation cache. The accepted prefix is
    re-prefilled on the next call, intentionally avoiding cross-branch cache mutation.
    """

    def __init__(
        self,
        model: Any,
        tokenizer: Any,
        *,
        model_id: str,
        revision: str | None = None,
        temperature: float = 0.8,
        top_p: float = 0.95,
    ):
        if not math.isfinite(temperature) or temperature <= 0 or not 0 < top_p <= 1:
            raise ValueError("temperature must be positive and top_p in (0, 1]")
        if model.config.is_encoder_decoder:
            raise ValueError("This backend currently supports decoder-only causal models")
        self.model = model.eval().requires_grad_(False)
        self.tokenizer = tokenizer
        self.model_id = model_id
        self.revision = revision
        self.temperature = temperature
        self.top_p = top_p
        self.device = next(model.parameters()).device
        self._lock = threading.Lock()
        eos = model.generation_config.eos_token_id
        if eos is None:
            eos = tokenizer.eos_token_id
        self.eos_ids = set(eos if isinstance(eos, list) else [eos]) - {None}
        pad = tokenizer.pad_token_id
        self.pad_id = pad if pad is not None else next(iter(self.eos_ids), None)
        if self.pad_id is None:
            raise ValueError("Tokenizer needs a pad token or an EOS token")

    @classmethod
    def load(
        cls,
        model_id: str,
        *,
        revision: str | None = None,
        device: str = "auto",
        dtype: str = "auto",
        temperature: float = 0.8,
        top_p: float = 0.95,
        local_files_only: bool = False,
    ) -> TransformersBackend:
        if device == "auto":
            device = (
                "cuda"
                if torch.cuda.is_available()
                else ("mps" if torch.backends.mps.is_available() else "cpu")
            )
        if dtype == "auto":
            dtype = "float32" if device == "cpu" else "bfloat16"
        if dtype not in ("float32", "float16", "bfloat16"):
            raise ValueError("Unsupported dtype")
        tokenizer = AutoTokenizer.from_pretrained(
            model_id,
            revision=revision,
            local_files_only=local_files_only,
            trust_remote_code=False,
        )
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            revision=revision,
            local_files_only=local_files_only,
            trust_remote_code=False,
            dtype=getattr(torch, dtype),
            attn_implementation="sdpa",
        ).to(device)
        return cls(
            model,
            tokenizer,
            model_id=model_id,
            revision=revision,
            temperature=temperature,
            top_p=top_p,
        )

    def encode(self, request: Request) -> tuple[int, ...]:
        user_text = f"Evidence:\n{request.evidence}\n\nQuestion:\n{request.question}"
        if self.tokenizer.chat_template:
            ids = self.tokenizer.apply_chat_template(
                [
                    {"role": "system", "content": request.system},
                    {"role": "user", "content": user_text},
                ],
                tokenize=True,
                add_generation_prompt=True,
            )
        else:
            ids = self.tokenizer.encode(f"{request.system}\n\n{user_text}\n\nAnswer:")
        return tuple(ids)

    def decode(self, token_ids: tuple[int, ...]) -> str:
        return self.tokenizer.decode(
            list(token_ids),
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )

    def encode_control(self, text: str) -> tuple[int, ...]:
        """Encode only a framing delimiter, never an answer or model-generated text."""
        if text not in ("<step>", "\n<step>", "<final>", "\n<final>"):
            raise ValueError("Unsupported control delimiter")
        return tuple(self.tokenizer.encode(text, add_special_tokens=False))

    def _sync(self) -> None:
        if self.device.type == "mps":
            torch.mps.synchronize()
        elif self.device.type == "cuda":
            torch.cuda.synchronize(self.device)

    def propose(
        self,
        prompt_ids: tuple[int, ...],
        accepted_ids: tuple[int, ...],
        *,
        count: int,
        max_tokens: int,
        seed: int,
        greedy: bool,
        max_seconds: float,
        framed: bool = False,
        cancel_event: threading.Event | None = None,
    ) -> Proposal:
        if greedy and count != 1:
            raise ValueError("Greedy generation has one candidate")
        ids = prompt_ids + accepted_ids
        context_limit = getattr(self.model.config, "max_position_embeddings", None)
        if context_limit and len(ids) + max_tokens > context_limit:
            raise ValueError("Prompt plus continuation exceeds the model context window")
        with self._lock, torch.inference_mode():
            self._sync()
            started = time.monotonic()
            torch.manual_seed(seed)
            inputs = torch.tensor([ids], dtype=torch.long, device=self.device)
            stop = (
                FrameStop(self.tokenizer, len(ids), count, started + max_seconds, cancel_event)
                if framed
                else ChunkStop(self.tokenizer, len(ids), count, started + max_seconds)
            )
            # Build explicitly, so a model repo's sampling defaults do not affect comparisons.
            generation = GenerationConfig(
                max_new_tokens=max_tokens,
                do_sample=not greedy,
                num_beams=1,
                num_return_sequences=count,
                temperature=1.0 if greedy else self.temperature,
                top_p=1.0 if greedy else self.top_p,
                top_k=50 if greedy else 0,
                bos_token_id=self.model.generation_config.bos_token_id,
                eos_token_id=sorted(self.eos_ids) or None,
                pad_token_id=self.pad_id,
                use_cache=True,
                return_dict_in_generate=True,
                output_logits=True,
            )
            output = self.model.generate(
                input_ids=inputs,
                attention_mask=torch.ones_like(inputs),
                generation_config=generation,
                stopping_criteria=StoppingCriteriaList([stop]),
            )
            rows = output.sequences[:, len(ids) :].tolist()
            lengths: list[int] = []
            reasons: list[str] = []
            for i, row in enumerate(rows):
                end = stop.stopped_at[i] or len(row)
                reason = stop.reasons[i]
                for j, token in enumerate(row[:end]):
                    if token in self.eos_ids:
                        end, reason = j + 1, "eos"
                        break
                lengths.append(end)
                reasons.append(reason)
            sums = [0.0] * len(rows)
            for position, logits in enumerate(output.logits):
                targets = output.sequences[:, len(ids) + position]
                values = logits.float().log_softmax(-1).gather(1, targets[:, None])[:, 0].tolist()
                for i, value in enumerate(values):
                    if position < lengths[i]:
                        sums[i] += value
            candidates_list = []
            prefix_text = self.decode(accepted_ids)
            for i, row in enumerate(rows):
                new_ids = tuple(row[: lengths[i]])
                full_text = self.decode(accepted_ids + new_ids)
                text = (
                    full_text[len(prefix_text) :]
                    if full_text.startswith(prefix_text)
                    else (self.decode(new_ids))
                )
                candidates_list.append(
                    Candidate(
                        new_ids,
                        text,
                        sums[i] / max(1, lengths[i]),
                        reasons[i],
                        full_text,
                    )
                )
            candidates = tuple(candidates_list)
            slots = len(output.logits) * count
            del output
            self._sync()
            return Proposal(
                candidates,
                sum(lengths),
                slots,
                len(ids) * count,
                time.monotonic() - started,
            )

    def propose_frames(self, prompt_ids, accepted_ids, *, cancel_event=None, **kwargs):
        return self.propose(
            prompt_ids, accepted_ids, framed=True, cancel_event=cancel_event, **kwargs
        )

    def metadata(self) -> dict[str, Any]:
        return {
            "backend": "transformers",
            "model": self.model_id,
            "requested_revision": self.revision,
            "resolved_revision": getattr(self.model.config, "_commit_hash", None),
            "device": str(self.device),
            "dtype": str(next(self.model.parameters()).dtype),
            "parameters": sum(p.numel() for p in self.model.parameters()),
            "trainable_parameters": sum(
                p.numel() for p in self.model.parameters() if p.requires_grad
            ),
            "torch": torch.__version__,
            "transformers": transformers.__version__,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "cache_between_chunks": "recompute accepted prefix",
        }

    def memory(self) -> dict[str, Any]:
        if self.device.type == "cuda":
            return {"cuda_peak_allocated_bytes": torch.cuda.max_memory_allocated(self.device)}
        if self.device.type == "mps":
            return {
                "mps_current_allocated_bytes": torch.mps.current_allocated_memory(),
                "mps_driver_allocated_bytes": torch.mps.driver_allocated_memory(),
                "note": "MPS counters are current allocations, not per-run peaks.",
            }
        return {"note": "Device memory counters unavailable on CPU."}

    def reset_memory_peak(self) -> None:
        if self.device.type == "cuda":
            torch.cuda.reset_peak_memory_stats(self.device)
