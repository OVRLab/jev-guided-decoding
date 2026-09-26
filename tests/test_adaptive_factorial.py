import asyncio
import hashlib
import json
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def module():
    return runpy.run_path(str(ROOT / "research/iterations/adaptive_attention_factorial.py"))


def test_factorial_has_six_new_corners_and_never_replays_primary_corners():
    m = module()
    policies = m["factorial_policies"]()
    assert len(policies) == 8
    assert len(m["new_policies"]()) == 6
    assert set(policies) - set(m["new_policies"]()) == {"s0-h0-t0", "s1-h1-t1"}
    assert policies["s1-h1-t1"]["weights"][6] == 0
    assert sum(w > 0 for w in policies["s1-h1-t1"]["weights"]) == 11


def test_replay_rejects_unseen_payload_and_preserves_failed_receipt(tmp_path):
    m = module()
    view = {
        "id": "x",
        "family": "hotpot",
        "question": "Where?",
        "sources": [{"id": "E1", "text": "A fact."}],
    }
    payload = m["S"]["payload_for"](view, "jev-1.13.0")
    key = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    path = tmp_path / "receipts.jsonl"
    receipt = {"key": key, "payload": payload, "status": "failed", "usage_unknown": True}
    path.write_text(json.dumps(receipt) + "\n")
    replay = m["Replay"](path)
    assert asyncio.run(replay.get(view)) == receipt
    with pytest.raises(ValueError, match="unseen"):
        asyncio.run(replay.get({**view, "question": "Different?"}))
