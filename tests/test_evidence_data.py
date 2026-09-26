import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
D = runpy.run_path(str(ROOT / "research/experiments/evidence_data.py"))


def test_fresh_balanced_worlds_graph_grading_and_public_view_excludes_oracle():
    all_ids = set()
    for split, count in [("profile", 24), ("calibration", 72), ("test", 360)]:
        worlds = D["worlds"](split, count)
        assert len(worlds) == count
        assert worlds == D["worlds"](split, count)
        assert sum(w["reference"] == "UNKNOWN" for w in worlds) == count // 2
        for w in worlds:
            assert w["id"] not in all_ids
            all_ids.add(w["id"])
            for condition in ("clean", "distracted"):
                c = D["context"](w, condition)
                assert D["grade"](c["target"], c["edges"]) == w["reference"]
                assert len(c["sources"]) == len(c["oracle_scores"])
                view = D["model_view"](c)
                assert set(view) == {"id", "question", "sources", "labels"}
                assert len(view["labels"]) == 7
                assert len(set(s["id"] for s in view["sources"])) == len(view["sources"])


def test_independent_grader_follows_bridges_missing_edges_and_cycles():
    assert D["grade"]("parcel", [("parcel", "box"), ("box", "room red")]) == "red"
    assert D["grade"]("parcel", [("other", "room red")]) == "UNKNOWN"
    assert D["grade"]("parcel", [("parcel", "box"), ("box", "parcel")]) == "UNKNOWN"
    with pytest.raises(ValueError):
        D["grade"]("parcel", [("parcel", "room red"), ("parcel", "room blue")])
