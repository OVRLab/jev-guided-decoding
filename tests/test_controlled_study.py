import asyncio
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
from test_fixed_verdict_cli import Client
from test_proofwriter_data import data, world
from test_reasoning_cli import backend as backend

SPEC = importlib.util.spec_from_file_location(
    "controlled_study", Path(__file__).parents[1] / "experiments/controlled_study.py"
)
study = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(study)


def test_planned_jobs_pair_all_modes_and_seeds_and_never_replay_started_work():
    cases = [data.case_from(world(), "q1")]
    jobs = study.plan_jobs(cases, [42, 43, 44])
    assert len(jobs) == 9 and len({j["key"] for j in jobs}) == 9
    assert study.remaining_jobs(jobs, [{"event": "started", "key": jobs[0]["key"]}]) == jobs[1:]
    with pytest.raises(ValueError, match="Duplicate"):
        study.remaining_jobs(jobs, [{"event": "started", "key": jobs[0]["key"]}] * 2)


def test_analysis_retains_missing_attempts_and_does_not_multiply_sample_size_by_seeds():
    cases = [data.case_from(world(), "q1")]
    request = study.prepared(cases[0])
    rows = [
        {
            "id": cases[0]["id"],
            "seed": 42,
            "request": request,
            "result": {
                "mode": "direct_jev",
                "text": "CONTRADICTED",
                "phase": "complete",
                "stop_reason": "complete",
                "steps": [],
                "reasoning_outcome": None,
            },
        }
    ]
    result = study.analyze(cases, [42, 43], rows)
    assert result["independent_problems"] == 1
    assert result["modes"]["direct_jev"]["correct"] == 1
    assert result["modes"]["direct_jev"]["planned"] == 2
    assert result["modes"]["direct_jev"]["accuracy"] == 0.5
    assert not result["study_complete"]
    assert result["modes"]["fixed_jev"]["missing"] == 2
    rows[0]["request"]["evidence"] = "A different problem"
    with pytest.raises(ValueError, match="identity"):
        study.analyze(cases, [42, 43], rows)


def test_paired_interval_groups_seeds_at_problem_level():
    result = study.paired_interval([1.0] * 20)
    assert result["difference"] == 1.0
    assert result["ci_97_5"] == [1.0, 1.0]
    assert result["wins"] == 20 and result["losses"] == 0
    assert study.paired_interval([0] * 20)["ci_97_5"] == [0, 0]


def test_fixed_generated_answer_is_a_separate_control_not_the_final_choice():
    case = data.case_from(world(), "q1")
    rows = [
        {
            "id": case["id"],
            "seed": 42,
            "request": study.prepared(case),
            "result": {
                "mode": "unguided_fixed_jev",
                "text": "CONTRADICTED",
                "phase": "complete",
                "stop_reason": "complete",
                "steps": [],
                "reasoning_outcome": {"text": "UNKNOWN", "phase": "complete", "mode": "likelihood"},
            },
        }
    ]
    result = study.analyze([case], [42], rows)
    assert result["modes"]["unguided_fixed_jev"]["correct"] == 1
    assert result["modes"]["granite_alone"]["correct"] == 0
    assert result["modes"]["granite_alone"]["completed"] == 1


def test_runner_records_all_arms_once_and_rejects_concurrent_or_modified_runs(
    backend, monkeypatch, tmp_path
):
    case = data.case_from(world(), "q1")
    cases = json.dumps(case) + "\n"
    (tmp_path / "cases.jsonl").write_text(cases)
    protocol = {
        "source_hashes": study.source_hashes(),
        "dataset_sha256": hashlib.sha256(cases.encode()).hexdigest(),
        "jobs": study.plan_jobs([case], [42]),
        "max_active_seconds": 1000,
        "max_api_calls": 30,
        "config": {
            "model": {"model_id": "fake"},
            "reasoning": {"max_resamples": 0, "prompt_style": "examples"},
            "verdict": {},
            "jev": {},
        },
    }
    (tmp_path / "protocol.json").write_text(json.dumps(protocol))
    monkeypatch.setattr(study, "load_api_key", lambda: "fake")
    monkeypatch.setattr(study, "VerdictScorer", Client)
    assert asyncio.run(study.execute(tmp_path)) == 0
    before = (tmp_path / "runs.jsonl").read_bytes()
    assert len(study.read_lines(tmp_path / "runs.jsonl")) == 3
    assert asyncio.run(study.execute(tmp_path)) == 0
    assert (tmp_path / "runs.jsonl").read_bytes() == before
    (tmp_path / "running.lock").write_text("123")
    with pytest.raises(FileExistsError):
        asyncio.run(study.execute(tmp_path))
    assert (tmp_path / "running.lock").read_text() == "123"
    (tmp_path / "cases.jsonl").write_text(cases + "\n")
    with pytest.raises(ValueError, match="dataset changed"):
        asyncio.run(study.execute(tmp_path))
