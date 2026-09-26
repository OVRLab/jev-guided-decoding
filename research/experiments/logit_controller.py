"""Explicit checkpoint policy; hosted scoring is outside the model forward pass."""

import math
import random
from dataclasses import asdict

from jev_guided_decoding.logit_bias import bounded_bias


def choose(runtime, state, judgments, *, scored_prefix_digest, seed, mode):
    """Bind scored root actions to the current prefix and commit one model token.

    Reference is the most probable native root, whose greedy continuation was
    scored. Unassessed actions have no utility; an unassessed reference is a no-op.
    All modes retain native mass outside the evaluated roots. This function cannot
    insert an answer string and never receives an independent reference label.
    """
    if mode not in {"native", "zero", "jev", "shuffled", "synthetic"}:
        raise ValueError("Unknown control mode")
    if state.prefix_digest != scored_prefix_digest:
        raise ValueError("Scored prefix does not match current prefix")
    probabilities = dict(state.options)
    if set(judgments) != set(probabilities):
        raise ValueError("Judgments do not match evaluated root actions")
    utilities = {}
    for token, judgment in judgments.items():
        if judgment is None:
            utilities[token] = None
            continue
        if set(judgment) != {"support", "assessable"} or any(
            type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 1
            for v in judgment.values()
        ):
            raise ValueError("Invalid local judgment")
        utilities[token] = judgment["support"] if judgment["assessable"] >= 0.5 else None
    if mode == "shuffled":
        values = list(utilities.values())
        random.Random(seed + 51913).shuffle(values)
        utilities = dict(zip(utilities, values, strict=True))
    elif mode == "synthetic":
        utilities = {token: float(index == 1) for index, token in enumerate(utilities)}
    reference = state.options[0][0]
    plan = bounded_bias(
        probabilities,
        utilities,
        reference=reference,
        strength=0 if mode in {"native", "zero"} else 2,
        max_bias=0.5,
        max_kl=0.02,
    )
    token, native, adjusted = runtime.sample(state, plan.bias, seed=seed)
    return {
        "mode": mode,
        "seed": seed,
        "prefix_digest": state.prefix_digest,
        "reference": reference,
        "utilities": utilities,
        "plan": asdict(plan),
        "token": token,
        "native_probability": native,
        "adjusted_probability": adjusted,
    }
