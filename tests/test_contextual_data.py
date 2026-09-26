import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "research/iterations"


def load():
    return runpy.run_path(str(HERE / "contextual_memory/data.py"))


def test_contextual_cohort_is_balanced_disjoint_and_independently_solvable():
    old = runpy.run_path(str(HERE / "structured_correction/common.py"))["make_data"]()[0]
    pairing = runpy.run_path(str(HERE / "feedback_pairing/common.py"))["worlds"]()[0]
    replay = runpy.run_path(str(HERE / "structured_correction/audit.py"))["replay_reference"]
    cases, refs = load()["make_data"]()
    assert len(cases) == len(refs) == 832
    assert {c["prompt"] for c in cases}.isdisjoint(c["prompt"] for c in old + pairing)
    assert len({c["id"] for c in cases}) == len({c["prompt"] for c in cases}) == 832
    for split, n in (("train", 512), ("development", 64), ("test", 256)):
        subset = [c for c in cases if c["split"] == split]
        assert len(subset) == n
        assert sum(c["task"] == "temporal" for c in subset) == n // 2
    assert all(replay(c) == refs[c["id"]] for c in cases)


def test_contextual_data_rejects_unbalanced_or_previously_exposed_worlds():
    m = load()
    with pytest.raises(ValueError, match="even"):
        m["make_data"](sizes=(3, 2, 2))
    # R30's first worlds are exactly reconstructed by this deliberately wrong seed.
    with pytest.raises(ValueError, match="overlap"):
        m["make_data"](sizes=(2, 2, 2), seed=30001)
