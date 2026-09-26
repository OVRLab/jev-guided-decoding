import runpy
from pathlib import Path
from types import SimpleNamespace

import pytest

CONTROL = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "research/experiments/logit_controller.py")
)


class Runtime:
    def sample(self, state, bias, *, seed):
        self.bias = bias
        return 1, 0.6, 0.6


def choose(judgments, mode="jev", digest="same"):
    state = SimpleNamespace(options=((1, 0.6), (2, 0.3)), prefix_digest="same")
    return CONTROL["choose"](
        Runtime(), state, judgments, scored_prefix_digest=digest, seed=42, mode=mode
    )


def test_critic_only_biases_assessed_actions_and_zero_control_is_exact():
    scores = {1: {"support": 0.1, "assessable": 1}, 2: {"support": 0.9, "assessable": 1}}
    result = choose(scores)
    assert result["plan"]["bias"][2] > 0
    assert result["plan"]["kl"] <= 0.02
    assert choose(scores, mode="zero")["plan"]["bias"] == {}
    assert choose(scores, mode="native")["plan"]["bias"] == {}
    scores[1] = None
    assert choose(scores)["plan"]["bias"] == {}


def test_stale_or_incomplete_judgment_binding_fails_before_sampling():
    scores = {1: None, 2: None}
    with pytest.raises(ValueError, match="prefix"):
        choose(scores, digest="old")
    with pytest.raises(ValueError, match="actions"):
        choose({1: None})
    with pytest.raises(ValueError, match="judgment"):
        choose({1: {"support": 0.8, "assessable": float("nan")}, 2: None})
    with pytest.raises(ValueError, match="mode"):
        choose(scores, mode="unregistered")


def test_shuffling_preserves_score_multiset_and_is_reproducible():
    scores = {1: {"support": 0.1, "assessable": 1}, 2: {"support": 0.9, "assessable": 1}}
    first = choose(scores, mode="shuffled")
    second = choose(scores, mode="shuffled")
    assert first == second
    assert sorted(first["utilities"].values()) == [0.1, 0.9]
