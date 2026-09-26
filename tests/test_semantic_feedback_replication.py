import json
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
R = runpy.run_path(str(ROOT / "research/iterations/semantic_feedback_replication/study.py"))


def test_replication_worlds_are_fresh_and_old_freeze_still_verifies(tmp_path):
    old = json.loads((ROOT / "research/protocols/semantic-feedback-v1/cases.json").read_text())
    path = tmp_path / "replication"
    R["prepare"](path)
    new = json.loads((path / "cases.json").read_text())
    assert len(new) == 384
    assert {n for c in old for n in c["people"]}.isdisjoint(n for c in new for n in c["people"])
    assert {c["id"] for c in old}.isdisjoint(c["id"] for c in new)
    assert R["verify"](path)["cases"] == 384
    original = runpy.run_path(str(ROOT / "research/iterations/semantic_feedback/study.py"))
    assert original["verify"](ROOT / "research/protocols/semantic-feedback-v1")["cases"] == 192
    (path / "cases.json").write_text("[]")
    with pytest.raises(ValueError, match="freeze"):
        R["verify"](path)
