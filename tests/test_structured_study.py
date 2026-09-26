import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
S = runpy.run_path(str(ROOT / "research/experiments/structured_study.py"))


def row(case, mode, seed=42):
    return dict(
        id=case["id"],
        mode=mode,
        seed=seed,
        status="complete",
        label=case["reference_label"],
        accepted_ids=[1],
        final=dict(candidate=dict(token_ids=[2])),
        steps=[],
        seconds=1.0,
        audit=dict(final_tokens=True, accepted_tokens=True, prompt=True),
    )


def test_missing_jobs_stay_in_denominator_and_duplicates_fail():
    cases = [dict(id="a", reference_label="TRUE"), dict(id="b", reference_label="FALSE")]
    rows = [row(cases[0], "native")]
    result = S["summarize"](rows, cases, [42], ["native"])
    assert result["arms"]["native"]["accuracy"] == 0.5
    assert result["missing"] == 1 and not result["admitted"]
    with pytest.raises(ValueError, match="Duplicate"):
        S["summarize"](rows + rows, cases, [42], ["native"])


def test_noop_disagreement_fails_operational_gate_even_when_labels_match():
    cases = [dict(id="a", reference_label="TRUE")]
    rows = [row(cases[0], "staged"), row(cases[0], "zero")]
    rows[1]["accepted_ids"] = [9]
    result = S["summarize"](rows, cases, [42], ["staged", "zero"])
    assert result["zero_identity"] == dict(matched=0, pairs=1)
    assert not result["admitted"]


def test_uncertainty_clusters_seeds_by_world_and_includes_failures():
    cases = [dict(id=str(i), reference_label="TRUE") for i in range(8)]
    rows = [row(c, m, s) for c in cases for m in ("native", "jev") for s in (1, 2, 3)]
    for r in rows:
        if r["mode"] == "jev" and int(r["id"]) < 4:
            r["label"] = "FALSE"
    result = S["summarize"](rows, cases, [1, 2, 3], ["native", "jev"], bootstrap=1000)
    contrast = result["contrasts"]["jev_minus_native"]
    assert contrast["difference"] == -0.5 and contrast["clusters"] == 8
    assert contrast["interval"][1] <= 0
