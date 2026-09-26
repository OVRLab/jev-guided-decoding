import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load():
    return runpy.run_path(str(ROOT / "research/diagnostics/musr_groups.py"))


def record(context, question, *, story=42):
    return dict(
        context=context,
        questions=[
            dict(
                question=question,
                choices=["Alice", "Bob"],
                answer=0,
                intermediate_data=[dict(story_hash_id=story)],
            )
        ],
    )


def test_author_scenario_groups_survive_changed_text_and_labels():
    m = load()
    a, b = record("first version", "who?"), record("counterfactual", "who?")
    b["questions"][0]["answer"] = 1
    groups = m["source_groups"]("murder_mystery", [a, b])
    assert len(groups) == 2 and len(set(groups.values())) == 1
    c = record("unrelated", "who?", story=99)
    assert len(set(m["source_groups"]("murder_mystery", [a, b, c]).values())) == 2
    del a["questions"][0]["intermediate_data"][0]["story_hash_id"]
    with pytest.raises(ValueError):
        m["source_groups"]("murder_mystery", [a])


def test_shared_narratives_and_team_groups_ignore_hidden_truth():
    m = load()
    a, b = record("same story", "where Alice?"), record("same story", "where Bob?")
    assert len(set(m["source_groups"]("object_placements", [a, b]).values())) == 1
    for row in (a, b):
        row["questions"][0]["intermediate_data"] = [
            dict(
                tasks=["task one", "task two"],
                matrix={"Alice": [1, 0], "Bob": [0, 1]},
                best_pair=[0],
            )
        ]
    b["context"] = "another telling"
    b["questions"][0]["intermediate_data"][0]["matrix"] = {"Bob": [1, 0], "Alice": [0, 1]}
    b["questions"][0]["intermediate_data"][0]["best_pair"] = [1]
    assert len(set(m["source_groups"]("team_allocation", [a, b]).values())) == 1


def test_source_binding_rejects_duplicates_and_absent_rows():
    m = load()
    a = record("context", "question")
    with pytest.raises(ValueError, match="Duplicate"):
        m["source_groups"]("murder_mystery", [a, a])
    groups = m["source_groups"]("murder_mystery", [a])
    rows = [dict(narrative="context", question="question", choices="['Alice', 'Bob']")]
    joined = m["bind_rows"]("murder_mystery", rows, groups)
    assert set(joined) == {"musr/murder_mystery/0"}
    with pytest.raises(ValueError, match="source"):
        m["bind_rows"]("murder_mystery", [rows[0] | {"question": "unmatched"}], groups)
