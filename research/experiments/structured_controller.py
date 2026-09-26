"""R13: common syntax, one-token Jev intervention, generator-owned final answer."""

import asyncio
import math
import re
import runpy
import time
from dataclasses import asdict
from pathlib import Path

from jev_guided_decoding.framing import parse_frame
from jev_guided_decoding.types import Candidate, Request, ScorerError

HERE = Path(__file__).parent
CHOOSE = runpy.run_path(str(HERE / "logit_controller.py"))["choose"]
FINAL_LABEL = runpy.run_path(str(HERE / "claim_grammar.py"))["final_label"]
ARMS = ("native", "staged", "likelihood", "jev", "shuffled", "zero", "soft_step")
PAID = {"jev", "shuffled", "zero", "soft_step"}
LIMITS = dict(
    steps=2,
    frame_tokens=40,
    candidates=4,
    final_tokens=16,
    reasoning_forwards=384,
    reasoning_prefill=200000,
    context_tokens=4096,
    job_seconds=90,
    final_seconds=15,
    lookahead_seconds=15,
    api_seconds=30,
)
SYSTEM = """Use only the supplied facts and forward implications. Every condition of a
rule is required. Missing evidence is not explicit negation. The target is a question,
not a given fact. When a <step> opening is supplied, complete one useful intermediate
claim, using 'X is P.', 'X is not P.', or 'It is not established that X is P.', then
close </step>. Earlier steps are tentative; check them against the evidence. When a
<final> opening is supplied, output exactly TRUE if the target follows, FALSE if its
explicit negation follows, or UNKNOWN if neither follows. Write no explanation in
the final frame; finish with </final> or end the message. Do not open another frame."""


class WorkLimit(RuntimeError):
    pass


class Work:
    def __init__(self, limits):
        self.limits, self.started = limits, time.monotonic()
        self.counts = dict(reasoning_forwards=0, reasoning_prefill=0, forced_root_tokens=0)
        self.counts.update(final_forwards=0, final_prefill=0)

    def remaining(self):
        return (
            self.limits["job_seconds"]
            - self.limits["final_seconds"]
            - (time.monotonic() - self.started)
        )

    def reserve(self, tokens):
        if (
            self.remaining() <= 0
            or tokens > self.limits["context_tokens"]
            or self.counts["reasoning_forwards"] >= self.limits["reasoning_forwards"]
            or self.counts["reasoning_prefill"] + tokens > self.limits["reasoning_prefill"]
        ):
            raise WorkLimit("Reasoning budget exhausted; final reserve retained")
        self.counts["reasoning_forwards"] += 1
        self.counts["reasoning_prefill"] += tokens

    def reserve_final(self, tokens):
        if (
            time.monotonic() - self.started >= self.limits["job_seconds"]
            or self.counts["final_forwards"] >= self.limits["final_tokens"]
            or tokens > self.limits["context_tokens"]
        ):
            raise WorkLimit("Final generation budget exhausted")
        self.counts["final_forwards"] += 1
        self.counts["final_prefill"] += tokens


def boundary(text, entities):
    match = re.fullmatch(r"(?:It is not established that )?([A-Z][a-z]+) is(?: not)?", text.strip())
    return match is not None and match[1] in entities


def request_for(view):
    if set(view) != {"id", "evidence", "target", "entities", "properties"}:
        raise ValueError("Only the public model view is accepted")
    return Request(
        f"Determine whether this target follows: {view['target']}", view["evidence"], SYSTEM
    )


