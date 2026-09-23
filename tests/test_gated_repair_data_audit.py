import copy
import hashlib
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    prompt = (
        "Which number?\n\nA. one\nB. two\n\nReason through the problem "
        "and finish with a separate line: Final: <letter>."
    )
    case = dict(id="arc/train/example", task="arc", split="train", origin="train/0", prompt=prompt)
    ref = dict(
        id=case["id"],
        prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
        kind="choice",
        choices=2,
        answer="B",
    )
    sources = {
        "arc/train": [
            dict(
                id="example",
                question="Which number?",
                answerKey="2",
                choices={"label": ["1", "2"], "text": ["one", "two"]},
            )
        ]
    }
    return [case], [ref], [dict(id=case["id"], target="Final: B")], sources


def test_source_audit_checks_relabeling_targets_and_exposure():
    mod = runpy.run_path(str(ROOT / "research/diagnostics/gated_repair_data_audit.py"))
    cases, refs, targets, sources = fixture()
    assert mod["audit_rows"](cases, refs, targets, sources, [])["cases"] == 1
    broken = copy.deepcopy(refs)
    broken[0]["answer"] = "A"
    with pytest.raises(ValueError):
        mod["audit_rows"](cases, broken, targets, sources, [])
    broken = copy.deepcopy(targets)
    broken[0]["target"] = "Final: A"
    with pytest.raises(ValueError):
        mod["audit_rows"](cases, refs, broken, sources, [])
    with pytest.raises(ValueError):
        mod["audit_rows"](cases, refs, targets, sources, ["WHICH NUMBER?"])


def test_source_audit_rejects_duplicate_or_foreign_references():
    mod = runpy.run_path(str(ROOT / "research/diagnostics/gated_repair_data_audit.py"))
    cases, refs, targets, sources = fixture()
    for invalid in (refs + [refs[0]], [{**refs[0], "id": "foreign"}]):
        with pytest.raises(ValueError):
            mod["audit_rows"](cases, invalid, targets, sources, [])
