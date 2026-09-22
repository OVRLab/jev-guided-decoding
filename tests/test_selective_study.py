import copy
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "research/iterations/selective_attention"


def module(name):
    return runpy.run_path(str(HERE / f"{name}.py"))


def test_new_worlds_exclude_prior_names_and_balance_relation_depth_and_missing():
    d = module("data")
    dev, test = d["synthetic"]("development", 36), d["synthetic"]("test", 36)
    assert len(dev) == 36 and len(test) == 72
    assert not {c["target"] for c in dev} & {c["target"] for c in test}
    for family in ("original", "paraphrase", "dependency"):
        group = [c for c in test if c["family"] == family and c["condition"] == "heavy"]
        assert {(c["depth"], c["missing"]) for c in group} == {
            (i, b) for i in range(1, 7) for b in (True, False)
        }
    assert all(d["OLD"]["visible_reference"](c) == c["reference"] for c in dev + test)
    assert all(set(d["public_view"](c)) == {"id", "question", "sources", "family"} for c in test)


def test_schedule_is_complete_and_prospective_gate_runs_before_always_control():
    s, d = module("study"), module("data")
    cases = d["synthetic"]("test", 36)
    jobs = s["schedule"](cases)
    assert len(jobs) == len(cases) * len(s["ARMS"])
    assert len({(j["case_id"], j["arm"]) for j in jobs}) == len(jobs)
    for c in cases:
        arms = [j["arm"] for j in jobs if j["case_id"] == c["id"]]
        assert arms[0] == "benefit_gate"
        assert set(arms) == set(s["ARMS"])


def test_offline_audit_rejects_token_and_skipped_call_tampering():
    a = module("analyze")
    encoded = {"input_ids": [1, 2, 3], "prompt_digest": "p"}
    token = dict(
        token_id=7,
        argmax_id=7,
        selected_logit=1.0,
        top_ids=[7, 8],
        top_logits=[1.0, 0.5],
        probability=0.2,
        entropy=2.0,
        strength=0.0,
        active_heads=0,
        hook_calls=0,
    )
    final = dict(
        token_ids=[7],
        tokens=[token],
        input_and_output_ids=[1, 2, 3, 7],
        text="7",
        model_forwards=1,
        hook_calls=0,
        processed_tokens=3,
        prompt_tokens=3,
        finish_reason="eos",
        model_seconds=0.01,
    )
    row = dict(
        status="complete",
        final=final,
        pilot=copy.deepcopy(final),
        pilot_reused=True,
        gate={"kind": "never"},
        features={},
        call_decision=False,
        logical_jev_calls=0,
        receipt_key=None,
        model_forwards=1,
        prompt_digest="p",
        text="7",
        guided_path=False,
        intervention_used=False,
        applied_scores=None,
        provider_status="unasked",
        policy=None,
    )
    a["check_output"](row, encoded, None)
    changed = copy.deepcopy(row)
    changed["final"]["tokens"][0]["argmax_id"] = 8
    with pytest.raises(ValueError):
        a["check_output"](changed, encoded, None)
    changed = copy.deepcopy(row)
    changed["receipt_key"] = "a-hidden-call"
    with pytest.raises(ValueError):
        a["check_output"](changed, encoded, None)
