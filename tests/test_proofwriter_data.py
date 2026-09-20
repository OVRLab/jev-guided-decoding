import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "proofwriter_data", Path(__file__).parents[1] / "experiments/proofwriter_data.py"
)
data = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(data)


def world():
    return {
        "id": "test-world",
        "theory": "A is red.",
        "triples": {"t1": {"text": "A is red.", "representation": '("A" "is" "red" "+")'}},
        "rules": {
            "r1": {
                "text": "Red things are blue.",
                "representation": '((("someone" "is" "red" "+")) -> ("someone" "is" "blue" "+"))',
            },
            "r2": {
                "text": "Blue and round things are green.",
                "representation": (
                    '((("something" "is" "blue" "+") ("something" "is" "round" "+"))'
                    ' -> ("something" "is" "green" "+"))'
                ),
            },
            "r3": {
                "text": "Green things are round.",
                "representation": (
                    '((("something" "is" "green" "+")) -> ("something" "is" "round" "+"))'
                ),
            },
        },
        "questions": {
            "q1": {
                "question": "A is not blue.",
                "representation": '("A" "is" "blue" "-")',
                "answer": False,
                "QDep": 1,
            },
            "q2": {
                "question": "A is green.",
                "representation": '("A" "is" "green" "+")',
                "answer": "Unknown",
                "QDep": 7,
            },
        },
    }


def test_symbolic_oracle_checks_explicit_negation_conjunction_and_unseeded_cycle():
    closure = data.derive(world())
    assert closure[("A", "is", "blue", "+")] == 1
    assert ("A", "is", "green", "+") not in closure
    assert data.case_from(world(), "q1")["label"] == "CONTRADICTED"
    assert data.case_from(world(), "q2")["depth"] is None


def test_wrong_source_label_is_rejected_and_model_inputs_exclude_annotations():
    w = world()
    w["questions"]["q1"]["answer"] = True
    with pytest.raises(ValueError, match="label"):
        data.case_from(w, "q1")
    case = data.case_from(world(), "q1")
    request = data.request_for(case)
    assert "q1" not in request.question and "QDep" not in request.evidence
    assert "A is not blue." in request.question


def test_representation_parser_rejects_junk_instead_of_executing_it():
    with pytest.raises(ValueError):
        data.atom('__import__("os").system("echo unsafe")')
    with pytest.raises(ValueError):
        data.rule('((("A" "is" "red" "+")) -> ("A" "is" "blue" "+")) trailing')


def test_owa_tilde_condition_requires_an_explicit_negative_fact():
    w = world()
    w["rules"]["r1"]["representation"] = (
        '((("someone" "is" "red" "~")) -> ("someone" "is" "blue" "+"))'
    )
    assert ("A", "is", "blue", "+") not in data.derive(w)
    w["triples"]["t1"]["representation"] = '("A" "is" "red" "-")'
    assert data.derive(w)[("A", "is", "blue", "+")] == 1


def test_claim_audit_does_not_call_unparsed_or_partial_reasoning_a_verified_proof():
    w = world()
    checks = data.audit_steps(
        w,
        [
            "Therefore, A is blue: the red rule applies.",
            "Therefore, A is green.",
            "Therefore, A is red.",
            "Therefore, permission is probably available.",
        ],
    )
    assert [r["status"] for r in checks] == ["supported_new", "unsupported", "premise", "unparsed"]
    assert all(r["full_inference_verified"] is False for r in checks)
