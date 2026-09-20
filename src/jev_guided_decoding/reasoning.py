"""Bounded inference-time search over explicit text steps and final answers."""

from __future__ import annotations

import asyncio
import math
import threading
import time
from dataclasses import asdict, dataclass, field, replace
from typing import Literal, Protocol

from .framing import REASONING_PROMPT, Frame, parse_frame
from .types import SYSTEM_PROMPT, Backend, Proposal, Request, RunResult, Scorer, ScorerError

ReasoningMode = Literal["greedy", "sample", "likelihood", "jev", "final_jev"]


def prepare_reasoning_request(request: Request) -> Request:
    if request.system == REASONING_PROMPT or request.system.endswith("\n\n" + REASONING_PROMPT):
        return request
    system = REASONING_PROMPT
    if request.system != SYSTEM_PROMPT:
        system = request.system + "\n\n" + system
    return replace(request, system=system)


class FramedBackend(Backend, Protocol):
    def propose_frames(
        self,
        prompt_ids: tuple[int, ...],
        accepted_ids: tuple[int, ...],
        *,
        count: int,
        max_tokens: int,
        seed: int,
        greedy: bool,
        max_seconds: float,
        cancel_event: threading.Event,
    ) -> Proposal: ...


@dataclass(frozen=True)
class ReasoningConfig:
    candidates: int = 3
    keep_branches: int = 2
    chunk_tokens: int = 96
    max_steps: int = 6
    max_expansions: int = 8
    max_pending: int = 6
    max_resamples: int = 1
    max_path_tokens: int = 512
    max_decode_tokens: int = 2304
    max_prefill_tokens: int = 60000
    max_context_tokens: int = 4096
    max_api_calls: int = 16
    max_seconds: float = 180.0
    support_threshold: float = 0.75
    progress_threshold: float = 0.60
    completion_threshold: float = 0.75
    seed: int = 42

    def __post_init__(self):
        for name in (
            "candidates",
            "keep_branches",
            "chunk_tokens",
            "max_steps",
            "max_expansions",
            "max_pending",
            "max_path_tokens",
            "max_decode_tokens",
            "max_prefill_tokens",
            "max_context_tokens",
            "max_api_calls",
        ):
            if type(getattr(self, name)) is not int or getattr(self, name) < 1:
                raise ValueError(f"{name} must be a positive integer")
        if type(self.max_resamples) is not int or self.max_resamples < 0:
            raise ValueError("max_resamples must be a nonnegative integer")
        if type(self.seed) is not int or not 0 <= self.seed < 2**32:
            raise ValueError("seed must be an integer in [0, 2**32)")
        if (
            type(self.max_seconds) not in (int, float)
            or not math.isfinite(self.max_seconds)
            or self.max_seconds <= 0
        ):
            raise ValueError("max_seconds must be finite and positive")
        for name in ("support_threshold", "progress_threshold", "completion_threshold"):
            value = getattr(self, name)
            if type(value) not in (int, float) or not 0 <= value <= 1:
                raise ValueError(f"{name} must be a finite probability")


@dataclass
class ReasoningResult(RunResult):
    mode: ReasoningMode
    schema_version: str = "reasoning-v1"
    phase: str = "reasoning"
    steps: list[str] = field(default_factory=list)
    expansions: int = 0
    proposal_batches: int = 0
    backtracks: int = 0
    resamples: int = 0
    duplicate_candidates: int = 0
    unique_candidates: int = 0
    pending_peak: int = 0
    api_attempts_unknown: bool = False


class ReasoningCancelled(asyncio.CancelledError):
    """Cancellation with partial accounting, after local model work has drained."""

    def __init__(self, result: ReasoningResult):
        super().__init__("Reasoning request cancelled")
        self.result = result


@dataclass(frozen=True)
class _Node:
    id: int
    parent_id: int | None
    token_ids: tuple[int, ...] = ()
    steps: tuple[str, ...] = ()
    frame: Frame | None = None
    depth: int = 0
    rank: tuple[float, float] = (0.0, 0.0)


