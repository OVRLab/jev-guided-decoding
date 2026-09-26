import json
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DATA = runpy.run_path(str(ROOT / "experiments/generated_answer_data.py"))
STUDY = runpy.run_path(str(ROOT / "experiments/generated_answer_study.py"))


def case(ident="one", task="gsm8k", answer="6"):
    return {
        "id": ident,
        "task": task,
        "question": "What is the total? Put only the number inside the final frame.",
        "evidence": "Two groups of three items.",
        "answer": answer,
        "source_id": ident,
        "evidence_sha256": DATA["digest_text"]("Two groups of three items."),
    }


def test_common_grader_reads_model_final_only_and_refuses_jev_rendered_output():
    c = case()
    good = {
        "text": "6.0",
        "phase": "complete",
        "output_source": "granite_generated",
        "final_token_ids": [1],
        "final_raw_text": "6.0</final>",
    }
    assert DATA["grade"](c, good)["correct"]
    assert not DATA["grade"](c, {**good, "text": "", "phase": "stopped", "steps": ["6"]})["correct"]
    with pytest.raises(ValueError, match="provenance"):
        DATA["grade"](c, {**good, "output_source": "jev_choice"})
    with pytest.raises(ValueError, match="provenance"):
        DATA["grade"](c, {**good, "final_token_ids": []})
    assert DATA["normalize_answer"]("gsm8k", "1,234.00") == "1234"
    for malformed in ["1,2", "6 or 7", "6 dollars", "NaN", "ENTAILED"]:
        assert DATA["normalize_answer"]("gsm8k", malformed) is None
    assert DATA["normalize_answer"]("proofwriter", "ENTAINED") is None


def test_gsm_selection_is_disjoint_and_answer_never_enters_prepared_input(tmp_path):
    path = tmp_path / "data.jsonl"
    path.write_text(
        "\n".join(
            json.dumps(
                {
                    "question": f"Question {n}?",
                    "answer": f"Secret reference calculation. #### {n + 10000}",
                }
            )
            for n in range(10)
        )
    )
    rows = DATA["load_gsm"](path, "train")
    excluded = {rows[0]["evidence_sha256"]}
    chosen = DATA["select_gsm"](rows, 4, excluded, 7)
    assert len({r["id"] for r in chosen}) == 4
    assert all(r["evidence_sha256"] not in excluded for r in chosen)
    assert chosen == DATA["select_gsm"](rows, 4, excluded, 7)
    for c in chosen:
        text = json.dumps(STUDY["prepared"](c))
        assert c["answer"] not in text and "Secret reference" not in text


def test_analysis_counts_missing_and_uses_same_generated_output_for_all_modes():
    c = case()
    rows = [
        {
            "key": f"one|42|{mode}",
            "id": "one",
            "seed": 42,
            "mode": mode,
            "request": STUDY["prepared"](c),
            "result": {
                "mode": mode,
                "text": "6",
                "phase": "complete",
                "output_source": "granite_generated",
                "final_token_ids": [1],
                "final_raw_text": "6</final>",
                "stop_reason": "complete",
                "steps": [],
                "trace": [],
            },
        }
        for mode in ("single", "jev")
    ]
    result = STUDY["analyze"]([c], [42, 43], rows)
    assert result["tasks"]["gsm8k"]["modes"]["jev"]["accuracy"] == 0.5
    assert result["tasks"]["gsm8k"]["modes"]["likelihood"]["missing"] == 2
    assert not result["study_complete"] and not result["positive_accuracy_evidence"]
    rows[0]["request"]["evidence"] = "Different problem"
    with pytest.raises(ValueError, match="identity"):
        STUDY["analyze"]([c], [42, 43], rows)


def test_jobs_rotate_modes_and_started_jobs_cannot_replay():
    jobs = STUDY["plan_jobs"]([case("a"), case("b")], [42, 43])
    assert len(jobs) == 12 and len({j["key"] for j in jobs}) == 12
    events = [{"event": "started", "key": jobs[0]["key"]}]
    remaining = STUDY["remaining_jobs"](jobs, events)
    assert jobs[0] not in remaining
    with pytest.raises(ValueError):
        STUDY["remaining_jobs"](jobs, events + events)


def test_numeric_normalization_never_rounds_model_output_into_reference():
    number = "123456789012345678901234567890123456789"
    assert DATA["normalize_answer"]("gsm8k", number) == number


def test_boolean_logic_contract_is_versioned_and_does_not_regrade_old_results():
    c = case(task="proofwriter", answer="ENTAILED")
    result = {
        "text": "TRUE",
        "phase": "complete",
        "output_source": "granite_generated",
        "final_token_ids": [1],
        "final_raw_text": "TRUE",
        "final_finish_reason": "eos",
    }
    assert DATA["grade"]({**c, "answer_format": "boolean-v2"}, result)["correct"]
    assert not DATA["grade"](c, result)["correct"]
    result["text"] = "ENTAINED"
    result["final_raw_text"] = "ENTAINED"
    assert not DATA["grade"]({**c, "answer_format": "boolean-v2"}, result)["correct"]
