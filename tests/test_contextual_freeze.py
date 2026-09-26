import json
import runpy
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1] / "research/iterations/contextual_memory"


def test_freeze_rejects_budget_source_contract_and_inventory_changes(tmp_path, monkeypatch):
    c = runpy.run_path(str(HERE / "contract.py"))
    namespace = c["prepare"].__globals__
    # Explicitly synthetic lineage; no paid worker or research output in this test.
    monkeypatch.setitem(
        namespace,
        "lineage",
        lambda: dict(prior_conservative_usd=122.0, cumulative_cap_usd=175, synthetic_test=True),
    )
    monkeypatch.setitem(namespace, "sources", lambda: {"fixture.py": "bound"})
    monkeypatch.setitem(
        namespace, "admission_input", lambda: dict(case={"id": "exposed"}, native={"text": "test"})
    )
    monkeypatch.setattr(
        namespace["subprocess"],
        "check_output",
        lambda args, **kw: "" if "status" in args else "a" * 40,
    )
    folder = tmp_path / "frozen"
    namespace["prepare"](folder)
    m = namespace["verify"](folder)
    assert m["planned_outputs"] == 11840 and m["planned_cases"] == 832
    assert m["informative"] == "both" and m["stage_reserve_usd"] == 16
    original = (folder / "manifest.json").read_text()
    for field, value in (
        ("api_cap_usd", 999),
        ("limit", 129),
        ("epochs", 3),
        ("seeds", [1, 2]),
        ("layer", 18),
    ):
        changed = json.loads(original)
        changed[field] = value
        (folder / "manifest.json").write_text(json.dumps(changed))
        with pytest.raises(ValueError, match="contract"):
            namespace["verify"](folder)
    (folder / "manifest.json").write_text(original)
    (folder / "extra.txt").write_text("unexpected")
    with pytest.raises(ValueError, match="inventory"):
        namespace["verify"](folder)
    (folder / "extra.txt").unlink()
    monkeypatch.setitem(namespace, "sources", lambda: {"fixture.py": "changed"})
    with pytest.raises(ValueError, match="source"):
        namespace["verify"](folder)
    monkeypatch.setitem(
        namespace, "lineage", lambda: dict(prior_conservative_usd=170.0, cumulative_cap_usd=175)
    )
    with pytest.raises(ValueError, match="budget"):
        namespace["prepare"](tmp_path / "over-budget")
