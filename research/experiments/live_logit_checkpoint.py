"""One bounded live checkpoint; experimental, not a multi-request serving engine.

Production callers supply LocalClaimScorer with a leased InputTokenBudget. This
path is offline-tested but has not dispatched a new paid request after R12 stopped.
"""

import asyncio
import hashlib
import json
import math
import runpy
import time
from dataclasses import asdict
from pathlib import Path

from jev_guided_decoding.framing import parse_frame
from jev_guided_decoding.logit_bias import bounded_bias
from jev_guided_decoding.types import Candidate

CONTROL = runpy.run_path(str(Path(__file__).with_name("logit_controller.py")))


async def guide_checkpoint(runtime, request, prompt, prefix, *, scorer, seed, record, mode="jev"):
    """Score short futures and return the old prefix plus one selected model token.

    The caller chooses a meaningful checkpoint before entering. No oracle, target
    label, generated answer string or hidden-layer direction is an input. Failed
    scoring cannot return a successful native fallback. Final generation is outside
    this function and uses the same unassisted policy in all comparison arms.
    """
    if getattr(scorer, "budget", None) is None:
        raise ValueError("A durable budget must be supplied before live scoring")
    if mode not in {"jev", "zero", "shuffled"}:
        raise ValueError("Live checkpoint mode must be jev, zero or shuffled")
    if type(seed) is not int or not 0 <= seed < 2**32:
        raise ValueError("Invalid seed")
    prompt, prefix = tuple(prompt), tuple(prefix)
    if runtime.base.encode(request) != prompt:
        raise ValueError("Request does not match model prompt tokens")
    revision = runtime.base.revision
    if not revision:
        raise ValueError("A pinned model revision is required")
    started = time.monotonic()
    record.update(
        status="started",
        model_revision=revision,
        request=asdict(request),
        prompt_ids=prompt,
        prefix_ids=prefix,
        branches=[],
    )
    try:
        state = runtime.inspect(prompt, prefix, count=4)
        digest = hashlib.sha256(json.dumps(prompt + prefix).encode()).hexdigest()
        if state.prefix_digest != digest:
            raise ValueError("Inspected model prefix differs")
        probabilities = dict(state.options)
        if not probabilities or len(probabilities) != len(state.options):
            raise ValueError("Invalid root actions")
        judgments = dict.fromkeys(probabilities)
        bounded_bias(probabilities, judgments, reference=state.options[0][0])
        record.update(
            prefix_digest=digest,
            root_options=state.options,
            checkpoint_prefill_tokens=state.prefill_tokens,
            checkpoint_seconds=state.seconds,
        )
        valid, tokens = [], []
        for token, probability in state.options:
            if time.monotonic() - started >= 90:
                raise TimeoutError("Checkpoint proposal time exceeded")
            branch = runtime.lookahead(
                prompt, prefix, first_token=token, max_tokens=32, seed=seed, max_seconds=15
            )
            record["branches"].append(branch)
            ids = tuple(branch["token_ids"])
            if not ids or ids[0] != token:
                raise ValueError("Lookahead root token differs")
            frame = parse_frame(runtime.base.decode(prefix + ids))
            if frame and frame.kind == "step" and branch["finish_reason"] == "frame":
                logprob = (
                    math.log(probability) + branch["rest_mean_logprob"] * (len(ids) - 1)
                ) / len(ids)
                valid.append(Candidate(ids, frame.body, logprob, "frame"))
                tokens.append(token)
        if valid:
            evaluation = await scorer.score(request, "", tuple(valid), timeout=30, max_attempts=1)
            record["evaluation"] = asdict(evaluation)
            if evaluation.model != "jev-1.13.0" or evaluation.attempts != 1:
                raise ValueError("Unexpected score model or attempt count")
            for token, judgment in zip(tokens, evaluation.judgments, strict=True):
                judgments[token] = asdict(judgment)
        if runtime.base.revision != revision:
            raise ValueError("Model revision changed while awaiting scores")
        record["judgments"] = judgments
        selected = CONTROL["choose"](
            runtime, state, judgments, scored_prefix_digest=digest, seed=seed, mode=mode
        )
        accepted = prefix + (selected["token"],)
        record.update(
            status="complete",
            selection=selected,
            accepted_ids=accepted,
            seconds=time.monotonic() - started,
        )
        return accepted
    except BaseException as exc:
        record.update(
            status="cancelled" if isinstance(exc, asyncio.CancelledError) else "failed",
            error_type=type(exc).__name__,
            seconds=time.monotonic() - started,
        )
        # The supplied scorer owns durable dispatch accounting; retain ambiguous reservations.
        if hasattr(exc, "usage_unknown"):
            record["usage_unknown"] = exc.usage_unknown
        raise
