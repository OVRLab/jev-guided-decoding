from __future__ import annotations

import asyncio
import time
from dataclasses import asdict

from .types import Backend, DecodeConfig, Mode, Request, RunResult, Scorer, ScorerError


class Controller:
    """Select token continuations before generation of the next chunk.

    A run owns its accepted token prefix; rejected branches never enter that prefix.
    The initial backend recomputes the prefix between chunks (no mutable-cache sharing).
    """

    def __init__(self, backend: Backend, config: DecodeConfig, scorer: Scorer | None = None):
        self.backend = backend
        self.config = config
        self.scorer = scorer
        self._lock = asyncio.Lock()

    async def run(self, request: Request, mode: Mode = "jev") -> RunResult:
        if mode not in ("greedy", "sample", "likelihood", "jev"):
            raise ValueError(f"Unknown mode: {mode}")
        if mode == "jev" and self.scorer is None:
            raise ValueError("Jev mode requires a scorer")
        async with self._lock:
            return await self._run(request, mode)

    async def _run(self, request: Request, mode: Mode) -> RunResult:
        cfg = self.config
        started = time.monotonic()
        deadline = started + cfg.max_seconds
        result = RunResult(mode=mode)
        prompt_ids = self.backend.encode(request)
        accepted: tuple[int, ...] = ()
        count = cfg.candidates if mode in ("jev", "likelihood") else 1

        def finish(reason: str) -> RunResult:
            result.stop_reason = reason
            result.token_ids = accepted
            result.text = self.backend.decode(accepted).strip()
            result.elapsed_seconds = time.monotonic() - started
            return result

        for step in range(cfg.max_steps):
            for retry in range(cfg.max_retries + 1 if mode == "jev" else 1):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return finish("time_budget")
                if mode == "jev" and result.api_calls >= cfg.max_api_calls:
                    return finish("api_budget")
                answer_left = cfg.max_answer_tokens - len(accepted)
                if answer_left <= 0:
                    return finish("answer_budget")
                work_left = cfg.max_decode_tokens - result.decode_token_slots
                chunk = min(cfg.chunk_tokens, answer_left, work_left // count)
                if chunk < 1:
                    return finish("decode_budget")
                # The same step/attempt seeds are used across selection modes.
                seed = (cfg.seed + step * 1009 + retry * 9176) % 2**32
                proposal = await asyncio.to_thread(
                    self.backend.propose,
                    prompt_ids,
                    accepted,
                    count=count,
                    max_tokens=chunk,
                    seed=seed,
                    greedy=mode == "greedy",
                    max_seconds=remaining,
                )
                if not proposal.candidates:
                    return finish("no_candidates")
                result.generated_tokens += proposal.generated_tokens
                result.decode_token_slots += proposal.decode_token_slots
                result.prefill_tokens += proposal.prefill_tokens
                result.generation_seconds += proposal.seconds
                entry = {
                    "step": step,
                    "retry": retry,
                    "seed": seed,
                    "accepted_prefix": self.backend.decode(accepted),
                    "candidates": [asdict(c) for c in proposal.candidates],
                    "generated_tokens": proposal.generated_tokens,
                    "decode_token_slots": proposal.decode_token_slots,
                    "prefill_tokens": proposal.prefill_tokens,
                    "generation_seconds": proposal.seconds,
                    "selected": None,
                }
                result.trace.append(entry)
                if time.monotonic() >= deadline:
                    return finish("time_budget")
                if mode == "jev":
                    assert self.scorer is not None
                    scoring_started = time.monotonic()
                    try:
                        evaluation = await self.scorer.score(
                            request,
                            entry["accepted_prefix"],
                            proposal.candidates,
                            timeout=deadline - time.monotonic(),
                            max_attempts=cfg.max_api_calls - result.api_calls,
                        )
                    except ScorerError as exc:
                        result.api_calls += exc.attempts
                        result.usage_unknown |= exc.usage_unknown
                        result.jev_seconds += time.monotonic() - scoring_started
                        entry["error"] = str(exc)
                        return finish("scorer_error")
                    result.api_calls += evaluation.attempts
                    result.jev_input_tokens += evaluation.input_tokens
                    result.jev_output_tokens += evaluation.output_tokens
                    result.jev_seconds += evaluation.seconds
                    entry["evaluation"] = asdict(evaluation)
                    if len(evaluation.judgments) != len(proposal.candidates):
                        entry["error"] = "Scorer returned the wrong number of judgments"
                        return finish("scorer_error")
                    if time.monotonic() >= deadline:
                        return finish("time_budget")
                    eligible = {}
                    for i, (candidate, judgment) in enumerate(
                        zip(proposal.candidates, evaluation.judgments, strict=True)
                    ):
                        relevance = (
                            judgment.completion if candidate.empty_eos else judgment.relevance
                        )
                        threshold = (
                            cfg.completion_threshold
                            if candidate.empty_eos
                            else cfg.relevance_threshold
                        )
                        if judgment.support < cfg.support_threshold:
                            continue
                        if relevance is None or not relevance >= threshold:
                            continue
                        if candidate.finish_reason == "eos" and (
                            judgment.completion is None
                            or not judgment.completion >= cfg.completion_threshold
                        ):
                            continue
                        eligible[i] = min(judgment.support, relevance)
                    if not eligible:
                        if retry == cfg.max_retries:
                            return finish("all_rejected")
                        continue
                    # A ranking heuristic, not a joint probability of correctness.
                    selected = max(
                        eligible,
                        key=lambda i: (
                            eligible[i],
                            proposal.candidates[i].mean_logprob,
                        ),
                    )
                elif mode == "likelihood":
                    selected = max(
                        range(len(proposal.candidates)),
                        key=lambda i: proposal.candidates[i].mean_logprob,
                    )
                else:
                    selected = 0
                candidate = proposal.candidates[selected]
                entry["selected"] = selected
                if not candidate.token_ids:
                    return finish("no_progress")
                accepted += candidate.token_ids
                if candidate.finish_reason == "eos":
                    return finish("eos")
                break
        return finish("step_budget")
