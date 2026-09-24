import copy
import runpy
from pathlib import Path

import pytest

PATH = Path(__file__).parents[1] / "research/evaluation/tranche_report_v1.py"


def fixture(m):
    summary = dict(
        correct=50,
        total=198,
        accuracy=50 / 198,
        wilson_95=[0.2, 0.3],
        unparseable=0,
        length_stops=0,
        unfinished_thinking=0,
    )
    untouched = summary | dict(total=196, accuracy=50 / 196)
    return dict(
        admitted=True,
        audited_records=True,
        tokenizers_checked=True,
        quality=dict(
            summaries={s: {"gpqa_diamond": summary} for s in m["SYSTEMS"]},
            paired_differences={},
            grades={"secret-case": {"answer": "PRIVATE EXAMPLE"}},
        ),
        untouched_quality=dict(
            summaries={s: {"gpqa_diamond": untouched} for s in m["SYSTEMS"]},
            paired_differences={},
        ),
        raw_payload="PRIVATE EXAMPLE",
    )


def test_export_omits_examples_and_requires_all_full_comparisons():
    m = runpy.run_path(str(PATH))
    a = fixture(m)
    result = m["quality_export"](a, tasks=["gpqa_diamond"])
    assert "PRIVATE EXAMPLE" not in str(result) and "secret-case" not in str(result)
    assert result["full"]["summaries"]["guided"]["gpqa_diamond"]["total"] == 198
    assert result["untouched"]["summaries"]["guided"]["gpqa_diamond"]["total"] == 196
    for flag in ("admitted", "audited_records", "tokenizers_checked"):
        with pytest.raises(ValueError, match="audit"):
            m["quality_export"](a | {flag: False}, tasks=["gpqa_diamond"])
    bad = copy.deepcopy(a)
    del bad["quality"]["summaries"]["self_refine"]
    with pytest.raises(ValueError, match="systems"):
        m["quality_export"](bad, tasks=["gpqa_diamond"])


def test_partial_or_invalid_counts_never_become_full_results():
    m = runpy.run_path(str(PATH))
    for edit in (dict(total=197), dict(correct=199), dict(accuracy=0.99)):
        a = copy.deepcopy(fixture(m))
        a["quality"]["summaries"]["guided"]["gpqa_diamond"].update(edit)
        with pytest.raises(ValueError):
            m["quality_export"](a, tasks=["gpqa_diamond"])
    a = fixture(m)
    a["quality"]["summaries"]["guided"]["gpqa_diamond"]["unparseable"] = "PRIVATE EXAMPLE"
    with pytest.raises(ValueError):
        m["quality_export"](a, tasks=["gpqa_diamond"])


def test_cost_sums_parallel_stages_once_and_requires_cleanup():
    m = runpy.run_path(str(PATH))
    stages = [
        dict(name="gpqa", resource_seconds=3600, rate_usd_hour=2, jev_usd=0.01, deleted=True),
        dict(name="short", resource_seconds=7200, rate_usd_hour=2, jev_usd=0.02, deleted=True),
    ]
    value = m["reconcile_cost"](47.4, stages, cap=110)
    assert value["cumulative_usd"] == pytest.approx(53.43)
    with pytest.raises(ValueError, match="duplicate"):
        m["reconcile_cost"](47.4, stages * 2, cap=110)
    with pytest.raises(ValueError, match="cleanup"):
        m["reconcile_cost"](47.4, [stages[0] | {"deleted": False}], cap=110)
    with pytest.raises(ValueError, match="cap"):
        m["reconcile_cost"](109, stages, cap=110)
