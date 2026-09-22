"""R19 treatment using R18's unchanged serial boundary/cache ownership mechanics."""

import asyncio
import math
import runpy
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = runpy.run_path(str(HERE.parent / "boundary_attention/runtime.py"))
P = runpy.run_path(str(HERE / "policies.py"))
Runtime, Session, OLD = (BASE[k] for k in ("Runtime", "Session", "OLD"))


def encode(tokenizer, view):
    encoded = BASE["encode"](tokenizer, view)
    text = encoded["rendered_prompt"]
    start = text.index(P["CLAUSE"])
    offsets = tokenizer(text, add_special_tokens=False, return_offsets_mapping=True)[
        "offset_mapping"
    ]
    encoded["abstention_token_indices"] = [
        i
        for i, (a, b) in enumerate(offsets)
        if b > start and a < start + len(P["CLAUSE"]) and b > a
    ]
    P["validate_spans"](encoded)
    return encoded


async def generate(
    runtime,
    encoded,
    view,
    policy,
    receipt,
    *,
    gate,
    mode="dual",
    instruction_strength=2,
    limit=32,
    capture=False,
):
    P["validate_spans"](encoded)
    if mode not in ("dual", "relevance", "sufficiency") or instruction_strength not in (2, 5):
        raise ValueError("Invalid treatment mode")
    if runtime.busy:
        raise RuntimeError("Runtime request already active")
    if set(view) != {"id", "question", "sources", "family"} or len(view["sources"]) != len(
        encoded["span_token_indices"]
    ):
        raise ValueError("Public source binding required")
    if type(limit) is not int or not 1 <= limit <= 32:
        raise ValueError("Invalid token limit")
    if (
        policy["mode"] != "additive"
        or policy["envelope"] != "all"
        or any(layer < runtime.boundary for layer, _ in policy["heads"])
    ):
        raise ValueError("Policy must begin at or after the boundary")
    if any(
        layer not in runtime.attentions or not 0 <= head < runtime.attentions[layer].num_heads
        for layer, head in policy["heads"]
    ):
        raise ValueError("Invalid policy head")
    OLD["P"]["strength"](policy, 0)
    runtime.busy = True
    loop, cancel = asyncio.get_running_loop(), threading.Event()
    started = time.monotonic()
    result = dict(
        logical_jev_calls=0,
        receipt_key=None,
        provider_status="unasked",
        guided_path=False,
        raw_scores=None,
        applied_scores=None,
        gate_requested=False,
        call_decision=False,
        sufficient=None,
        intervention_action="native",
        applied_maps={},
    )

    def worker():
        session = Session(runtime, encoded)

        def boundary(features):
            if cancel.is_set():
                raise InterruptedError("Cancelled before boundary dispatch")
            requested = P["decision"](gate, features, encoded, view)
            result["call_decision"] = requested
            if not requested:
                return
            result.update(logical_jev_calls=1, gate_requested=True)
            runtime.base._sync()
            start = time.monotonic()
            response = asyncio.run_coroutine_threadsafe(receipt(view), loop).result()
            session.wait_seconds += time.monotonic() - start
            result["receipt_key"] = response["key"]
            if response["status"] == "failed":
                result["provider_status"] = "failed_fallback"
                return
            scores = response.get("scores")
            if (
                response["status"] != "complete"
                or not isinstance(scores, list)
                or len(scores) != len(view["sources"])
                or any(
                    type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 1
                    for v in scores
                )
            ):
                raise ValueError("Invalid provider scores")
            result.update(
                provider_status="complete",
                guided_path=True,
                raw_scores=list(scores),
                applied_scores=list(scores),
            )
            maps, action = P["maps_for"](
                policy, encoded, scores, response.get("sufficient"), mode, instruction_strength
            )
            session.maps = maps
            session.strength = (
                instruction_strength
                if action == "abstention"
                else policy["strength"]
                if action == "relevance"
                else 0.0
            )
            result.update(
                sufficient=response["sufficient"], intervention_action=action, applied_maps=maps
            )

        final = session.run(boundary, limit=limit, cancel=cancel, capture=capture)
        row = dict(
            **result,
            status="complete",
            final=final,
            text=final["text"],
            features=session.observation["features"],
            boundary=session.boundary_record,
            gate=gate,
            benefit_features=P["vector"](session.observation["features"], encoded, view),
            mode=mode,
            instruction_strength=instruction_strength,
            model_forwards=session.forwards,
            model_seconds=session.seconds,
            provider_wait_seconds=session.wait_seconds,
            feature_seconds=session.feature_seconds,
            first_token_seconds=session.first_token_seconds,
            layer_calls=session.layer_calls,
            layer_token_counts=session.layer_tokens,
            prefills=1,
            discarded_tokens=0,
            wall_seconds=time.monotonic() - started,
            prompt_digest=encoded["prompt_digest"],
            intervention_used=bool(session.maps),
            pilot=None,
            pilot_reused=False,
        )
        if capture:
            row["_debug"] = dict(logits=session.full_logits, cache=session.cache)
        return row

    task = asyncio.create_task(asyncio.to_thread(worker))
    try:
        return await asyncio.shield(task)
    except asyncio.CancelledError:
        cancel.set()
        while not task.done():
            try:
                await asyncio.shield(task)
            except asyncio.CancelledError:
                continue
            except Exception:
                break
        if task.done() and not task.cancelled():
            task.exception()
        raise
    finally:
        # Cancellation drains the owned worker above before making this model reusable.
        runtime.busy = False