class ReasoningController:
    def __init__(
        self,
        backend: FramedBackend,
        config: ReasoningConfig,
        scorer: Scorer | None = None,
        *,
        clock=None,
    ):
        self.backend, self.config, self.scorer = backend, config, scorer
        self.clock = clock or time.monotonic
        self._lock = asyncio.Lock()

    async def run(self, request: Request, mode: ReasoningMode = "jev") -> ReasoningResult:
        if mode not in ("greedy", "sample", "likelihood", "jev", "final_jev"):
            raise ValueError("Unknown reasoning mode")
        if mode in ("jev", "final_jev") and self.scorer is None:
            raise ValueError("This reasoning mode requires a scorer")
        request = prepare_reasoning_request(request)
        async with self._lock:
            return await self._run(request, mode)

    @staticmethod
    def _account(result, proposal):
        result.generated_tokens += proposal.generated_tokens
        result.decode_token_slots += proposal.decode_token_slots
        result.prefill_tokens += proposal.prefill_tokens
        result.generation_seconds += proposal.seconds

    async def _propose(self, result, prompt_ids, node, **kwargs):
        cancel_event = threading.Event()
        task = asyncio.create_task(
            asyncio.to_thread(
                self.backend.propose_frames,
                prompt_ids,
                node.token_ids,
                cancel_event=cancel_event,
                **kwargs,
            )
        )
        try:
            return await asyncio.shield(task)
        except asyncio.CancelledError:
            cancel_event.set()
            # Cancellation of the await does not stop a GPU worker. Keep ownership
            # until the cooperative stopping criterion has finished that work.
            while not task.done():
                try:
                    await asyncio.shield(task)
                except asyncio.CancelledError:
                    cancel_event.set()
                except Exception:
                    break
            if not task.cancelled() and task.exception() is None:
                proposal = task.result()
                self._account(result, proposal)
                result.trace.append(
                    {
                        "event": "cancelled_generation",
                        "node_id": node.id,
                        "proposal": asdict(proposal),
                    }
                )
            raise

    async def _run(self, request, mode):
        cfg = self.config
        started = self.clock()
        deadline = started + cfg.max_seconds
        result = ReasoningResult(mode=mode)
        node = _Node(0, None)
        pending = []
        next_id = 1
        uses_jev = mode in ("jev", "final_jev")
        count = 1 if mode in ("greedy", "sample") else cfg.candidates
        prompt_ids = self.backend.encode(request)

        def finish(reason):
            result.stop_reason = reason
            result.phase = "complete" if reason == "complete" else "stopped"
            result.steps = list(node.steps)
            result.token_ids = node.token_ids
            result.text = node.frame.body if reason == "complete" else ""
            result.elapsed_seconds = self.clock() - started
            result.trace.append(
                {"event": "finish", "node_id": node.id, "reason": reason, "phase": result.phase}
            )
            return result

        def restore(reason):
            result.trace.append({"event": "dead_end", "node_id": node.id, "reason": reason})
            if not pending:
                return None
            sibling = pending.pop()
            result.backtracks += 1
            result.trace.append(
                {
                    "event": "backtrack",
                    "from_node": node.id,
                    "to_node": sibling.id,
                    "parent_id": sibling.parent_id,
                }
            )
            return sibling

        try:
            while True:
                if self.clock() >= deadline:
                    return finish("time_budget")
                if node.frame is not None and node.frame.kind == "final":
                    return finish("complete")
                local_limit = None
                if node.depth >= cfg.max_steps:
                    local_limit = "depth_budget"
                elif len(node.token_ids) >= cfg.max_path_tokens:
                    local_limit = "path_budget"
                elif len(prompt_ids) + len(node.token_ids) >= cfg.max_context_tokens:
                    local_limit = "context_budget"
                if local_limit:
                    restored = restore(local_limit)
                    if restored is None:
                        return finish(local_limit)
                    node = restored
                    continue
                if result.expansions >= cfg.max_expansions:
                    return finish("expansion_budget")
                result.expansions += 1
                seen = set()
                children = []
                dead_reason = "no_eligible_branch"
                attempts = 1 if mode == "greedy" else cfg.max_resamples + 1
                for attempt in range(attempts):
                    remaining = deadline - self.clock()
                    if remaining <= 0:
                        return finish("time_budget")
                    if uses_jev and result.api_calls >= cfg.max_api_calls:
                        if children:
                            break
                        return finish("api_budget")
                    prefill = (len(prompt_ids) + len(node.token_ids)) * count
                    if result.prefill_tokens + prefill > cfg.max_prefill_tokens:
                        if children:
                            break
                        return finish("prefill_budget")
                    token_limit = min(
                        cfg.chunk_tokens,
                        cfg.max_path_tokens - len(node.token_ids),
                        cfg.max_context_tokens - len(prompt_ids) - len(node.token_ids),
                        (cfg.max_decode_tokens - result.decode_token_slots) // count,
                    )
                    if token_limit < 1:
                        if children:
                            break
                        return finish("decode_budget")
                    if attempt:
                        result.resamples += 1
                    seed = (cfg.seed + (result.expansions - 1) * 1009 + attempt * 9176) % 2**32
                    result.proposal_batches += 1
                    try:
                        proposal = await self._propose(
                            result,
                            prompt_ids,
                            node,
                            count=count,
                            max_tokens=token_limit,
                            seed=seed,
                            greedy=mode == "greedy",
                            max_seconds=remaining,
                        )
                    except Exception as exc:
                        result.trace.append(
                            {"event": "backend_error", "error_type": type(exc).__name__}
                        )
                        return finish("backend_error")
                    self._account(result, proposal)
                    entry = {
                        "event": "proposal",
                        "node_id": node.id,
                        "parent_id": node.parent_id,
                        "depth": node.depth,
                        "attempt": attempt,
                        "seed": seed,
                        "prefix_token_ids": node.token_ids,
                        "prefix_text": self.backend.decode(node.token_ids),
                        "proposal": asdict(proposal),
                        "invalid": {},
                        "duplicates": [],
                        "scored_indices": [],
                        "children": [],
                    }
                    result.trace.append(entry)
                    if (
                        proposal.decode_token_slots > token_limit * count
                        or proposal.prefill_tokens > prefill
                        or proposal.generated_tokens > proposal.decode_token_slots
                        or len(proposal.candidates) > count
                    ):
                        return finish("backend_contract_error")
                    if self.clock() >= deadline:
                        return finish("time_budget")
                    fresh = []
                    for i, candidate in enumerate(proposal.candidates):
                        if candidate.token_ids in seen:
                            entry["duplicates"].append(i)
                            result.duplicate_candidates += 1
                            continue
                        seen.add(candidate.token_ids)
                        result.unique_candidates += 1
                        frame = parse_frame(candidate.text)
                        invalid = None
                        if candidate.finish_reason == "eos" and (
                            frame is None or frame.kind != "final"
                        ):
                            invalid = "premature_eos"
                        elif frame is None:
                            invalid = (
                                "incomplete_step"
                                if candidate.finish_reason == "length"
                                else "malformed_frame"
                            )
                        elif not candidate.token_ids:
                            invalid = "no_progress"
                        elif frame.kind == "step" and frame.body in node.steps:
                            invalid = "repeated_step"
                        if invalid:
                            entry["invalid"][i] = invalid
                            dead_reason = invalid
                            continue
                        fresh.append((i, candidate, frame))
                    to_score = [
                        item
                        for item in fresh
                        if mode == "jev" or (mode == "final_jev" and item[2].kind == "final")
                    ]
                    judgments = {}
                    if to_score:
                        entry["scored_indices"] = [item[0] for item in to_score]
                        scoring_started = self.clock()
                        try:
                            evaluation = await self.scorer.score(
                                request,
                                entry["prefix_text"],
                                tuple(item[1] for item in to_score),
                                timeout=deadline - self.clock(),
                                max_attempts=cfg.max_api_calls - result.api_calls,
                            )
                        except asyncio.CancelledError:
                            result.usage_unknown = True
                            result.api_attempts_unknown = True
                            result.jev_seconds += self.clock() - scoring_started
                            entry["error"] = "cancelled_scoring"
                            raise
                        except ScorerError as exc:
                            result.api_calls += exc.attempts
                            result.usage_unknown |= exc.usage_unknown
                            result.jev_seconds += self.clock() - scoring_started
                            entry["error"] = str(exc)
                            return finish("scorer_error")
                        except (ValueError, TypeError) as exc:
                            # Custom scorers may fail while constructing typed judgments.
                            # Their provider activity cannot be inferred from that exception.
                            result.usage_unknown = True
                            result.api_attempts_unknown = True
                            result.jev_seconds += self.clock() - scoring_started
                            entry["error"] = "invalid_scorer_result"
                            entry["error_type"] = type(exc).__name__
                            return finish("scorer_error")
                        result.api_calls += evaluation.attempts
                        result.jev_input_tokens += evaluation.input_tokens
                        result.jev_output_tokens += evaluation.output_tokens
                        result.jev_seconds += evaluation.seconds
                        entry["evaluation"] = asdict(evaluation)
                        if len(evaluation.judgments) != len(to_score):
                            return finish("scorer_error")
                        if self.clock() >= deadline:
                            return finish("time_budget")
                        judgments = dict(
                            zip(entry["scored_indices"], evaluation.judgments, strict=True)
                        )
                    for i, candidate, frame in fresh:
                        judgment = judgments.get(i)
                        rank = (candidate.mean_logprob, candidate.mean_logprob)
                        if judgment is not None:
                            other = (
                                judgment.completion if frame.kind == "final" else judgment.relevance
                            )
                            threshold = (
                                cfg.completion_threshold
                                if frame.kind == "final"
                                else cfg.progress_threshold
                            )
                            if (
                                judgment.support < cfg.support_threshold
                                or other is None
                                or other < threshold
                            ):
                                dead_reason = "no_eligible_branch"
                                continue
                            rank = (min(judgment.support, other), candidate.mean_logprob)
                        child = _Node(
                            next_id,
                            node.id,
                            node.token_ids + candidate.token_ids,
                            node.steps + (frame.body,) if frame.kind == "step" else node.steps,
                            frame,
                            node.depth + 1,
                            rank,
                        )
                        next_id += 1
                        children.append(child)
                        entry["children"].append(
                            {
                                "node_id": child.id,
                                "candidate_index": i,
                                "kind": frame.kind,
                                "rank": rank,
                                "judged": judgment is not None,
                            }
                        )
                    if children and (
                        any(c.frame.kind == "final" for c in children)
                        or len(seen) > 1
                        or count == 1
                    ):
                        break
                if not children:
                    restored = restore(dead_reason)
                    if restored is None:
                        return finish(dead_reason)
                    node = restored
                    continue
                children.sort(key=lambda c: c.rank, reverse=True)
                kept = children[: cfg.keep_branches]
                result.trace.append(
                    {
                        "event": "select",
                        "parent_id": node.id,
                        "node_id": kept[0].id,
                        "saved": [c.id for c in kept[1:]],
                        "pruned": [c.id for c in children[cfg.keep_branches :]],
                    }
                )
                pending.extend(reversed(kept[1:]))
                if len(pending) > cfg.max_pending:
                    overflow = len(pending) - cfg.max_pending
                    result.trace.append(
                        {"event": "prune_pending", "node_ids": [c.id for c in pending[:overflow]]}
                    )
                    del pending[:overflow]
                result.pending_peak = max(result.pending_peak, len(pending))
                node = kept[0]
        except asyncio.CancelledError:
            raise ReasoningCancelled(finish("cancelled")) from None
