import json
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]


def module():
    return runpy.run_path(str(ROOT / "experiments/fixed_verdict_probe.py"))


def test_fresh_worlds_are_consistent_balanced_and_label_only():
    data = module()
    worlds = data["worlds"]()
    old = json.loads((ROOT / "experiments/proposal_worlds.json").read_text())
    assert len(worlds) == 6
    assert not {w["id"] for w in old} & {w["id"] for w in worlds}
    labels = [data["render"](w)["answers"][0] for w in worlds]
    assert all(labels.count(label) == 2 for label in ("ENTAILED", "CONTRADICTED", "UNKNOWN"))
    assert all("return only this label" in data["render"](w)["question"] for w in worlds)


def test_fixed_grader_preserves_planned_denominator_and_checks_problem_identity():
    data = module()
    grade = data["grade"]([])
    assert all(r["planned_runs"] == 6 and r["not_run"] == 6 for r in grade["summary"].values())
    case = data["render"](data["worlds"]()[0])
    row = {
        "id": case["id"],
        "seed": 42,
        "request": case,
        "result": {
            "mode": "fixed_jev",
            "phase": "complete",
            "text": case["answers"][0],
            "stop_reason": "complete",
        },
    }
    assert data["grade"]([row])["summary"]["fixed_jev"]["matching_verdicts"] == 1
    row["request"]["evidence"] = "Changed problem"
    with pytest.raises(ValueError, match="problem"):
        data["grade"]([row])
