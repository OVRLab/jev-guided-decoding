import copy
import math
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_independent_r15_audit_rejects_scope_and_threshold_tampering():
    module = runpy.run_path(str(ROOT / "research/analysis/evidence_v2.py"))
    encoded = dict(
        input_ids=[1, 2, 3, 4, 5, 6],
        query_start=4,
        span_token_indices=[[1], [3]],
        labels=["red", "blue"],
        label_ids=[11, 12],
        prompt_digest="abc",
    )
    policy = dict(id="test", heads=[[1, 2]], count=1, scope="answer", mapping="hard80", strength=2)
    row = dict(
        policy=policy,
        raw_scores=[0.81, 0.8],
        query_start=5,
        heads=[[1, 2]],
        strength=2,
        span_scores=[1, 0],
        token_bias={"1": 2},
        hook_calls=1,
        prompt_digest="abc",
        generated_token_ids=[12],
        label="blue",
        label_logits=[0, 1],
        label_probabilities=[1 / (1 + math.e), math.e / (1 + math.e)],
    )
    module["audit_row"](row, encoded, policy, [0.81, 0.8])
    for field, value in [
        ("query_start", 4),
        ("span_scores", [1, 1]),
        ("token_bias", {"1": 2, "3": 2}),
    ]:
        changed = copy.deepcopy(row)
        changed[field] = value
        with pytest.raises(ValueError):
            module["audit_row"](changed, encoded, policy, [0.81, 0.8])


def test_independent_single_factor_arm_reconstruction_changes_only_named_factor():
    module = runpy.run_path(str(ROOT / "research/analysis/evidence_v2.py"))
    old = dict(id="r14", heads=[[1, 2]], count=1, scope="question", mapping="soft", strength=1)
    new = dict(
        id="new", heads=[[3, 4], [5, 6]], count=2, scope="answer", mapping="hard80", strength=2
    )
    heads = module["expected_policy"]("heads_only", old, new)
    assert heads["heads"] == new["heads"] and heads["count"] == 2
    assert heads["mapping"] == "soft" and heads["scope"] == "question" and heads["strength"] == 1
    assert module["expected_policy"]("scope_only", old, new)["scope"] == "answer"
