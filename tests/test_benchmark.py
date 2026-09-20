import json

import pytest

from jev_guided_decoding.benchmark import answer_metrics, load_cases


def test_lexical_metrics_penalize_extra_words_and_accept_reference_variants():
    assert answer_metrics("East Gate!", ["The east gate."])["exact_match"] == 1
    assert answer_metrics("East gate and some invented detail.", ["East gate."])["token_f1"] < 1
    assert answer_metrics("", ["East gate."])["token_f1"] == 0


def test_reference_answers_are_required(tmp_path):
    path = tmp_path / "cases.jsonl"
    path.write_text(json.dumps({"id": "1", "question": "Q", "evidence": "E", "answers": []}))
    with pytest.raises(ValueError, match="reference answers"):
        load_cases(path)


def test_fixture_ids_are_unique():
    from pathlib import Path

    cases, digest = load_cases(Path(__file__).parents[1] / "data/grounded-smoke.jsonl")
    assert len(cases) == 12
    assert len(digest) == 64
