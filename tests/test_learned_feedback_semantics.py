import runpy
from pathlib import Path

M = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "research/diagnostics/learned_feedback_semantics.py")
)


def test_complete_color_readout_does_not_complete_or_extract_wrong_partial_answers():
    for text in (
        "red",
        "RED.",
        '"red"',
        "**red**",
        "The badge is red.",
        "It is red.",
        "a red badge",
    ):
        assert M["extract_color"](text) == "red"
    for text in (
        "[E02]",
        "not red",
        "red or blue",
        "The badge is",
        "red, but actually blue",
        "The courier is red",
        "red badge and blue hat",
    ):
        assert M["extract_color"](text) is None
