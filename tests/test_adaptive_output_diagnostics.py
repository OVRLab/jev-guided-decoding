import hashlib
import json
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def module():
    return runpy.run_path(str(ROOT / "research/diagnostics/adaptive_output_diagnostics.py"))


def row(text, parsed, correct, finish="eos", status="complete"):
    return dict(
        stage="test",
        family="original",
        contract="open_explicit",
        arm="tuned",
        status=status,
        text=text,
        grade={"parsed": parsed, "correct": correct},
        phases=[{"phase": "final", "finish_reason": finish}],
    )


def test_natural_bare_and_harmful_abstentions_keep_failures_in_denominator():
    rows = [
        row("Insufficient evidence.", "UNKNOWN", 1),
        row(" UNKNOWN! ", "UNKNOWN", 1),
        row("The answer is unknown.", "UNKNOWN", 0),
        row("red", "red", 1),
        row("", None, 0, status="provider_failed"),
    ]
    summary = module()["describe"](rows)["original/open_explicit/tuned"]
    assert summary["outcomes"] == 5 and summary["complete"] == 4
    assert summary["recognized_abstentions"] == 3
    assert summary["bare_unknown_answers"] == 1
    assert summary["other_recognized_abstentions"] == 2
    assert summary["correct_abstentions"] == 2
    assert summary["abstentions_on_answerable_cases"] == 1
    assert summary["failed"] == 1


def test_budget_endings_are_recorded_without_regrading_completed_answers():
    rows = [row("red", "red", 1, "token_limit"), row("blue", "blue", 0)]
    rows[0]["phases"].insert(0, {"phase": "reasoning_1", "finish_reason": "newline"})
    summary = module()["describe"](rows)["original/open_explicit/tuned"]
    assert summary["final_endings"] == {"token_limit": 1, "eos": 1}
    assert summary["reasoning_endings"] == {"newline": 1}
    assert summary["correct_at_final_token_limit"] == 1
    assert summary["recognized_abstentions"] == 0


def test_diagnostics_reject_output_bytes_that_do_not_match_audit(tmp_path):
    output = tmp_path / "outputs.jsonl"
    output.write_text(json.dumps(row("red", "red", 1)) + "\n")
    audit = {
        "audit_passed": True,
        "artifact_hashes": {"outputs.jsonl": hashlib.sha256(b"other").hexdigest()},
    }
    with pytest.raises(ValueError, match="audited output"):
        module()["analyze"](output, audit)