async def checkpoint(
    runtime, request, prompt, prefix, offset, grammar, state, *, mode, seed, scorer, work, record
):
    base, limits = runtime.base, work.limits
    revision = base.revision
    record.update(
        prefix_ids=list(prefix),
        prefix_digest=state.prefix_digest,
        root_options=state.options,
        branches=[],
    )
    candidates = []
    for token, probability in state.options:
        branch = dict(root=token, root_probability=probability, continuation={})
        record["branches"].append(branch)
        work.counts["forced_root_tokens"] += 1
        tail = runtime.continue_frame(
            prompt,
            prefix + (token,),
            frame_offset=offset,
            grammar=grammar,
            max_tokens=limits["frame_tokens"] - 1,
            seed=seed,
            greedy=True,
            max_seconds=min(limits["lookahead_seconds"], work.remaining()),
            record=branch["continuation"],
        )
        ids = (token,) + tuple(tail["token_ids"])
        frame = parse_frame(base.decode((prefix + ids)[offset:]))
        if tail["finish_reason"] != "frame" or frame is None or frame.kind != "step":
            raise WorkLimit("Lookahead did not complete within its budget")
        branch.update(
            token_ids=list(ids),
            body=frame.body,
            mean_logprob=(math.log(probability) + tail["logprob_sum"]) / len(ids),
        )
        candidates.append(Candidate(ids, frame.body, branch["mean_logprob"], "frame"))
    if mode == "likelihood":
        selected = max(record["branches"], key=lambda b: b["mean_logprob"])
        record["selection"] = dict(
            mode=mode, token=selected["root"], prefix_digest=state.prefix_digest
        )
        return (selected["root"],)
    if work.remaining() <= 0:
        raise WorkLimit("No reasoning time left before scorer dispatch")
    evaluation = await scorer.score(
        request,
        "",
        tuple(candidates),
        timeout=min(limits["api_seconds"], work.remaining()),
        max_attempts=1,
    )
    record["evaluation"] = asdict(evaluation)
    if base.revision != revision or evaluation.model != scorer.model:
        raise ValueError("Model revision changed across scoring")
    if len(evaluation.judgments) != len(candidates):
        raise ValueError("Wrong judgment count")
    judgments = {
        token: asdict(j) for (token, _), j in zip(state.options, evaluation.judgments, strict=True)
    }
    selection = CHOOSE(
        runtime,
        state,
        judgments,
        scored_prefix_digest=record["prefix_digest"],
        seed=seed,
        mode="jev" if mode == "soft_step" else mode,
    )
    record["selection"] = selection
    if mode == "soft_step":
        for branch in record["branches"]:
            if branch["root"] == selection["token"]:
                return tuple(branch["token_ids"])
    return (selection["token"],)


