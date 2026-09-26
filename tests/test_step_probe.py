"""Offline checks for the deliberately narrow reasoning diagnostic."""

import asyncio
import json
import runpy
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).parents[1]


def probe():
    return runpy.run_path(str(ROOT / "experiments/step_probe.py"))


def fixture():
    return json.loads((ROOT / "experiments/step_cases.json").read_text())


def test_oracle_requires_every_conjunct_and_does_not_reverse_rules():
    close = probe()["closure"]
    assert close(["training"], [(["training", "approval"], "badge")]) == {"training"}
    assert close(["badge"], [(["training"], "badge")]) == {"badge"}
    assert close(["a"], [(["a"], "b"), (["b"], "a"), (["b"], "c")]) == {"a", "b", "c"}


def test_oracle_does_not_promote_a_contaminated_prefix_to_evidence():
    case = fixture()["cases"][-1]
    assert all(not row["valid"] for row in probe()["oracle"](case))


def test_valid_intermediate_step_and_irrelevant_truth_are_distinct():
    case = fixture()["cases"][-2]
    labels = probe()["oracle"](case)
    assert labels == [
        {"valid": True, "progress": False, "eligible": False},
        {"valid": True, "progress": True, "eligible": True},
        {"valid": False, "progress": False, "eligible": False},
    ]


def test_request_builders_do_not_send_oracle_labels_or_other_candidates():
    data = fixture()
    case = data["cases"][0] | {"expected": "PRIVATE_REFERENCE_CANARY"}
    for mode in ("answer", "step"):
        payload = probe()["make_payload"](data["atoms"], case, mode)
        encoded = json.dumps(payload)
        assert "PRIVATE_REFERENCE_CANARY" not in encoded
        assert "expected" not in encoded
        assert "candidates" not in payload["state"]
        question = payload["questions"]["support_0"]
        assert "Mira is blocked from the archive" not in json.dumps(question)


def test_granite_request_contains_only_the_problem_and_step_instructions():
    data = fixture()
    case = data["cases"][0] | {"expected": "PRIVATE_REFERENCE_CANARY"}
    request = probe()["reasoning_request"](data["atoms"], case)
    assert "Step:" in request.system and "Final:" in request.system
    assert "PRIVATE_REFERENCE_CANARY" not in str(request)
    assert "Mira is blocked from the archive" not in str(request)
    assert "Fact: Mira completed orientation" in request.evidence


@pytest.mark.parametrize("value", [True, -0.1, 1.1, float("nan"), "0.9"])
def test_invalid_provider_probabilities_are_not_judgments(value):
    with pytest.raises(ValueError):
        probe()["probability"]({"type": "noul", "noul": value})


def test_selection_keeps_all_rejected_and_uses_a_stable_tie_break():
    select = probe()["select"]
    assert select([(0.5, 0.99), (0.99, 0.5)]) is None
    assert select([(0.9, 0.9), (0.9, 0.9)]) == 0
    assert select([(0.99, 0.6), (0.8, 0.8)]) == 1


def test_http_failure_is_recorded_without_retry_or_response_body(tmp_path):
    calls = []

    def respond(request):
        calls.append(request)
        return httpx.Response(529, text="PRIVATE_ERROR_CANARY")

    job = probe()["jobs"](fixture())[0]
    rows = asyncio.run(
        probe()["collect"]([job], tmp_path / "run", "synthetic-key", httpx.MockTransport(respond))
    )
    assert len(calls) == 1
    assert rows[0]["status"] == "http_error"
    assert rows[0]["usage_unknown"] is True
    saved = (tmp_path / "run/runs.jsonl").read_text()
    assert "PRIVATE_ERROR_CANARY" not in saved
    assert "synthetic-key" not in saved


def test_probe_refuses_excess_requests_and_existing_output_before_network(tmp_path):
    call = probe()["collect"]
    with pytest.raises(ValueError, match="16"):
        asyncio.run(call([{}] * 17, tmp_path / "new", "synthetic-key"))
    with pytest.raises(FileExistsError):
        asyncio.run(call([], tmp_path, "synthetic-key"))


def test_ambiguous_timeout_is_not_replayed_or_reported_as_zero_usage(tmp_path):
    calls = []

    def timeout(request):
        calls.append(request)
        raise httpx.ReadTimeout("PRIVATE_ERROR_CANARY")

    job = probe()["jobs"](fixture())[0]
    rows = asyncio.run(
        probe()["collect"]([job], tmp_path / "run", "synthetic-key", httpx.MockTransport(timeout))
    )
    assert len(calls) == 1
    assert rows[0]["status"] == "transport_error"
    assert rows[0]["usage_unknown"] is True
    assert "PRIVATE_ERROR_CANARY" not in (tmp_path / "run/runs.jsonl").read_text()
    summary = probe()["summarize"](rows)["answer"]
    assert summary["unscored_cases"] == 1
    assert summary["usage_unknown"] is True
