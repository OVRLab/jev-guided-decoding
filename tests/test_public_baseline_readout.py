import runpy
from pathlib import Path

R = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "research/diagnostics/public_baseline_readout.py")
)
PROMPT = "Where?\n\nA. room one\nB. room two\nC. room three\n\nReason first."


def test_complete_option_match_needs_label_and_text():
    assert R["option_readout"](PROMPT, "A. room one\n\nReason: a story.") == "A"
    assert R["option_readout"](PROMPT, "**B. room two.**") == "B"
    assert R["option_readout"](PROMPT, "A. room two") is None
    assert R["option_readout"](PROMPT, "I think room one is where A might go.") is None


def test_ambiguous_multiple_options_are_not_guessed():
    assert R["option_readout"](PROMPT, "A. room one\nB. room two") is None
    assert R["option_readout"](PROMPT, "A. room one\nC. something else") is None


def test_later_explicit_final_keeps_primary_authority():
    ref = {"kind": "choice", "answer": "B", "choices": 3}
    g = R["readout"](PROMPT, "A. room one\nReconsider.\nFinal: B", ref)
    assert g["answer"] == "B" and g["method"] == "primary"
    assert g["correct"]
