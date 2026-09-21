import copy
import math
import runpy
from pathlib import Path

import pytest

A = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "research/analysis/evidence_attention.py")
)


def test_independent_decision_audit_rejects_token_and_probability_tampering():
    encoded = {"label_ids": [11, 12], "labels": ["red", "blue"], "prompt_digest": "abc"}
    row = {
        "generated_token_ids": [12],
        "label": "blue",
        "prompt_digest": "abc",
        "label_logits": [0.0, math.log(3)],
        "label_probabilities": [0.25, 0.75],
    }
    A["audit_decision"](row, encoded)
    for field, value in [
        ("generated_token_ids", [11]),
        ("label_probabilities", [0.5, 0.5]),
        ("label", "red"),
    ]:
        changed = copy.deepcopy(row)
        changed[field] = value
        with pytest.raises(ValueError):
            A["audit_decision"](changed, encoded)


def test_independent_bias_audit_rejects_wrong_heads_and_span_scores():
    encoded = {"span_token_indices": [[1, 2], [4]], "query_start": 6}
    row = {
        "heads": [[2, 3]],
        "strength": 2.0,
        "span_scores": [0.8, 0.2],
        "token_bias": {"1": 1.2, "2": 1.2},
        "hook_calls": 1,
    }
    A["audit_bias"](row, encoded, [[2, 3]], [0.8, 0.2], 2.0)
    changed = {**row, "token_bias": {"1": 1.2, "4": 1.2}}
    with pytest.raises(ValueError):
        A["audit_bias"](changed, encoded, [[2, 3]], [0.8, 0.2], 2.0)


def test_independent_graph_walk_is_not_a_room_frequency_vote():
    edges = [
        ["parcel a", "crate b"],
        ["crate b", "room red"],
        ["parcel c", "room blue"],
        ["parcel d", "room blue"],
    ]
    assert A["reference_for"]("parcel a", edges) == "red"
    assert A["reference_for"]("parcel absent", edges) == "UNKNOWN"


def test_visible_record_parser_preserves_containment_direction_in_both_templates():
    sources = [
        {"text": "The parcel a is inside the crate b."},
        {"text": "The room red contains the crate b."},
    ]
    edges = A["visible_edges"](sources)
    assert edges == [("parcel a", "crate b"), ("crate b", "room red")]
    assert A["reference_for"]("parcel a", edges) == "red"
    with pytest.raises(ValueError):
        A["visible_edges"]([{"text": "An unsupported rendering."}])
