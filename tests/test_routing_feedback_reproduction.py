import runpy
from pathlib import Path

import pytest

HERE = Path(__file__).parents[1] / "research/iterations/routing_feedback"


def test_reproduction_separates_reference_metadata_and_preserves_question_order():
    module = runpy.run_path(str(HERE / "reproduce.py"))
    rows = [
        dict(
            key=i,
            prompt=f"Question {i}",
            instruction_id_list=["keywords:existence"],
            kwargs=[{"keywords": ["hello"]}],
        )
        for i in [4, 1122, 5, 1129]
    ]
    cases, refs = module["build_inputs"](rows, excluded={1122, 1129})
    assert [c["id"] for c in cases] == ["ifeval/4", "ifeval/5"]
    assert all(
        set(c) == {"id", "task", "family", "prompt", "format", "origin_id", "cluster", "split"}
        for c in cases
    )
    assert [r["prompt"] for r in refs] == [r["prompt"] for r in cases]
    assert all("kwargs" in r and "prompt_sha256" in r for r in refs)
    with pytest.raises(ValueError):
        module["build_inputs"](rows + rows[:1], excluded=set())


def test_public_numeric_export_rejects_text_and_keeps_only_allowed_fields():
    module = runpy.run_path(str(HERE / "reproduce.py"))
    grade = dict(
        id="ifeval/4",
        arm="native",
        strict=True,
        loose=True,
        instruction_strict=[True],
        instruction_loose=[True],
    )
    assert module["public_grade"](grade) == grade
    for change in [dict(text="PRIVATE ANSWER"), dict(strict=0.5), dict(id="../secret")]:
        with pytest.raises(ValueError):
            module["public_grade"](grade | change)
