import math

import pytest

from jev_guided_decoding.logit_bias import bounded_bias


def test_zero_strength_and_equal_utilities_are_exact_noops():
    assert bounded_bias({1: 0.4, 2: 0.3}, {1: 0.1, 2: 0.9}, reference=1, strength=0).bias == {}
    assert bounded_bias({1: 0.4, 2: 0.3}, {1: 0.8, 2: 0.8}, reference=1).bias == {}


def test_sparse_bias_respects_full_distribution_kl_and_preserves_tail():
    base = {1: 0.2, 2: 0.3, 3: 0.5}
    plan = bounded_bias(
        {1: 0.2, 2: 0.3}, {1: 0.1, 2: 0.9}, reference=1, strength=100, max_bias=2, max_kl=0.005
    )
    q = {k: p * math.exp(plan.bias.get(k, 0)) / plan.normalizer for k, p in base.items()}
    actual = sum(q[k] * math.log(q[k] / base[k]) for k in base)
    assert sum(q.values()) == pytest.approx(1)
    assert actual == pytest.approx(plan.kl, abs=1e-12)
    assert 0 < actual <= 0.005 + 1e-12
    assert q[2] > base[2] and q[3] > 0
    assert max(map(abs, plan.bias.values())) <= 2


def test_unassessable_reference_leaves_distribution_alone():
    assert bounded_bias({1: 0.4, 2: 0.3}, {1: None, 2: 0.9}, reference=1).bias == {}


@pytest.mark.parametrize(
    "probs,scores",
    [
        ({1: 0.8, 2: 0.8}, {1: 0.1, 2: 0.9}),
        ({1: float("nan")}, {1: 0.2}),
        ({1: 0.5}, {1: float("nan")}),
        ({1: 0.5}, {1: -1}),
        ({1: 0.5}, {2: 0.9}),
    ],
)
def test_invalid_distribution_or_score_fails(probs, scores):
    with pytest.raises(ValueError):
        bounded_bias(probs, scores, reference=1)


@pytest.mark.parametrize(
    "kwargs", [{"strength": -1}, {"max_kl": -0.1}, {"max_bias": float("inf")}, {"reference": 999}]
)
def test_invalid_control_parameters_fail(kwargs):
    options = {"reference": 1, **kwargs}
    with pytest.raises(ValueError):
        bounded_bias({1: 0.5}, {1: 0.2}, **options)
