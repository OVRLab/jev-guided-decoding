import runpy
from collections import Counter
from pathlib import Path

D = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "research/experiments/structured_data.py")
)


def test_new_worlds_are_balanced_independently_solved_and_split_disjoint():
    dev = D["worlds"]("development", 24)
    test = D["worlds"]("test", 300)
    assert Counter(c["reference_label"] for c in test) == {
        "TRUE": 100,
        "FALSE": 100,
        "UNKNOWN": 100,
    }
    assert len({c["id"] for c in dev + test}) == 324
    assert not {c["evidence"] for c in dev}.intersection(c["evidence"] for c in test)
    assert {c["depth"] for c in test} == {3, 5}
    for case in dev + test:
        assert D["truth"](case) == case["reference_label"]


def test_model_view_excludes_reference_and_rule_engine_internals():
    case = D["worlds"]("development", 1)[0]
    view = D["model_view"](case)
    assert set(view) == {"id", "evidence", "target", "entities", "properties"}
    case["reference_label"] = "deliberately changed"
    assert D["model_view"](case) == view
