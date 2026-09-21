"""Serialization must preserve the original freeze bytes and reject real changes."""

import json
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_equivalent_tuple_list_does_not_rewrite_frozen_record(tmp_path):
    ns = runpy.run_path(str(ROOT / "research/iterations/evidence_v2_continuation2.py"))
    path = tmp_path / "test-freeze.json"
    path.write_text(
        json.dumps({"at": "old", "arms": ["native", "r15"], "selected_policy_sha256": "abc"})
    )
    before = path.read_bytes()
    ns["preserve_freeze"](
        path, {"at": "new", "arms": ("native", "r15"), "selected_policy_sha256": "abc"}
    )
    assert path.read_bytes() == before
    with pytest.raises(ValueError, match="change"):
        ns["preserve_freeze"](
            path, {"at": "new", "arms": ("native", "r15"), "selected_policy_sha256": "different"}
        )
    assert path.read_bytes() == before
