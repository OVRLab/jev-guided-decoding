import copy
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_binding_audit_rejects_substituted_memory_weights_feedback_and_missing_work():
    check = runpy.run_path(str(ROOT / "research/iterations/contextual_memory/checks.py"))[
        "check_bindings"
    ]
    row = dict(id="case", arm="contextual-scalar/3101", probabilities=[0.4] * 3, at="12:01")
    expected = {
        ("case", row["arm"]): dict(
            probabilities=[0.4] * 3, memory_digest="memory-one", adapter_digest="chosen-epoch"
        )
    }
    binding = dict(
        id="case", arm=row["arm"], **expected["case", row["arm"]], seconds=0.1, at="12:00"
    )
    assert check([row], [binding], expected) == pytest.approx(0.1)
    for field, replacement in (
        ("memory_digest", "different-memory"),
        ("adapter_digest", "wrong-epoch"),
        ("probabilities", [0.8] * 3),
        ("seconds", float("nan")),
    ):
        bad = copy.deepcopy(binding)
        bad[field] = replacement
        with pytest.raises(ValueError):
            check([row], [bad], expected)
    with pytest.raises(ValueError, match="coverage"):
        check([row], [], expected)
    with pytest.raises(ValueError, match="coverage"):
        check([row], [binding, binding], expected)
