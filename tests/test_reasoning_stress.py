import runpy
from pathlib import Path

from test_proofwriter_data import data


def test_stress_worlds_have_independent_labels_depths_and_missing_premises():
    module = runpy.run_path(str(Path(__file__).parents[1] / "experiments/reasoning_stress.py"))
    cases = module["make_cases"]()
    assert len(cases) == 24 and len({c["theory_id"] for c in cases}) == 24
    assert cases == module["make_cases"]()
    assert {c["target_depth"] for c in cases} == {2, 4, 6, 7}
    for case in cases:
        checked = data.case_from(case["world"], "Q1")
        assert checked["label"] == case["label"]
        assert checked["depth"] == (None if case["label"] == "UNKNOWN" else case["target_depth"])
    assert {label: sum(c["label"] == label for c in cases) for label in data.LABELS} == {
        "ENTAILED": 8,
        "CONTRADICTED": 8,
        "UNKNOWN": 8,
    }
