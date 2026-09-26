import copy
import runpy
from pathlib import Path

import pytest

HERE = Path(__file__).parents[1] / "research/iterations/routing_feedback"


def fixture():
    names = [
        "native",
        "always_constant",
        "jev_constant",
        "confidence_constant",
        "random_constant",
        "jev_live",
        "jev_shuffled",
    ]
    scores = {
        name: dict(
            n=539,
            strict=100,
            loose=110,
            strict_pct=10000 / 539,
            instruction_strict=150,
            instruction_loose=160,
            instructions=700,
            repairs=0 if name == "native" else 539 if name == "always_constant" else 269,
            empty=0,
            length_stops=1,
            attributed_generated_tokens=2000,
            attributed_processed_slots=6000,
            attributed_generation_seconds=90,
        )
        for name in names
    }
    pairs = [
        ("jev_constant", "random_constant"),
        ("jev_constant", "confidence_constant"),
        ("jev_live", "jev_constant"),
        ("jev_live", "jev_shuffled"),
    ] + [(n, "native") for n in names if n != "native"]
    analysis = dict(
        protocol="r28-routing-feedback-v1",
        status="completed",
        cases=539,
        scores=scores,
        contrasts={
            a + "__" + b: dict(
                delta_pp=0,
                wins=1,
                losses=1,
                ci95_pp=[-1, 1],
                ci9875_pp=[-2, 2],
                block_delta_pp=[0, 0],
                practical_success=False,
            )
            for a, b in pairs
        },
        selection_pass=False,
        feedback_pass=False,
        integrity=dict(
            passed=True,
            cases=539,
            outputs=1616,
            policies=7,
            generated_tokens=3000,
            jev=dict(calls=539, charged_tokens=5000, usd=0.00021, unresolved=0, max_charged=0),
        ),
        random_100_seeds=dict(min_correct=90, max_correct=110, mean_correct=100),
        total_collected_generation_seconds=120,
    )
    cost = dict(
        instance_terminated=True,
        owned_disk_deleted=True,
        owned_security_group_deleted=True,
        owned_subnet_deleted=True,
        prior_conservative_usd=103.82976781335556,
        cumulative_cap_usd=125,
        compute_usd=6,
        api_usd=0.00021,
        preflight_usd=0.000015204,
        operating_allowance_usd=4.31,
        stage_conservative_usd=10.310225204,
        cumulative_conservative_usd=114.13999301735555,
    )
    return analysis, cost


def test_report_refuses_incomplete_or_unverified_cleanup_and_preserves_null_result():
    mod = runpy.run_path(str(HERE / "report.py"))
    analysis, cost = fixture()
    text = mod["render"](analysis, cost)
    assert "100/539" in text
    assert "Selection criterion: **not met**" in text
    assert "Internal-feedback criterion: **not met**" in text
    assert "does not establish equivalence" in text
    assert "not independently measured deployment" in text
    assert "$114.14 / $125" in text
    for update in [dict(status="running"), dict(cases=538), dict(integrity={"passed": False})]:
        with pytest.raises(ValueError):
            mod["render"](analysis | update, cost)
    for key in ["instance_terminated", "owned_disk_deleted", "owned_subnet_deleted"]:
        with pytest.raises(ValueError):
            mod["render"](analysis, cost | {key: False})
    changed = copy.deepcopy(analysis)
    changed["scores"]["jev_live"]["n"] = 538
    with pytest.raises(ValueError):
        mod["render"](changed, cost)
    with pytest.raises(ValueError):
        mod["render"](analysis, cost | {"cumulative_conservative_usd": 0})


def test_report_rejects_success_flags_that_disagree_with_registered_contrasts():
    mod = runpy.run_path(str(HERE / "report.py"))
    analysis, cost = fixture()
    with pytest.raises(ValueError):
        mod["render"](analysis | {"selection_pass": True}, cost)
    changed = copy.deepcopy(analysis)
    changed["contrasts"]["jev_live__jev_shuffled"]["practical_success"] = True
    with pytest.raises(ValueError):
        mod["render"](changed, cost)
