import runpy
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "research/diagnostics/selective_outputs.py"


def test_descriptive_abstention_and_termination_counts_keep_distinct_failures():
    m = runpy.run_path(str(PATH))
    cases = {"a": {"missing": True}, "b": {"missing": False}, "c": {"missing": True}}
    rows = [
        {
            "case_id": "a",
            "text": "There is not enough information to determine the room.",
            "grade": {"parsed": "UNKNOWN", "correct": 1},
            "final": {"finish_reason": "eos"},
            "provider_status": "unasked",
            "logical_jev_calls": 0,
        },
        {
            "case_id": "b",
            "text": "UNKNOWN",
            "grade": {"parsed": "UNKNOWN", "correct": 0},
            "final": {"finish_reason": "eos"},
            "provider_status": "failed_fallback",
            "logical_jev_calls": 1,
        },
        {
            "case_id": "c",
            "text": "[E02] contains",
            "grade": {"parsed": None, "correct": 0},
            "final": {"finish_reason": "token_limit"},
            "provider_status": "complete",
            "logical_jev_calls": 1,
        },
    ]
    got = m["describe"](rows, cases)
    assert got["recognized_abstentions"] == 2 and got["natural_abstentions"] == 1
    assert got["bare_unknown"] == 1 and got["wrong_abstentions"] == 1
    assert got["unparsed"] == 1 and got["eos"] == 2 and got["token_limit"] == 1
    assert got["provider_fallbacks"] == 1 and got["logical_calls"] == 2
