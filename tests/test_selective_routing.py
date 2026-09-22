import runpy
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[1] / "research/diagnostics/selective_routing.py"


def test_budget_matched_random_expectation_exposes_useful_routing():
    pytest.importorskip("numpy")
    m = runpy.run_path(str(PATH))
    rows = [
        {"world": "a", "native": 0, "guided": 1, "called": True},
        {"world": "b", "native": 1, "guided": 0, "called": False},
    ]
    result = m["routing_value"](rows)
    assert result["call_fraction"] == 0.5
    assert result["gate_quality"] == 1
    assert result["expected_random_quality"] == 0.5
    assert result["routing_value"] == 0.5
    assert result["worlds"] == 2


@pytest.mark.parametrize("called", [True, False])
def test_all_or_no_calls_have_zero_routing_value(called):
    pytest.importorskip("numpy")
    m = runpy.run_path(str(PATH))
    rows = [
        {"world": str(i // 2), "native": i % 2, "guided": 1 - i % 2, "called": called}
        for i in range(12)
    ]
    result = m["routing_value"](rows)
    assert result["routing_value"] == 0
    assert result["interval"] == [0, 0]
    assert result["permutation_one_sided_p"] == 1
    assert result["worlds"] == 6
