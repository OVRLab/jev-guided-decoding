"""Never replay a completed held-out job or an unavailable paid request."""

import asyncio
import json
import runpy
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]


def test_continuation_retains_503_and_finishes_only_unstarted_jobs(tmp_path):
    ns = runpy.run_path(str(ROOT / "research/iterations/evidence_v2_continuation.py"))
    m = json.loads((ROOT / "research/protocols/evidence-attention-v2/manifest.json").read_text())
    m["bootstrap_draws"] = 0
    worlds = json.loads((ROOT / "research/protocols/evidence-attention-v2/test.json").read_text())
    cases = [ns["D"]["context"](worlds[i // 2], ("clean", "distracted")[i % 2]) for i in range(3)]
    for n in ("starts", "inputs", "development-scores", "test", "test-scores"):
        (tmp_path / (n + ".jsonl")).touch()
    with (
        (tmp_path / "test.jsonl").open("a") as out,
        (tmp_path / "starts.jsonl").open("a") as starts,
    ):
        for mode in ns["P"]["ARMS"]:
            ns["append"](
                out, dict(id=cases[0]["id"], mode=mode, status="complete", label="red", seconds=0)
            )
            ns["append"](starts, dict(id=cases[0]["id"], stage="test", mode=mode, kind="model"))
        for case in cases[:2]:
            ns["append"](starts, dict(id=case["id"], stage="test", mode="relevance", kind="jev"))
    with (tmp_path / "test-scores.jsonl").open("a") as out:
        ns["append"](
            out,
            dict(
                id=cases[0]["id"],
                stage="test",
                status="complete",
                evaluation={"scores": [0.9] * len(cases[0]["sources"])},
            ),
        )
        ns["append"](
            out,
            dict(
                id=cases[1]["id"],
                stage="test",
                status="failed",
                status_code=503,
                usage_unknown=True,
                retry_after=None,
                message="Jev returned HTTP 503",
            ),
        )

    class FakeScorer:
        model = m["jev_model"]
        budget = SimpleNamespace(unresolved=set())
        calls = []

        async def score(self, view, *, timeout):
            self.calls.append(view["id"])
            return ns["E"]["RelevanceEvaluation"](
                tuple(0.9 for _ in view["sources"]), self.model, 10, 0, 1, 0.01, {}
            )

    class FakeRunner(ns["ContinuationRunner"]):
        def encoded(self, case, highlights=None):
            return {}

        def forward(self, stage, case, mode, policy, scores, stream, **kwargs):
            self.start("model", stage, case["id"], mode)
            row = dict(id=case["id"], mode=mode, status="complete", label="red", seconds=0)
            ns["append"](stream, row)
            return row

    runner, scorer = FakeRunner(None, tmp_path, m), FakeScorer()
    try:
        result = asyncio.run(
            runner.evaluate(cases, m["previous_policy"], m["previous_policy"], scorer, stage="test")
        )
    finally:
        runner.close()
    assert scorer.calls == [cases[2]["id"]]
    assert result["recorded"] == 36
    assert sum(a["failed"] for a in result["arms"].values()) == 8
    rows = [json.loads(x) for x in (tmp_path / "test.jsonl").read_text().splitlines()]
    assert len({(r["id"], r["mode"]) for r in rows}) == 36
    assert sum(r["status"] == "complete" for r in rows) == 28


def test_continuation_transient_budget_excludes_auth_and_unknown_contract_errors():
    ns = runpy.run_path(str(ROOT / "research/iterations/evidence_v2_continuation.py"))
    assert ns["recoverable"]({"status_code": 503}, 2)
    assert not ns["recoverable"]({"status_code": 503}, 30)
    assert not ns["recoverable"]({"status_code": 401}, 2)
    assert not ns["recoverable"](
        {
            "status_code": None,
            "usage_unknown": True,
            "message": "Unexpected model or attempt count",
        },
        2,
    )
