import copy
import runpy
from pathlib import Path

import pytest


def test_cuda_device_alias_is_normalized_without_mutating_record_or_accepting_cpu():
    namespace = runpy.run_path(
        str(
            Path(__file__).resolve().parents[1]
            / "research/diagnostics/audit_contextual_completion_v2.py"
        )
    )
    normalize = namespace["canonical_admission"]
    actual = dict(
        device="cuda:0", passed=True, backbone_before="unchanged", backbone_after="unchanged"
    )
    saved = copy.deepcopy(actual)
    result = normalize(actual)
    assert result == actual | dict(device="cuda")
    assert actual == saved and result is not actual
    assert normalize(dict(device="cuda")) == dict(device="cuda")
    for device in ("cpu", "mps", "cuda:1", "cuda:00", None):
        with pytest.raises(ValueError, match="device"):
            normalize(dict(device=device))
