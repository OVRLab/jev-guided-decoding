"""Exercise actual development orchestration with fake model/provider outcomes."""

import asyncio
import json
import runpy
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
HELPER = "research/iterations/evidence_v2_recovery2.py"


@pytest.mark.parametrize("partial", [False, True])
def test_development_saves_multiple_zero_checks_and_resumes_partial_block(tmp_path, partial):
    torch = pytest.importorskip("torch")
    ns = runpy.run_path(str(ROOT / HELPER))
    manifest = json.loads(
        (ROOT / "research/protocols/evidence-attention-v2/manifest.json").read_text()
    )
    worlds = json.loads(
        (ROOT / "research/protocols/evidence-attention-v2/development.json").read_text()
    )[:7]
    cases = [ns["D"]["context"](w, c) for w in worlds for c in ("clean", "distracted")]
    for name in ("starts", "inputs", "development", "development-scores"):
        (tmp_path / (name + ".jsonl")).touch()
    receipt_type = ns["E"]["RelevanceEvaluation"]

    class FakeScorer:
        model = manifest["jev_model"]
        budget = SimpleNamespace(unresolved=set())
        calls = []

        async def score(self, view, *, timeout):
            assert view["id"] not in self.calls
            self.calls.append(view["id"])
            return receipt_type(tuple(0.9 for _ in view["sources"]), self.model, 10, 0, 1, 0.01, {})

    scorer = FakeScorer()

    class FakeRunner(ns["RecoveryRunner"]):
        def encoded(self, case, highlights=None):
            return {}

        def forward(self, stage, case, mode, policy, scores, stream, **kwargs):
            self.start("model", stage, case["id"], mode)
            row = dict(
                id=case["id"],
                status="complete",
                mode=mode,
                correct=True,
                reference_logprob=-0.1,
                generated_token_ids=[1],
            )
            ns["append"](stream, row)
            return (row, torch.tensor([0.0, 1.0])) if kwargs.get("full_logits") else row

    if partial:
        ev = asyncio.run(scorer.score(ns["D"]["model_view"](cases[0]), timeout=90))
        with (tmp_path / "development-scores.jsonl").open("a") as f:
            ns["append"](
                f,
                dict(
                    id=cases[0]["id"], stage="development", status="complete", evaluation=asdict(ev)
                ),
            )
        runner = FakeRunner(None, tmp_path, manifest)
        with (tmp_path / "development.jsonl").open("a") as f:
            runner.forward("development", cases[0], "native", None, None, f)
        runner.close()
    runner = FakeRunner(None, tmp_path, manifest)
    try:
        asyncio.run(runner.development(cases, scorer))
    finally:
        runner.close()
    rows = [json.loads(x) for x in (tmp_path / "development.jsonl").read_text().splitlines()]
    assert len({(r["id"], r["mode"]) for r in rows}) == len(rows)
    assert len([r for r in rows if r["mode"] == "native"]) == len(cases)
    assert len(scorer.calls) == len(cases)
    assert len(json.loads((tmp_path / "zero-equivalence.json").read_text())) == 12
    assert (tmp_path / "selected-policy.json").exists()
