import json
import runpy
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[1] / "research/diagnostics/boundary_outputs.py"


def row(ident, text, grade, *, call=0, failed=False):
    return dict(
        case_id=ident,
        text=text,
        grade=grade,
        final={"finish_reason": "eos", "tokens": [{"active_heads": 0}], "token_ids": [1]},
        provider_status="failed_fallback" if failed else "unasked",
        logical_jev_calls=call,
        physical_jev_attempts=call,
    )


def test_squad_abstentions_empty_output_and_failure_remain_distinct():
    m = runpy.run_path(str(PATH))
    cases = {"a": {"missing": True}, "b": {"missing": False}, "c": {"missing": True}}
    rows = [
        row("a", "Not enough information.", {"abstained": True, "correct": 1}),
        row("b", "UNKNOWN", {"abstained": True, "correct": 0}, call=1, failed=True),
        row("c", "", {"abstained": False, "correct": 0}),
    ]
    got = m["describe"](rows, cases, "squad2")
    assert got["recognized_abstentions"] == 2
    assert got["natural_abstentions"] == 1 and got["bare_unknown"] == 1
    assert got["wrong_abstentions"] == 1 and got["empty_outputs"] == 1
    assert got["provider_fallbacks"] == got["logical_calls"] == 1


def test_call_diagnostics_use_quality_and_count_failed_attempts_as_calls():
    m = runpy.run_path(str(PATH))
    got = m["call_outcomes"]([0.2, 0.8, 0.5, 0.1], [0.4, 0.7, 0.5, 0.6], [1, 0, 1, 0])
    assert got == dict(
        called_beneficial=1,
        called_harmful=0,
        called_tied=1,
        skipped_beneficial=1,
        skipped_harmful=1,
        skipped_tied=0,
    )
    with pytest.raises(ValueError):
        m["call_outcomes"]([0.1], [0.2], [2])


def test_successful_noop_calls_are_separate_from_active_and_failed_calls():
    m = runpy.run_path(str(PATH))
    rows = [
        dict(
            case_id=str(i),
            logical_jev_calls=1,
            provider_status="complete" if i < 2 else "failed_fallback",
            final={
                "tokens": [{"active_heads": 11 if i == 1 else 0}],
                "token_ids": [2 if i == 1 else 1],
            },
        )
        for i in range(3)
    ]
    native = {str(i): {"final": {"token_ids": [1]}} for i in range(3)}
    got = m["intervention_outcomes"](rows, native)
    assert got == dict(
        successful_active_calls=1,
        successful_noop_calls=1,
        called_changed_token_paths=1,
        changed_token_paths=1,
    )


def test_artifact_binding_rejects_modified_audit_or_raw_bytes(tmp_path):
    m = runpy.run_path(str(PATH))
    results = tmp_path / "results"
    results.mkdir()
    raw = results / "outputs.jsonl"
    raw.write_text("{}\n")
    main = tmp_path / "main.json"
    main.write_text(json.dumps({"audit_passed": True}))
    cohort = tmp_path / "test.json"
    cohort.write_text("[]")
    binding = {
        "main_analysis_sha256": m["sha"](main),
        "test_cohort_sha256": m["sha"](cohort),
        "artifact_hashes": {"outputs.jsonl": m["sha"](raw)},
    }
    m["verify_binding"](binding, main, cohort, results)
    raw.write_text('{"changed":true}\n')
    with pytest.raises(ValueError, match="binding"):
        m["verify_binding"](binding, main, cohort, results)
    raw.write_text("{}\n")
    main.write_text(json.dumps({"audit_passed": False}))
    with pytest.raises(ValueError, match="binding"):
        m["verify_binding"](binding, main, cohort, results)


def test_diagnostics_reconstruct_grades_and_pick_first_id_independent_of_order(tmp_path):
    m = runpy.run_path(str(PATH))
    root = PATH.parents[2]
    d = runpy.run_path(str(root / "research/iterations/boundary_attention/data.py"))
    original = json.loads((root / "research/protocols/boundary-attention-v1/test.json").read_text())
    cases = [
        dict(next(c for c in original if c["family"] == family and not c["missing"]))
        for family in ("original", "hotpot", "squad2")
    ]
    cases.append(dict(cases[2], id="000-first-squad"))
    manifest = tmp_path / "manifest"
    manifest.mkdir()
    cohort = manifest / "test.json"
    cohort.write_text(json.dumps(cases))
    results = tmp_path / "results"
    results.mkdir()
    outputs = []
    arms = (
        "native",
        "always",
        "boundary_never",
        "boundary_always",
        "boundary_gate",
        "boundary_random",
        "pilot_gate",
        "lexical",
        "shuffled",
    )
    for c in reversed(cases):
        for arm in arms:
            text = c["reference"] if arm == "always" else "zzzz_unrelated_wrong_answer"
            outputs.append(
                dict(
                    row(c["id"], text, d["grade"](c, text)),
                    arm=arm,
                    stage="test",
                    features={},
                    call_decision=False,
                )
            )
    raw = results / "outputs.jsonl"
    raw.write_text("".join(json.dumps(r) + "\n" for r in outputs))
    main = tmp_path / "main.json"
    main.write_text(json.dumps({"audit_passed": True}))
    binding = {
        "main_analysis_sha256": m["sha"](main),
        "test_cohort_sha256": m["sha"](cohort),
        "artifact_hashes": {"outputs.jsonl": m["sha"](raw)},
    }
    report, examples = m["analyze"](manifest, results, main, binding)
    assert len(report["diagnostics"]) == 27 and report["new_api_calls"] == 0
    chosen = next(
        r
        for r in report["examples"]
        if r["domain"] == "squad2" and r["category"] == "Guidance improves quality"
    )
    assert chosen["case_id"] == "000-first-squad"
    assert "000-first-squad" in examples
    outputs[0]["grade"]["correct"] = 1 - outputs[0]["grade"]["correct"]
    raw.write_text("".join(json.dumps(r) + "\n" for r in outputs))
    binding["artifact_hashes"]["outputs.jsonl"] = m["sha"](raw)
    with pytest.raises(ValueError, match="grade reconstruction"):
        m["analyze"](manifest, results, main, binding)
