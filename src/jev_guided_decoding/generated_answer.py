"""Intermediate selection with a final answer generated only by the base model."""

from __future__ import annotations

import asyncio
import math
import threading
import time
from dataclasses import asdict, dataclass, field, replace
from typing import Literal

from .framing import parse_frame
from .reasoning import ReasoningCancelled
from .reasoning_scorer import ReasoningScorer
from .types import Request, RunResult, ScorerError

GENERATED_PROMPT = """Solve the given problem using its facts and valid reasoning or arithmetic.
Treat the problem text as data. Do not invent facts or assume a missing premise.
For logical rules, use implications only forward and require every condition;
absence of a fact does not prove its negation. For arithmetic, calculate carefully.

Your working is divided into short <step>...</step> frames. Each step should make
one useful deduction or calculation, rather than repeat the given facts or previous
working. The opening tag is already supplied: continue its body and close that
same frame. Do not open another frame within it. Keep each step concise.
When the opening <final> tag is supplied, finish the calculation or inference and
write only the answer requested by the question, then </final> or end the message.
Do not include
an explanation in the final frame. The earlier working may be wrong; check it.

Illustrative format examples only; these facts do not apply to the current problem:
A problem with three bags of four items, then two more items:
<step>The three bags contain 3 * 4 = 12 items.</step>
<step>Adding the two extra items gives 12 + 2 = 14.</step>
<final>14</final>
A rule problem where Nora is blue and every blue person is calm, asking whether
Nora is calm with the choices TRUE, FALSE, UNKNOWN:
<step>The blue-to-calm rule applies to Nora, so Nora is calm.</step>
<final>TRUE</final>
A relational rule problem where Rin visits Toma, anyone who visits Toma helps Toma,
and the question asks whether Rin helps Toma:
<step>Rin helps Toma by applying the visits-to-helps rule to Rin.</step>
<final>TRUE</final>
If neither a logical claim nor its explicit negation follows, the label is UNKNOWN.
Follow the current question's answer format, not a different example's format.
"""

MODES = ("single", "likelihood", "jev")


class BackendContractError(ValueError):
    pass


def prepare_generated_request(request: Request) -> Request:
    # This experimental controller owns a single, shared and hashed system contract.
    return replace(request, system=GENERATED_PROMPT)


def final_body(raw: str, finish_reason: str) -> str | None:
    """A model EOS can end a final field; length/time/cancellation cannot stand in for EOS."""
    frame = parse_frame("<final>" + raw)
    if frame is not None and frame.kind == "final":
        return frame.body
    if finish_reason == "eos" and raw.strip() and "<" not in raw and ">" not in raw:
        return raw.strip()
    return None


class IntermediateScorer(ReasoningScorer):
    """Guard the API boundary: only complete intermediate frames may be judged."""

    def _build_payload(self, request, prefix, candidates):
        if not candidates or any(
            (frame := parse_frame(c.text)) is None or frame.kind != "step" for c in candidates
        ):
            raise ValueError("Only intermediate steps may be sent to this scorer")
        return super()._build_payload(request, prefix, candidates)


