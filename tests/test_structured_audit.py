import copy
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
A = runpy.run_path(str(ROOT / "experiments/analyze_structured_study.py"))
F = runpy.run_path(str(ROOT / "tests/test_structured_controller.py"))


def test_reconstruction_accepts_original_and_rejects_changed_prefix_or_final():
    row = F["run"]("jev", F["Scorer"]())
    assert A["audit_tokens"](row, F["Base"]())
    for mutate in (
        lambda r: r["steps"][0]["trace"][0].update(prefix_digest="wrong"),
        lambda r: r["final"]["candidate"].update(token_ids=(4, 10)),
        lambda r: r["steps"][0]["checkpoint"]["branches"][0].update(body="Mira is calm."),
    ):
        bad = copy.deepcopy(row)
        mutate(bad)
        with pytest.raises(ValueError):
            A["audit_tokens"](bad, F["Base"]())


def test_final_token_loop_prefix_is_audited_separately():
    row = F["run"]("native")
    row["final"]["token_trace"] = {"trace": [{"token": 9, "prefix_digest": "wrong"}]}
    with pytest.raises(ValueError, match="Final trace"):
        A["audit_tokens"](row, F["Base"]())


def test_confusion_diagnostics_retain_invalid_outputs():
    a = F["run"]("native")
    a.update(reference_label="FALSE", depth=3, motif="negative")
    b = F["run"]("native")
    b.update(reference_label="UNKNOWN", label=None, depth=5, motif="missing")
    result = A["diagnostics"]([a, b])
    assert result["confusion"]["native"] == {"FALSE": {"TRUE": 1}, "UNKNOWN": {"INVALID": 1}}
    assert result["strata"]["native"]["depth:5"] == {"jobs": 1, "correct": 0}


def test_input_audit_rejects_reused_id_with_changed_question_evidence_or_prompt():
    class Tokenizer:
        chat_template = "fixture"

        def apply_chat_template(self, messages, *, tokenize, add_generation_prompt):
            assert tokenize and add_generation_prompt
            return list("|".join(m["content"] for m in messages).encode())

    case = {"id": "same-id", "target": "Mira is blue.", "evidence": "Mira is calm."}
    manifest = {"system": "Frozen system instructions."}
    row = {
        "id": "same-id",
        "request": {
            "question": "Determine whether this target follows: Mira is blue.",
            "evidence": "Mira is calm.",
            "system": "Frozen system instructions.",
        },
        "prompt_ids": list(
            b"Frozen system instructions.|Evidence:\nMira is calm.\n\nQuestion:\n"
            b"Determine whether this target follows: Mira is blue."
        ),
    }
    assert A["audit_input"](row, case, manifest, Tokenizer())
    for field in ("question", "evidence", "system"):
        bad = copy.deepcopy(row)
        bad["request"][field] += " The answer is TRUE."
        with pytest.raises(ValueError, match="request"):
            A["audit_input"](bad, case, manifest, Tokenizer())
    bad = copy.deepcopy(row)
    bad["prompt_ids"].append(99)
    with pytest.raises(ValueError, match="prompt"):
        A["audit_input"](bad, case, manifest, Tokenizer())


def test_grade_audit_recomputes_accepted_claims_as_well_as_rejected_branches():
    case = {
        "facts": ["Mira is blue."],
        "rules": [],
        "entities": ["Mira"],
        "properties": ["blue", "calm"],
    }
    grade = A["STUDY"]["DATA"]["grade_claim"]
    row = {
        "steps": [
            {
                "text": "<step>Mira is blue.</step>",
                "oracle": grade(case, "Mira is blue."),
                "checkpoint": {
                    "branches": [{"body": "Mira is calm.", "oracle": grade(case, "Mira is calm.")}]
                },
            }
        ]
    }
    assert A["audit_grades"](row, case)
    bad = copy.deepcopy(row)
    bad["steps"][0]["oracle"]["correct"] = False
    with pytest.raises(ValueError, match="Accepted claim"):
        A["audit_grades"](bad, case)
    bad = copy.deepcopy(row)
    bad["steps"][0]["checkpoint"]["branches"][0]["oracle"]["correct"] = True
    with pytest.raises(ValueError, match="Branch"):
        A["audit_grades"](bad, case)
