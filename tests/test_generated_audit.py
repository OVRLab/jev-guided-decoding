import copy
import runpy
from pathlib import Path

import pytest

AUDIT = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "experiments/audit_generated_answers.py")
)


def row():
    ids = tuple(map(ord, "6</final>"))
    controls = tuple(map(ord, "<final>"))
    return {
        "result": {
            "mode": "single",
            "output_source": "granite_generated",
            "text": "6",
            "phase": "complete",
            "token_ids": controls + ids,
            "generated_token_ids": ids,
            "final_token_ids": ids,
            "final_raw_text": "6</final>",
            "steps": [],
            "generated_tokens": len(ids),
            "decode_token_slots": len(ids),
            "prefill_tokens": 8,
            "generation_seconds": 0.1,
            "api_calls": 0,
            "jev_input_tokens": 0,
            "jev_output_tokens": 0,
            "trace": [
                {
                    "event": "proposal",
                    "phase": "final",
                    "control_token_ids": controls,
                    "accepted_before": (),
                    "prefix_token_ids": controls,
                    "count": 1,
                    "greedy": True,
                    "selected_index": 0,
                    "proposal": {
                        "candidates": [
                            {"token_ids": ids, "text": "6</final>", "full_text": "<final>6</final>"}
                        ],
                        "generated_tokens": len(ids),
                        "decode_token_slots": len(ids),
                        "prefill_tokens": 8,
                        "seconds": 0.1,
                    },
                }
            ],
        }
    }


def test_independent_audit_reconstructs_generated_final_and_rejects_injected_answer():
    value = row()
    assert AUDIT["audit_row"](value, lambda ids: "".join(map(chr, ids)))["final_generations"] == 1
    changed = copy.deepcopy(value)
    changed["result"]["text"] = "999"
    with pytest.raises(ValueError):
        AUDIT["audit_row"](changed, lambda ids: "".join(map(chr, ids)))


def test_independent_audit_rejects_final_scoring_and_control_answer_tokens():
    value = row()
    value["result"]["trace"][0]["evaluation"] = {}
    with pytest.raises(ValueError):
        AUDIT["audit_row"](value, lambda ids: "".join(map(chr, ids)))
    value = row()
    value["result"]["trace"][0]["control_token_ids"] = tuple(map(ord, "<final>6"))
    with pytest.raises(ValueError):
        AUDIT["audit_row"](value, lambda ids: "".join(map(chr, ids)))


def test_audit_retains_a_budget_stop_before_any_generation():
    value = row()
    r = value["result"]
    r.update(
        phase="stopped",
        text="",
        trace=[],
        token_ids=(),
        generated_token_ids=(),
        final_token_ids=(),
        final_raw_text="",
        final_finish_reason="",
        generated_tokens=0,
        decode_token_slots=0,
        prefill_tokens=0,
        generation_seconds=0,
    )
    assert AUDIT["audit_row"](value, lambda ids: "".join(map(chr, ids))) == {}
