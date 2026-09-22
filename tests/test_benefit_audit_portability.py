import copy
import math
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_portable_features_only_accept_one_ulp_for_the_two_logarithms():
    s = runpy.run_path(str(ROOT / "research/diagnostics/benefit_sufficiency_audit.py"))
    expected = [0.1, 0.2, 0.3, math.log1p(3), math.log1p(10), 0.4]
    recorded = expected.copy()
    recorded[3] = math.nextafter(recorded[3], math.inf)
    s["validate_feature_roundtrip"](recorded, expected)
    for index, steps in ((3, 2), (4, 2), (0, 1), (1, 1), (2, 1), (5, 1)):
        changed = expected.copy()
        for _ in range(steps):
            changed[index] = math.nextafter(changed[index], math.inf)
        with pytest.raises(ValueError, match="feature"):
            s["validate_feature_roundtrip"](changed, expected)
    for changed in ([*expected[:-1], float("nan")], expected[:-1]):
        with pytest.raises(ValueError, match="feature"):
            s["validate_feature_roundtrip"](changed, expected)


def test_portable_output_adapter_preserves_raw_records_and_original_rejections():
    s = runpy.run_path(str(ROOT / "research/diagnostics/benefit_sufficiency_audit.py"))
    expected = [0.1, 0.2, 0.3, math.log1p(3), math.log1p(10), 0.4]
    recorded = expected.copy()
    recorded[4] = math.nextafter(recorded[4], math.inf)
    row = {"features": {}, "benefit_features": recorded, "token_valid": False}
    original = copy.deepcopy(row)

    def reject_token(value, *args):
        assert value["benefit_features"] == expected
        if not value["token_valid"]:
            raise ValueError("Original token check rejected tampering")

    checker = s["guarded_checker"](reject_token, lambda *args: expected)
    with pytest.raises(ValueError, match="Original token check"):
        checker(row, {}, {}, None, {})
    assert row == original