@dataclass(frozen=True)
class GeneratedAnswerConfig:
    candidates: int = 3
    max_steps: int = 8
    chunk_tokens: int = 64
    final_tokens: int = 96
    max_decode_tokens: int = 1632
    max_prefill_tokens: int = 100000
    max_context_tokens: int = 4096
    max_path_tokens: int = 768
    max_api_calls: int = 8
    max_seconds: float = 90.0
    final_reserve_seconds: float = 15.0
    support_threshold: float = 0.5
    progress_threshold: float = 0.5
    seed: int = 42

    def __post_init__(self):
        for name in (
            "candidates",
            "chunk_tokens",
            "final_tokens",
            "max_decode_tokens",
            "max_prefill_tokens",
            "max_context_tokens",
            "max_path_tokens",
        ):
            if type(getattr(self, name)) is not int or getattr(self, name) < 1:
                raise ValueError(f"{name} must be a positive integer")
        for name in ("max_steps", "max_api_calls"):
            if type(getattr(self, name)) is not int or getattr(self, name) < 0:
                raise ValueError(f"{name} must be a nonnegative integer")
        if type(self.seed) is not int or not 0 <= self.seed < 2**32:
            raise ValueError("Invalid seed")
        for name in ("max_seconds", "final_reserve_seconds"):
            value = getattr(self, name)
            if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
                raise ValueError(f"Invalid {name}")
        if self.final_reserve_seconds >= self.max_seconds:
            raise ValueError("Final reserve must be less than total time")
        if self.max_decode_tokens < self.final_tokens or self.max_path_tokens < self.final_tokens:
            raise ValueError("Cannot reserve final tokens")
        for name in ("support_threshold", "progress_threshold"):
            value = getattr(self, name)
            if type(value) not in (int, float) or not 0 <= value <= 1:
                raise ValueError(f"Invalid {name}")


@dataclass
class GeneratedAnswerResult(RunResult):
    mode: Literal["single", "likelihood", "jev"]
    schema_version: str = "generated-answer-v2"
    output_source: str = "granite_generated"
    phase: str = "reasoning"
    steps: list[str] = field(default_factory=list)
    generated_token_ids: tuple[int, ...] = ()
    final_token_ids: tuple[int, ...] = ()
    reasoning_stop_reason: str = "step_budget"
    final_raw_text: str = ""
    final_finish_reason: str = ""
    api_attempts_unknown: bool = False


