import copy
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def module():
    return runpy.run_path(str(ROOT / "research/diagnostics/adaptive_injection_audit.py"))


def record():
    return {
        "status": "complete",
        "contract": "open_neutral",
        "hook_calls": 2,
        "model_forwards": 2,
        "framing": [],
        "phases": [
            {
                "phase": "final",
                "token_ids": [10, 11],
                "tokens": [{"token_id": 10}, {"token_id": 11}],
                "maps": [{"head": [3, 1]}, {"head": [3, 2]}],
            }
        ],
    }


def test_injection_count_groups_heads_by_layer_and_rejects_unexercised_hook():
    m = module()
    row = record()
    assert m["check_injection_and_contract"](row)["hook_calls"] == 2
    bad = copy.deepcopy(row)
    bad["hook_calls"] = 0
    with pytest.raises(ValueError, match="injection count"):
        m["check_injection_and_contract"](bad)


def test_open_vocabulary_audit_rejects_hidden_answer_menu():
    row = record()
    row["phases"][0]["tokens"][0]["allowed_ids"] = [10, 11]
    with pytest.raises(ValueError, match="answer menu"):
        module()["check_injection_and_contract"](row)


def test_framing_audit_rejects_inserted_semantic_text():
    row = record()
    row["contract"] = "staged"
    row["framing"] = [{"name": "final cue", "token_ids": [99]}]

    class Tokenizer:
        def encode(self, text, **kwargs):
            return [8] if text == "\nFinal answer:" else [9]

    with pytest.raises(ValueError, match="framing"):
        module()["check_injection_and_contract"](row, tokenizer=Tokenizer())
