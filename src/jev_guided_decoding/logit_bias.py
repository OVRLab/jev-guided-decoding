"""Bounded sparse intervention in log-probability space; no inference dependency."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class BiasPlan:
    bias: dict[int, float]
    normalizer: float = 1.0
    kl: float = 0.0
    scale: float = 0.0


def bounded_bias(
    probabilities: dict[int, float],
    utilities: dict[int, float | None],
    *,
    reference: int,
    strength: float = 1.0,
    max_bias: float = 0.5,
    max_kl: float = 0.02,
) -> BiasPlan:
    """Reweight assessed actions while leaving all unlisted actions at zero bias.

    Probabilities are native FULL-vocabulary probabilities, not normalized top-k.
    Utilities are bounded heuristic judgments, not claimed future-value estimates.
    An unassessed reference means no intervention. The closed-form KL includes
    the unlisted vocabulary's probability mass, so no full vector is required.
    """
    if not probabilities or reference not in probabilities or set(utilities) != set(probabilities):
        raise ValueError("Probabilities, utilities and reference must identify the same actions")
    if any(type(k) is not int or k < 0 for k in probabilities):
        raise ValueError("Invalid token ID")
    for value in probabilities.values():
        if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError("Invalid probability")
    if math.fsum(probabilities.values()) > 1 + 1e-12:
        raise ValueError("Listed mass exceeds full distribution")
    for value in utilities.values():
        if value is not None and (
            type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1
        ):
            raise ValueError("Invalid utility")
    for value in (strength, max_bias, max_kl):
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise ValueError("Invalid control limit")
    if max_bias > 20:
        raise ValueError("Maximum bias exceeds the supported numerical range")
    baseline = utilities[reference]
    if baseline is None or strength == 0 or max_bias == 0 or max_kl == 0:
        return BiasPlan({})
    raw = {
        token: max(-max_bias, min(max_bias, strength * (value - baseline)))
        for token, value in utilities.items()
        if value is not None and value != baseline and probabilities[token] > 0
    }
    if not raw:
        return BiasPlan({})

    def at(scale):
        bias = {token: value * scale for token, value in raw.items()}
        z = 1 + math.fsum(probabilities[token] * math.expm1(value) for token, value in bias.items())
        kl = math.fsum(
            probabilities[token] * math.exp(value) * value / z for token, value in bias.items()
        ) - math.log(z)
        return BiasPlan(bias, z, max(0.0, kl), scale)

    plan = at(1.0)
    if plan.kl <= max_kl:
        return plan
    low, high = 0.0, 1.0
    for _ in range(60):
        mid = (low + high) / 2
        if at(mid).kl <= max_kl:
            low = mid
        else:
            high = mid
    return at(low)