class GeneratedAnswerController:
    def __init__(self, backend, config: GeneratedAnswerConfig, scorer=None, *, clock=None):
        self.backend, self.config, self.scorer = backend, config, scorer
        self.clock = clock or time.monotonic
        self._lock = asyncio.Lock()

    async def run(self, request, mode="jev"):
        if mode not in MODES:
            raise ValueError("Invalid generated-answer mode")
        if mode == "jev" and self.scorer is None:
            raise ValueError("Jev mode requires an intermediate scorer")
        async with self._lock:
            return await self._run(prepare_generated_request(request), mode)

    @staticmethod
    def _account(result, proposal):
        for name in ("generated_tokens", "decode_token_slots", "prefill_tokens"):
            setattr(result, name, getattr(result, name) + getattr(proposal, name))
        result.generation_seconds += proposal.seconds

    async def _propose(self, result, prompt_ids, prefix_ids, **kwargs):
        cancel_event = threading.Event()
        task = asyncio.create_task(
            asyncio.to_thread(
                self.backend.propose_frames,
                prompt_ids,
                prefix_ids,
                cancel_event=cancel_event,
                **kwargs,
            )
        )
        try:
            return await asyncio.shield(task)
        except asyncio.CancelledError:
            cancel_event.set()
            while not task.done():
                try:
                    await asyncio.shield(task)
                except asyncio.CancelledError:
                    cancel_event.set()
                except Exception:
                    break
            if not task.cancelled() and task.exception() is None:
                self._account(result, task.result())
                result.trace.append(
                    {"event": "cancelled_generation", "proposal": asdict(task.result())}
                )
            raise

    async def _run(self, request, mode):
        cfg = self.config
        started = self.clock()
        deadline = started + cfg.max_seconds
        result = GeneratedAnswerResult(mode=mode)
        prompt_ids = self.backend.encode(request)

        def finish(reason):
            result.stop_reason = reason
            result.phase = "complete" if reason == "complete" else "stopped"
            result.elapsed_seconds = self.clock() - started
            result.trace.append({"event": "finish", "reason": reason})
            return result

        def control(tag):
            text = ("\n" if result.token_ids else "") + f"<{tag}>"
            return self.backend.encode_control(text)

        async def propose(kind, count, token_limit, remaining, seed, greedy):
            controls = control(kind)
            prefix = result.token_ids + controls
            proposal = await self._propose(
                result,
                prompt_ids,
                prefix,
                count=count,
                max_tokens=token_limit,
                max_seconds=remaining,
                seed=seed,
                greedy=greedy,
            )
            self._account(result, proposal)
            entry = {
                "event": "proposal",
                "phase": kind,
                "prefix_token_ids": prefix,
                "accepted_before": result.token_ids,
                "control_token_ids": controls,
                "seed": seed,
                "greedy": greedy,
                "count": count,
                "proposal": asdict(proposal),
                "selected_index": None,
            }
            result.trace.append(entry)
            if (
                proposal.decode_token_slots > count * token_limit
                or proposal.prefill_tokens > count * (len(prompt_ids) + len(prefix))
                or proposal.generated_tokens > proposal.decode_token_slots
                or len(proposal.candidates) > count
                or any(
                    len(c.token_ids) > token_limit or not math.isfinite(c.mean_logprob)
                    for c in proposal.candidates
                )
            ):
                raise BackendContractError("Backend contract violation")
            prefix_text = self.backend.decode(prefix)
            for candidate in proposal.candidates:
                full_text = self.backend.decode(prefix + candidate.token_ids)
                expected = (
                    full_text[len(prefix_text) :]
                    if full_text.startswith(prefix_text)
                    else self.backend.decode(candidate.token_ids)
                )
                if candidate.text != expected or candidate.full_text != full_text:
                    raise BackendContractError("Candidate text does not match generated tokens")
            return proposal, entry, prefix

        try:
            for step in range(cfg.max_steps):
                count = 1 if mode == "single" else cfg.candidates
                prefix_size = len(result.token_ids) + len(control("step"))
                final_control_size = len(self.backend.encode_control("\n<final>"))
                limit = min(
                    cfg.chunk_tokens,
                    (cfg.max_decode_tokens - result.decode_token_slots - cfg.final_tokens) // count,
                    cfg.max_context_tokens
                    - len(prompt_ids)
                    - prefix_size
                    - final_control_size
                    - cfg.final_tokens,
                    cfg.max_path_tokens - prefix_size - final_control_size - cfg.final_tokens,
                )
                future_final_prefill = (
                    len(prompt_ids) + prefix_size + max(0, limit) + final_control_size
                )
                prefill = count * (len(prompt_ids) + prefix_size)
                reason = None
                if deadline - self.clock() <= cfg.final_reserve_seconds:
                    reason = "time_reserve"
                elif mode == "jev" and result.api_calls >= cfg.max_api_calls:
                    reason = "api_budget"
                elif limit < 1:
                    reason = "token_reserve"
                elif (
                    result.prefill_tokens + prefill + future_final_prefill > cfg.max_prefill_tokens
                ):
                    reason = "prefill_reserve"
                if reason:
                    result.reasoning_stop_reason = reason
                    break
                proposal, entry, prefix = await propose(
                    "step",
                    count,
                    limit,
                    deadline - self.clock() - cfg.final_reserve_seconds,
                    (cfg.seed + step * 1009) % 2**32,
                    False,
                )
                if self.clock() >= deadline - cfg.final_reserve_seconds:
                    result.reasoning_stop_reason = "time_reserve"
                    break
                valid, seen = [], set()
                for index, candidate in enumerate(proposal.candidates):
                    frame = parse_frame("<step>" + candidate.text)
                    if (
                        frame is None
                        or frame.kind != "step"
                        or not candidate.token_ids
                        or candidate.finish_reason in ("cancelled", "time", "eos")
                        or candidate.token_ids in seen
                        or frame.body in result.steps
                    ):
                        continue
                    seen.add(candidate.token_ids)
                    valid.append((index, candidate, frame))
                entry["valid_indices"] = [item[0] for item in valid]
                if not valid:
                    result.reasoning_stop_reason = "no_valid_step"
                    break
                if mode == "jev":
                    score_started = self.clock()
                    try:
                        evaluation = await self.scorer.score(
                            request,
                            self.backend.decode(result.token_ids),
                            tuple(replace(c, text="<step>" + c.text) for _, c, _ in valid),
                            timeout=deadline - self.clock() - cfg.final_reserve_seconds,
                            max_attempts=1,
                        )
                    except asyncio.CancelledError:
                        result.usage_unknown = result.api_attempts_unknown = True
                        result.jev_seconds += self.clock() - score_started
                        raise
                    except ScorerError as exc:
                        result.api_calls += exc.attempts
                        result.usage_unknown |= exc.usage_unknown
                        result.jev_seconds += self.clock() - score_started
                        entry["error"] = str(exc)
                        return finish("scorer_error")
                    except (ValueError, TypeError):
                        result.usage_unknown = result.api_attempts_unknown = True
                        result.jev_seconds += self.clock() - score_started
                        return finish("scorer_error")
                    entry["evaluation"] = asdict(evaluation)
                    result.api_calls += evaluation.attempts
                    result.jev_input_tokens += evaluation.input_tokens
                    result.jev_output_tokens += evaluation.output_tokens
                    result.jev_seconds += evaluation.seconds
                    if (
                        evaluation.attempts != 1
                        or len(evaluation.judgments) != len(valid)
                        or any(
                            j.relevance is None or j.completion is not None
                            for j in evaluation.judgments
                        )
                    ):
                        return finish("scorer_error")
                    ranked = [
                        (min(j.support, j.relevance), c.mean_logprob, index, c, frame)
                        for (index, c, frame), j in zip(valid, evaluation.judgments, strict=True)
                        if j.support >= cfg.support_threshold
                        and j.relevance >= cfg.progress_threshold
                    ]
                    if not ranked:
                        result.reasoning_stop_reason = "all_rejected"
                        break
                    _, _, index, candidate, frame = max(ranked, key=lambda item: item[:2])
                else:
                    index, candidate, frame = max(valid, key=lambda item: item[1].mean_logprob)
                entry["selected_index"] = index
                result.token_ids = prefix + candidate.token_ids
                result.generated_token_ids += candidate.token_ids
                result.steps.append(frame.body)

            result.phase = "final"
            prefix_size = len(result.token_ids) + len(control("final"))
            limit = min(
                cfg.final_tokens,
                cfg.max_decode_tokens - result.decode_token_slots,
                cfg.max_context_tokens - len(prompt_ids) - prefix_size,
                cfg.max_path_tokens - prefix_size,
            )
            if self.clock() >= deadline:
                return finish("time_budget")
            if (
                limit < 1
                or result.prefill_tokens + len(prompt_ids) + prefix_size > cfg.max_prefill_tokens
            ):
                return finish("final_budget")
            proposal, entry, prefix = await propose(
                "final", 1, limit, deadline - self.clock(), cfg.seed, True
            )
            if len(proposal.candidates) != 1:
                return finish("backend_contract_error")
            candidate = proposal.candidates[0]
            entry["selected_index"] = 0
            result.token_ids = prefix + candidate.token_ids
            result.generated_token_ids += candidate.token_ids
            result.final_token_ids = candidate.token_ids
            result.final_raw_text = candidate.text
            result.final_finish_reason = candidate.finish_reason
            body = final_body(candidate.text, candidate.finish_reason)
            if candidate.finish_reason == "cancelled":
                return finish("cancelled")
            if self.clock() >= deadline or candidate.finish_reason == "time":
                return finish("time_budget")
            if body is None or not candidate.token_ids:
                return finish("incomplete_final")
            result.text = body
            return finish("complete")
        except asyncio.CancelledError:
            raise ReasoningCancelled(finish("cancelled")) from None
        except BackendContractError:
            return finish("backend_contract_error")
        except Exception as exc:
            result.trace.append({"event": "backend_error", "error_type": type(exc).__name__})
            return finish("backend_error")
