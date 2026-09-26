import copy
import runpy
from pathlib import Path

import pytest

PATH = Path(__file__).parents[1] / "research/diagnostics/completed_granite_audit_v1.py"


def fixture():
    cases = {k: dict(id=k, task="gpqa_diamond", split="test") for k in ("a", "b")}
    rows = [
        dict(model=model, arm=arm, id=ident)
        for model, arm in [
            ("granite_4_0_1b", "native"),
            ("granite_4_0_1b", "self_refine"),
            ("granite_4_2_3b", "native"),
        ]
        for ident in cases
    ]
    rows.append(dict(model="qwen3_4b_instruct", arm="native", id="a"))
    lost = [dict(model="qwen3_4b_instruct", arm="native", ids=["b"])]
    return cases, rows, lost


def test_complete_granite_scope_keeps_qwen_partial_and_refuses_missing_granite():
    m = runpy.run_path(str(PATH))
    cases, rows, lost = fixture()
    coverage = m["check_scope"](cases, rows, lost)
    assert coverage["gpqa_diamond"]["granite_4_2_3b"] == 2
    assert coverage["gpqa_diamond"]["qwen3_4b_instruct"] == 1
    for bad in (rows[1:], rows + [rows[0]], rows + [dict(model="unknown", arm="native", id="a")]):
        with pytest.raises(ValueError):
            m["check_scope"](cases, bad, lost)


def test_unfinished_granite_or_saved_qwen_job_is_never_excused():
    m = runpy.run_path(str(PATH))
    cases, rows, lost = fixture()
    for bad in (
        [lost[0] | dict(model="granite_4_2_3b")],
        [lost[0] | dict(ids=["a"])],
        lost * 2,
    ):
        with pytest.raises(ValueError, match="unfinished"):
            m["check_scope"](cases, rows, bad)


def test_completed_model_needs_matching_weight_evidence():
    m = runpy.run_path(str(PATH))
    profile = dict(id="synthetic", revision="fixed")
    hardware = dict(profile=profile, original_weights_sha256="original")
    complete = dict(weights_unchanged=True, weights_sha256="original")
    m["check_weights"](profile, hardware, complete)
    for bad in (
        {},
        complete | dict(weights_unchanged=False),
        complete | dict(weights_sha256="changed"),
    ):
        with pytest.raises(ValueError, match="weight"):
            m["check_weights"](profile, hardware, bad)


def test_selection_keeps_native_tokens_and_rejects_tampered_or_missing_control():
    m = runpy.run_path(str(PATH))
    cases, rows, _ = fixture()
    for row in rows:
        row.update(generated_token_ids=[9], gate=None)
    donors = {"a": "b", "b": "a"}
    feedback = {i: dict(actual_probability_correct=0.8) for i in cases}
    decisions = {
        (arm, i): dict(
            arm=arm,
            donor_id=donors[i],
            probability_correct=0.8,
            repair_executed=False,
            selected_arm="native",
            decision="retain_native",
            gate=None,
            selected_tokens_sha256=m["C"]["digest"]("[9]"),
        )
        for arm in m["A"]["ARMS"]
        for i in cases
    }
    selected = m["select_complete"](cases, rows, decisions, feedback, donors)
    assert selected["guided"]["a"] is selected["original"]["a"]
    broken = copy.deepcopy(decisions)
    broken[("live", "a")]["selected_tokens_sha256"] = "changed"
    with pytest.raises(ValueError, match="provenance"):
        m["select_complete"](cases, rows, broken, feedback, donors)
    del broken[("blind", "a")]
    with pytest.raises(ValueError, match="coverage"):
        m["select_complete"](cases, rows, broken, feedback, donors)


def test_evaluator_binding_checks_code_environment_and_language_seed(tmp_path):
    m = runpy.run_path(str(PATH))
    evaluator, requirements = tmp_path / "evaluator.py", tmp_path / "requirements.txt"
    evaluator.write_text("pass\n")
    requirements.write_text("fake==1\n")
    manifest = dict(
        external_evaluation=dict(
            ifbench_evaluator_sha256=m["C"]["sha"](evaluator),
            ifbench_environment_sha256=m["C"]["sha"](requirements),
            language_seed=2701,
        )
    )
    m["check_evaluator"](manifest, evaluator, requirements)
    requirements.write_text("fake==2\n")
    with pytest.raises(ValueError, match="evaluator"):
        m["check_evaluator"](manifest, evaluator, requirements)


def test_public_export_preserves_full_denominators_and_drops_private_fields():
    m = runpy.run_path(str(PATH))
    row = dict(
        correct=50,
        total=198,
        accuracy=50 / 198,
        wilson_95=[0.2, 0.3],
        unparseable=0,
        length_stops=0,
        unfinished_thinking=0,
    )
    q = dict(
        summaries={s: {"gpqa_diamond": row} for s in m["SYSTEMS"]},
        paired_differences={},
        grades={"PRIVATE CASE": "PRIVATE ANSWER"},
    )
    value = dict(
        audited_records=True,
        tokenizers_checked=True,
        completed_scope_admitted=True,
        quality=q,
        untouched_quality=copy.deepcopy(q),
    )
    for s in value["untouched_quality"]["summaries"].values():
        s["gpqa_diamond"] = row | dict(total=196, accuracy=50 / 196)
    result = m["public_quality"](value, tasks=["gpqa_diamond"])
    assert "PRIVATE" not in str(result)
    assert result["full"]["summaries"]["guided"]["gpqa_diamond"]["total"] == 198
    for change in ("missing", "qwen", "denominator", "not_audited"):
        bad = copy.deepcopy(value)
        if change == "missing":
            del bad["quality"]["summaries"]["blind"]
        elif change == "qwen":
            bad["quality"]["summaries"]["qwen3_4b_instruct"] = {"gpqa_diamond": row}
        elif change == "denominator":
            bad["quality"]["summaries"]["guided"]["gpqa_diamond"]["total"] = 197
        else:
            bad["completed_scope_admitted"] = False
        with pytest.raises(ValueError):
            m["public_quality"](bad, tasks=["gpqa_diamond"])
