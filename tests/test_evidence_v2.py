import copy
import math
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
P = runpy.run_path(str(ROOT / "research/iterations/evidence_v2/policies.py"))
D = runpy.run_path(str(ROOT / "research/iterations/evidence_v2/data.py"))


def test_fresh_worlds_are_balanced_disjoint_and_independently_grade_long_chains():
    used = {"alreadyused"}
    all_ids = set()
    for split, depths in [
        ("development", (1, 2, 3)),
        ("test", (1, 2, 3)),
        ("challenge", (4, 5, 6)),
    ]:
        worlds = D["worlds"](split, 12, used)
        assert {w["depth"] for w in worlds} == set(depths)
        assert len({w["id"] for w in worlds} & all_ids) == 0
        all_ids.update(w["id"] for w in worlds)
        for depth in depths:
            for missing in (False, True):
                assert sum(w["depth"] == depth and w["missing"] == missing for w in worlds) == 2
        for w in worlds:
            c = D["context"](w, "distracted")
            edges = dict(c["edges"])
            node = c["target"]
            while node in edges:
                node = edges[node]
            assert c["reference"] == (node[5:] if node.startswith("room ") else "UNKNOWN")
            assert len(c["sources"]) <= 24


def test_grid_contains_exact_r14_and_changes_are_explicit():
    ranking = [{"head": [i // 16, i % 16]} for i in range(640)]
    grid = P["grid"](ranking)
    assert len(grid) == len({p["id"] for p in grid}) == 90
    old = P["r14"](ranking)
    assert old in grid
    assert old["count"] == 8 and old["strength"] == math.log(8)
    assert old["mapping"] == "soft" and old["scope"] == "question"
    selected = {**old, "mapping": "hard80", "scope": "answer"}
    arms = P["arms"](old, selected)
    assert arms["mapping_only"]["mapping"] == "hard80"
    assert arms["mapping_only"]["scope"] == "question"
    assert arms["scope_only"]["mapping"] == "soft"
    assert arms["scope_only"]["scope"] == "answer"
    assert arms["zero"]["strength"] == 0


def test_mapping_thresholds_equal_scores_and_invalid_values():
    scores = [0.5, 0.8, 0.81]
    assert P["map_scores"](scores, "soft") == scores
    assert P["map_scores"](scores, "hard50") == [0, 1, 1]
    assert P["map_scores"](scores, "hard80") == [0, 0, 1]
    assert P["map_scores"]([0.9, 0.9], "hard80") == [1, 1]
    for bad in [[True], [float("nan")], [-0.1], [], [1.1]]:
        with pytest.raises(ValueError):
            P["map_scores"](bad, "soft")
    with pytest.raises(ValueError):
        P["map_scores"]([0.4], "invented")


def test_selection_preserves_class_floors_and_can_keep_previous_version():
    old = {"id": "r14", "count": 8, "strength": 2.0, "mapping": "soft", "scope": "question"}
    base = {"accuracy": 0.5, "answerable": 0.4, "missing": 0.6, "clean": 0.5, "mean_logprob": -1}
    prior = {"policy": old, **base}
    sacrificing = {"policy": {**old, "id": "bad"}, **base, "accuracy": 0.55, "answerable": 0.3}
    better = {"policy": {**old, "id": "better"}, **base, "accuracy": 0.52, "answerable": 0.44}
    assert P["select"]([prior, sacrificing], "r14")["selected"]["policy"]["id"] == "r14"
    result = P["select"]([prior, sacrificing, better], "r14")
    assert result["selected"]["policy"]["id"] == "better"
    assert result["candidates"][1]["eligible"] is False


def test_answer_scope_preserves_input_and_calls_original_runtime_with_exact_scores():
    module = runpy.run_path(str(ROOT / "research/iterations/evidence_v2/runtime.py"))

    class Fake:
        def forward(self, encoded, **kwargs):
            return {
                "status": "complete",
                "observed_input": copy.deepcopy(encoded),
                "kwargs": kwargs,
            }

    original = {"input_ids": [1, 2, 3, 4], "query_start": 2}
    policy = {"heads": [[1, 3]], "strength": math.log(8), "mapping": "hard80", "scope": "answer"}
    result = module["forward"](Fake(), original, policy, [0.2, 0.9])
    assert original["query_start"] == 2
    assert result["observed_input"]["query_start"] == 3
    assert result["kwargs"]["scores"] == [0, 1]
    assert result["query_start"] == 3
    native = module["forward"](Fake(), original, None, None)
    assert native["kwargs"]["heads"] is None


def test_planned_summary_keeps_missing_outcomes_and_paired_worlds():
    module = runpy.run_path(str(ROOT / "research/iterations/evidence_v2/study.py"))
    cases = [
        {"id": "a/c", "world_id": "a", "condition": "clean", "reference": "red"},
        {"id": "a/d", "world_id": "a", "condition": "distracted", "reference": "red"},
        {"id": "b/c", "world_id": "b", "condition": "clean", "reference": "UNKNOWN"},
        {"id": "b/d", "world_id": "b", "condition": "distracted", "reference": "UNKNOWN"},
    ]
    rows = [
        dict(id=c["id"], mode=arm, status="complete", label=c["reference"], seconds=0.1)
        for c in cases
        for arm in P["ARMS"]
    ]
    rows = [r for r in rows if not (r["mode"] == "r15" and r["id"] == "b/d")]
    result = module["summarize"](rows, cases, draws=100)
    assert result["arms"]["r15"]["accuracy"] == 0.75
    assert result["arms"]["r15"]["missing"] == 1
    assert result["primary"]["r14"]["difference"] == -0.25
    assert result["primary"]["r14"]["world_losses"] == 1
    assert result["advancement"] is False


def test_explicit_overload_retains_eight_dependents_and_never_retries_case(tmp_path, monkeypatch):
    import asyncio
    from dataclasses import dataclass

    from jev_guided_decoding.types import ScorerError

    module = runpy.run_path(str(ROOT / "research/iterations/evidence_v2/study.py"))

    async def no_wait(seconds):
        assert seconds >= 60

    monkeypatch.setattr(asyncio, "sleep", no_wait)

    @dataclass
    class Evaluation:
        scores: tuple
        model: str = "jev-1.13.0"
        input_tokens: int = 20
        output_tokens: int = 3
        attempts: int = 1
        seconds: float = 0.1
        raw_response: dict = None

    class Budget:
        unresolved = {}

    class Scorer:
        model = "jev-1.13.0"
        budget = Budget()
        calls = []

        async def score(self, view):
            self.calls.append(view["id"])
            if len(self.calls) == 1:
                raise ScorerError(
                    "overloaded",
                    attempts=1,
                    usage_unknown=True,
                    diagnostics={"status_code": 529, "retry_after_seconds": 1},
                )
            return Evaluation(tuple([0.9] + [0.1] * (len(view["sources"]) - 1)))

    class Runtime:
        def encode(self, view, highlights=None):
            return {
                "input_ids": [1, 2, 3],
                "query_start": 2,
                "labels": view["labels"],
                "prompt_digest": view["id"] + str(highlights),
            }

        def forward(self, encoded, **kwargs):
            return {
                "status": "complete",
                "label": "red",
                "label_probabilities": [1 / 7] * 7,
                "seconds": 0.1,
            }

    worlds = D["worlds"]("test", 6, set())
    cases = [D["context"](worlds[0], c) for c in ("clean", "distracted")]
    policy = P["r14"]([{"head": [i // 16, i % 16]} for i in range(640)])
    runner = module["Runner"](Runtime(), tmp_path, {"max_seconds": 100, "bootstrap_draws": 20})
    scorer = Scorer()
    try:
        result = asyncio.run(runner.evaluate(cases, policy, policy, scorer, stage="test"))
    finally:
        runner.close()
    assert scorer.calls == [c["id"] for c in cases]
    assert result["recorded"] == 24
    assert sum(a["failed"] for a in result["arms"].values()) == 8
    assert result["arms"]["native"]["complete"] == 2
    assert result["arms"]["r14"]["complete"] == 1


def test_real_tiny_runtime_answer_scope_keeps_prior_query_rows_causal(monkeypatch):
    torch = pytest.importorskip("torch")
    pytest.importorskip("transformers")
    tiny_runtime = runpy.run_path(str(ROOT / "tests/test_evidence_runtime.py"))["runtime"]()
    wrapper = runpy.run_path(str(ROOT / "research/iterations/evidence_v2/runtime.py"))
    case = D["context"](D["worlds"]("development", 6, set())[0], "clean")
    encoded = tiny_runtime.encode(D["model_view"](case))
    globals_ = tiny_runtime.attention.apply.__wrapped__.__globals__
    original_mask = globals_["steered_mask"]
    masks = []

    def capture(*args, **kwargs):
        value = original_mask(*args, **kwargs)
        if value is not None:
            masks.append(value.clone())
        return value

    monkeypatch.setitem(globals_, "steered_mask", capture)
    policy = dict(heads=[[0, 1]], count=1, strength=math.log(8), mapping="hard80", scope="answer")
    raw = [0.9] + [0.1] * (len(case["sources"]) - 1)
    before = {k: v.clone() for k, v in tiny_runtime.base.model.state_dict().items()}
    result = wrapper["forward"](tiny_runtime, encoded, policy, raw)
    length = len(encoded["input_ids"])
    assert result["query_start"] == length - 1
    assert encoded["query_start"] < length - 1
    causal = torch.full((length, length), torch.finfo(torch.float32).min).triu(1)
    torch.testing.assert_close(masks[0][0, 1, :-1], causal[:-1], rtol=0, atol=0)
    assert all(masks[0][0, 1, -1, k] > 0 for k in encoded["span_token_indices"][0])
    assert result["generated_token_ids"][0] in encoded["label_ids"]
    assert all(torch.equal(before[k], v) for k, v in tiny_runtime.base.model.state_dict().items())
    assert tiny_runtime.attention.active is False
