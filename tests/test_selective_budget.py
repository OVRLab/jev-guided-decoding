import copy
import runpy
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[1] / "research/diagnostics/selective_budget.py"


def fixture():
    return [
        dict(
            case_id=str(i),
            family=domain,
            features=dict(min_probability=i / 8, mean_entropy=i / 4, copy_fraction=1.0),
            native_quality=0,
            guided_quality=int(i >= 4),
        )
        for domain in ("synthetic", "hotpot")
        for i in range(8)
    ]


def test_budget_selection_uses_development_benefit_with_feasible_call_counts():
    m = runpy.run_path(str(PATH))
    rows = fixture()
    selections = m["choose_budgets"](rows)
    assert [s["ceiling"] for s in selections] == [0.25, 0.5, 0.75]
    assert all(s["selected"]["call_fraction"] <= s["ceiling"] for s in selections)
    half = selections[1]["selected"]
    assert half["quality"] == 0.375
    assert half["call_fraction"] == 0.375
    assert half["gate"]["direction"] == "gt"


def test_budget_selection_can_reject_every_call_when_guidance_harms():
    m = runpy.run_path(str(PATH))
    rows = fixture()
    for r in rows:
        r["native_quality"], r["guided_quality"] = 1, 0
    assert all(s["selected"]["call_fraction"] == 0 for s in m["choose_budgets"](rows))


def test_replay_counts_discarded_pilot_and_two_prefills_only_when_called():
    m = runpy.run_path(str(PATH))
    native = dict(model_forwards=12, processed_tokens=111)
    guided = dict(model_forwards=6, processed_tokens=105)
    pilot = dict(model_forwards=8, processed_tokens=107, token_ids=list(range(8)))
    skip = m["branch_work"](False, native, guided, pilot)
    call = m["branch_work"](True, native, guided, pilot)
    assert skip == dict(model_forwards=12, processed_tokens=111, discarded_tokens=0, prefills=1)
    assert call == dict(model_forwards=14, processed_tokens=212, discarded_tokens=8, prefills=2)


def test_frozen_budget_selection_rejects_changed_rule_or_development():
    m = runpy.run_path(str(PATH))
    selected = {"gate_development": fixture(), "selected": {"policy": {"id": "fixture"}}}
    frozen = m["freeze_selection"](selected, "development-hash", "plan-hash")
    m["verify_selection"](frozen, selected, "development-hash", "plan-hash")
    bad = copy.deepcopy(frozen)
    bad["budgets"][0]["selected"]["gate"] = {"kind": "always"}
    with pytest.raises(ValueError, match="selection"):
        m["verify_selection"](bad, selected, "development-hash", "plan-hash")
    with pytest.raises(ValueError, match="selection"):
        m["verify_selection"](frozen, selected, "changed", "plan-hash")


def test_failed_request_keeps_native_pilot_and_does_not_charge_a_fresh_prefill():
    m = runpy.run_path(str(PATH))
    native = dict(model_forwards=12, processed_tokens=111)
    guided_fallback = dict(model_forwards=12, processed_tokens=111)
    pilot = dict(model_forwards=8, processed_tokens=107, token_ids=list(range(8)))
    result = m["branch_work"](True, native, guided_fallback, pilot, provider_failed=True)
    assert result == dict(model_forwards=12, processed_tokens=111, discarded_tokens=0, prefills=1)