async def run_job(
    view, runtime, *, mode, seed, scorer=None, record=None, limits=None, final_grammar=False
):
    request = request_for(view)
    if mode not in ARMS:
        raise ValueError("Unknown arm")
    if mode in PAID and (scorer is None or getattr(scorer, "budget", None) is None):
        raise ValueError("Paid arms require a durable budget")
    config = {**LIMITS, **(limits or {})}
    if any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0 for v in config.values()):
        raise ValueError("Positive finite work limits required")
    work = Work(config)
    base = runtime.base
    prompt = tuple(base.encode(request))
    if (
        len(prompt) + config["steps"] * (config["frame_tokens"] + 8) + config["final_tokens"] + 8
        > config["context_tokens"]
    ):
        raise ValueError("Context cannot reserve the final answer")
    if record is None:
        record = {}
    accepted = ()
    record.update(
        id=view["id"],
        mode=mode,
        seed=seed,
        request=asdict(request),
        prompt_ids=list(prompt),
        steps=[],
        accepted_ids=[],
        status="started",
        reasoning_stop="complete",
        work=work.counts,
    )
    runtime.before_forward = work.reserve
    try:
        if mode != "native":
            grammar, opening = runtime.make_grammar(view["entities"], view["properties"])
            for step_index in range(config["steps"]):
                step = dict(before_ids=list(accepted), opening_ids=list(opening), trace=[])
                record["steps"].append(step)
                offset = len(accepted)
                prefix = accepted + tuple(opening)
                checked = False
                try:
                    while not grammar.complete(prefix[offset:]):
                        position = len(prefix) - offset - len(opening)
                        if position >= config["frame_tokens"]:
                            raise WorkLimit("Intermediate frame token limit")
                        state = runtime.inspect(
                            prompt,
                            prefix,
                            allowed=grammar.allowed(prefix[offset:]),
                            count=config["candidates"],
                        )
                        sample_seed = seed + step_index * 1000 + position
                        trace = dict(
                            prefix_digest=state.prefix_digest,
                            prefill_tokens=state.prefill_tokens,
                            seconds=state.seconds,
                            syntax_mass=state.syntax_mass,
                            allowed_count=state.allowed_count,
                            seed=sample_seed,
                        )
                        step["trace"].append(trace)
                        text = base.decode(prefix[offset + len(opening) :])
                        if (
                            not checked
                            and boundary(text, view["entities"])
                            and len(state.options) >= 2
                        ):
                            checked = True
                            if mode != "staged":
                                step["checkpoint"] = {}
                                ids = await checkpoint(
                                    runtime,
                                    request,
                                    prompt,
                                    prefix,
                                    offset,
                                    grammar,
                                    state,
                                    mode=mode,
                                    seed=sample_seed,
                                    scorer=scorer,
                                    work=work,
                                    record=step["checkpoint"],
                                )
                                trace["committed_ids"] = list(ids)
                                prefix += ids
                                continue
                        token, probability, _ = runtime.sample(state, {}, seed=sample_seed)
                        trace.update(committed_ids=[token], probability=probability)
                        prefix += (token,)
                    step.update(
                        token_ids=list(prefix[offset:]),
                        text=base.decode(prefix[offset:]),
                        finish_reason="frame",
                    )
                    accepted = prefix
                    record["accepted_ids"] = list(accepted)
                except WorkLimit as exc:
                    step.update(
                        partial_ids=list(prefix[offset:]), finish_reason="budget", reason=str(exc)
                    )
                    record["reasoning_stop"] = "budget"
                    break
        # Retain exact accepted IDs; supply only a delimiter. No Jev final call.
        opening = tuple(base.encode_control("<final>"))
        final_prefix = accepted + opening
        remaining = config["job_seconds"] - (time.monotonic() - work.started)
        if remaining <= 0:
            raise TimeoutError("Final reserve expired")
        final_trace = None
        if final_grammar:
            runtime.before_forward = work.reserve_final
            proposal, final_trace = runtime.propose_final(
                prompt,
                accepted,
                max_tokens=config["final_tokens"],
                seed=seed + 9000,
                max_seconds=min(config["final_seconds"], remaining),
            )
        else:
            proposal = base.propose_frames(
                prompt,
                final_prefix,
                count=1,
                max_tokens=config["final_tokens"],
                seed=seed + 9000,
                greedy=True,
                max_seconds=min(config["final_seconds"], remaining),
            )
        if len(proposal.candidates) != 1:
            raise ValueError("Wrong final candidate count")
        candidate = proposal.candidates[0]
        if candidate.full_text != base.decode(final_prefix + tuple(candidate.token_ids)):
            raise ValueError("Final model-token provenance mismatch")
        raw = base.decode(candidate.token_ids)
        # The backend's full_text includes the prefix and may contain multiple step frames.
        label = FINAL_LABEL(raw, candidate.finish_reason)
        record["final"] = dict(
            prefix_ids=list(final_prefix),
            opening_ids=list(opening),
            candidate=asdict(candidate),
            decoded_tokens=raw,
            generated_tokens=proposal.generated_tokens,
            decode_token_slots=proposal.decode_token_slots,
            prefill_tokens=proposal.prefill_tokens,
            seconds=proposal.seconds,
            grammar=final_grammar,
            token_trace=final_trace,
        )
        record.update(label=label, status="complete")
        return record
    except BaseException as exc:
        record["status"] = "cancelled" if isinstance(exc, asyncio.CancelledError) else "failed"
        record["error"] = dict(type=type(exc).__name__, message=str(exc))
        if isinstance(exc, ScorerError):
            record["error"].update(
                usage_unknown=exc.usage_unknown, attempts=exc.attempts, diagnostics=exc.diagnostics
            )
        raise
    finally:
        runtime.before_forward = None
        record["seconds"] = time.monotonic() - work.started
