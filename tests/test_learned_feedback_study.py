import json
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
S = runpy.run_path(str(ROOT / "research/iterations/learned_feedback/study.py"))


def test_donor_mapping_never_uses_same_case_and_preserves_motif():
    cases = [{"id": str(i), "motif": str(i % 3)} for i in range(12)]
    donors = S["donor_map"](cases)
    assert set(donors) == {c["id"] for c in cases}
    assert all(k != v and int(k) % 3 == int(v) % 3 for k, v in donors.items())


def test_development_checkpoint_ties_prefer_first_and_cannot_use_test():
    assert S["choose_epoch"]([0.5, 0.5]) == 1
    assert S["choose_epoch"]([0.5, 0.6]) == 2
    with pytest.raises(ValueError):
        S["choose_epoch"]([0.5, float("nan")])


def test_analysis_pairs_seeds_by_world_and_rejects_missing_outputs():
    cases = [{"id": "a", "motif": "direct"}, {"id": "b", "motif": "passive"}]
    rows = []
    for c in cases:
        for mode, seed in S["ARMS"]:
            rows.append(
                {
                    "case_id": c["id"],
                    "mode": mode,
                    "seed": seed,
                    "grade": {"correct": mode == "live"},
                    "token_ids": [1],
                    "seconds": 0.1,
                    "forwards": 1,
                    "processed_tokens": 4,
                }
            )
    a = S["analyze"](cases, rows)
    assert a["contrasts"]["live-native"]["difference"] == 1.0
    assert a["worlds"] == 2
    with pytest.raises(ValueError, match="coverage"):
        S["analyze"](cases, rows[:-1])


def test_training_admission_must_bind_to_audited_artifact_bytes(tmp_path):
    admission = tmp_path / "admission"
    (admission / "replication").mkdir(parents=True)
    (admission / "replication/analysis.json").write_text(json.dumps({"admitted": True}))
    (admission / "replication-audit.json").write_text(
        json.dumps({"passed": True, "admitted": True})
    )
    with pytest.raises(ValueError, match="admission"):
        S["prepare"](tmp_path / "freeze", admission)
