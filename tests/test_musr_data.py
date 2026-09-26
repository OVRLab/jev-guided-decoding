import runpy
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1] / "research/iterations/musr_transfer"


def test_exposure_excludes_whole_scenario_and_references_never_enter_cases():
    m = runpy.run_path(str(HERE / "data.py"))
    rows, groups = [], {}
    for i in range(4):
        choices = ["pantry", "pantry ", "hall"] if i == 3 else ["room", "hall"]
        row = dict(
            narrative=f"Story variant {i}",
            question="Which room?",
            choices=repr(choices),
            answer_index="1",
            answer_choice=choices[1],
        )
        rows.append(row)
        sig = m["G"]["signature"](row["narrative"], row["question"], choices)
        groups[sig] = "murder_mystery/" + str(i // 2)
    result = m["bind"]("murder_mystery", rows, groups, {"musr/murder_mystery/0"})
    assert len(result["cases"]) == 3
    assert [c["split"] for c in result["cases"]] == ["development", "test", "test"]
    assert result["excluded_related_ids"] == ["musr/murder_mystery/1"]
    assert result["ambiguous_choice_ids"] == ["musr/murder_mystery/3"]
    for case in result["cases"]:
        assert set(case) == {"id", "task", "split", "context", "question", "choices"}
        assert result["references"][case["id"]] == 1
    assert set(result["case_groups"]) == set(result["references"])
    assert result["case_groups"]["musr/murder_mystery/0"] not in {
        result["case_groups"][c["id"]] for c in result["cases"] if c["split"] == "test"
    }
    with pytest.raises(ValueError, match="exposure"):
        m["bind"]("murder_mystery", rows, groups, {"absent"})
    rows[-1]["answer_choice"] = "different"
    with pytest.raises(ValueError, match="reference"):
        m["bind"]("murder_mystery", rows, groups, set())
