import runpy
from pathlib import Path

import pytest

summarize = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "research/analysis/trace_diagnostics.py")
)["summarize"]


def row(
    *,
    candidate="A useful deduction.</step>",
    finish="frame",
    judgments=None,
    valid=(0,),
    selected=None,
    stop="all_rejected",
    steps=(),
):
    entry = {
        "event": "proposal",
        "phase": "step",
        "valid_indices": list(valid),
        "selected_index": selected,
        "proposal": {
            "candidates": [
                {"text": candidate, "token_ids": [7], "finish_reason": finish, "mean_logprob": -0.1}
            ]
        },
    }
    if judgments is not None:
        entry["evaluation"] = {"judgments": judgments}
    return {
        "key": "synthetic/1|42|jev",
        "id": "synthetic/1",
        "mode": "jev",
        "result": {
            "mode": "jev",
            "steps": list(steps),
            "trace": [entry],
            "reasoning_stop_reason": stop,
            "stop_reason": "complete",
        },
    }


def judgment(support, progress):
    return {"support": support, "relevance": progress, "completion": None}


def test_unscored_eos_is_not_attributed_to_jev_rejection():
    r = row(candidate="", finish="eos", valid=(), stop="no_valid_step")
    group = summarize([r])["groups"]["synthetic/jev"]
    assert group["zero_step_stops"] == {"no_valid_step": 1}
    assert group["scored_batches"] == 0
    assert group["invalid_candidates"] == {"parse_failure": 1}
    assert group["candidate_finish_reasons"] == {"eos": 1}


def test_valid_supported_step_can_fail_only_the_progress_gate():
    r = row(judgments=[judgment(0.98, 0.04)])
    group = summarize([r])["groups"]["synthetic/jev"]
    assert group["zero_step_stops"] == {"all_rejected": 1}
    assert group["candidate_gates"] == {"progress_only": 1}
    assert group["rejected_batches_with_support_passing_candidate"] == 1
    assert group["initial_likelihood_winner_gate"] == {"progress_only": 1}


def test_accepted_weak_progress_is_not_hard_rejected():
    r = row(
        judgments=[judgment(0.9, 0.5)],
        selected=0,
        stop="step_budget",
        steps=("A useful deduction.",),
    )
    group = summarize([r])["groups"]["synthetic/jev"]
    assert group["accepted_steps"] == 1
    assert group["candidate_gates"] == {"eligible": 1}
    assert group["zero_step_stops"] == {}


def test_missing_or_malformed_judgments_fail_closed():
    with pytest.raises(ValueError, match="judgment count"):
        summarize([row(judgments=[])])
    with pytest.raises(ValueError, match="probability"):
        summarize([row(judgments=[judgment(float("nan"), 0.8)])])
    with pytest.raises(ValueError, match="unscored"):
        summarize([row()])


def test_trace_disagreement_and_duplicate_jobs_are_rejected():
    r = row(judgments=[judgment(0.98, 0.04)], selected=0)
    with pytest.raises(ValueError, match="selection"):
        summarize([r])
    r = row(judgments=[judgment(0.98, 0.04)])
    with pytest.raises(ValueError, match="duplicate"):
        summarize([r, r])


def test_gate_categories_preserve_all_scored_candidates():
    rows = []
    for i, (s, p) in enumerate(((0.1, 0.9), (0.1, 0.1), (0.9, 0.1))):
        r = row(judgments=[judgment(s, p)])
        r["key"] = f"synthetic/{i}|42|jev"
        rows.append(r)
    group = summarize(rows)["groups"]["synthetic/jev"]
    assert group["candidate_gates"] == {"both": 1, "progress_only": 1, "support_only": 1}
    assert group["scored_batches"] == 3
