import copy
import runpy
from pathlib import Path

import pytest

HERE = Path(__file__).parents[1] / "research/iterations/routing_feedback"


def common():
    return runpy.run_path(str(HERE / "common.py"))


def fixture():
    ids = [f"case/{i}" for i in range(20)]
    return ids, {i: n / 20 for n, i in enumerate(ids)}, {i: -n - 1.0 for n, i in enumerate(ids)}


def test_routing_matches_counts_is_order_invariant_and_keeps_feedback_distribution():
    c = common()
    ids, probs, confidence = fixture()
    plan = c["make_plan"](ids, probs, confidence)
    assert plan == c["make_plan"](list(reversed(ids)), probs, confidence)
    for block in plan["blocks"]:
        assert len(block["ids"]) == 10
        assert all(len(block["selected"][s]) == 5 for s in ("jev", "confidence", "random"))
        selected = block["selected"]["jev"]
        assert all(
            probs[i] <= probs[j] for i in selected for j in block["ids"] if j not in selected
        )
        assert set(block["donors"]) == set(block["donors"].values()) == set(selected)
        assert all(i != d for i, d in block["donors"].items())
    assert len(plan["policies"]) == 7
    assert len(c["required_outputs"](plan)) == 60


def test_empty_answers_are_low_confidence_and_invalid_feedback_is_not_zero():
    c = common()
    ids, probs, conf = fixture()
    conf[ids[0]] = None
    p = c["make_plan"](ids, probs, conf)
    assert any(ids[0] in b["selected"]["confidence"] for b in p["blocks"])
    for value in (None, float("nan"), -0.1, True):
        with pytest.raises(ValueError):
            c["make_plan"](ids, probs | {ids[0]: value}, conf)
    with pytest.raises(ValueError):
        c["make_plan"](ids + [ids[0]], probs, conf)
    with pytest.raises(ValueError):
        c["make_plan"](ids, probs, {i: -1 for i in ids[1:]})


def test_case_contract_rejects_reference_leakage_and_spending_cap():
    c = common()
    case = dict(
        id="ifeval/1",
        task="ifeval",
        family="instruction_following",
        prompt="Say hi.",
        format="instruction",
        origin_id="1",
        cluster="ifeval/1",
        split="test",
    )
    c["validate_case"](case)
    with pytest.raises(ValueError):
        c["validate_case"](case | {"answer": "hi"})
    c["admit_cost"](103.82976781335556, 18.5, 125)
    for args in [(103.83, 22, 125), (float("nan"), 1, 125), (103, -1, 125)]:
        with pytest.raises(ValueError):
            c["admit_cost"](*args)


def test_selection_reconstructs_exact_outputs_and_refuses_missing_or_duplicates():
    c = common()
    ids, probs, conf = fixture()
    plan = c["make_plan"](ids, probs, conf)
    rows = [
        dict(id=i, arm=a, generated_token_ids=[n], correct=(n % 3 == 0))
        for n, (i, a) in enumerate(sorted(c["required_outputs"](plan)))
    ]
    out = c["select_outputs"](plan, rows)
    lookup = {(r["id"], r["arm"]): r for r in rows}
    for policy, records in out.items():
        assert len(records) == len(ids)
        for row in records:
            assert row == lookup[row["id"], plan["policies"][policy][row["id"]]]
    for bad in [rows[:-1], rows + rows[:1]]:
        with pytest.raises(ValueError):
            c["select_outputs"](plan, bad)
    changed = copy.deepcopy(plan)
    changed["policies"]["jev_live"][ids[0]] = "invented"
    with pytest.raises(ValueError):
        c["select_outputs"](changed, rows)


def test_paired_analysis_reports_wins_losses_and_rejects_unpaired_cases():
    c = common()
    out = c["paired"](
        [True, True, False, False], [False, True, True, False], [0, 0, 1, 1], draws=1000
    )
    assert out["delta_pp"] == 0 and out["wins"] == 1 and out["losses"] == 1
    assert out["ci9875_pp"][0] <= 0 <= out["ci9875_pp"][1]
    with pytest.raises(ValueError):
        c["paired"]([True], [False, True], [0])


def test_likelihood_observer_preserves_native_tokens_and_cleans_up():
    pytest.importorskip("torch")
    root = HERE.parents[2]
    tiny = runpy.run_path(str(root / "tests/test_evidence_attention.py"))["tiny"]
    tok = runpy.run_path(str(root / "tests/test_selective_benchmark_runtime.py"))["Tokenizer"]()
    r = runpy.run_path(str(HERE / "runtime.py"))
    model = tiny()
    args = dict(limit=4, eos=[31], seed=2801)
    before, _ = r["BASE"]["generate_batch"](model, tok, [[1, 2, 3]], **args)
    observed, work = r["generate"](model, tok, [1, 2, 3], observe=True, **args)
    assert observed["generated_token_ids"] == before[0]["generated_token_ids"]
    assert len(observed["log_probabilities"]) == len(observed["generated_token_ids"])
    assert observed["mean_log_probability"] <= 0
    assert work["forwards"] == len(observed["generated_token_ids"])
    assert not model._forward_hooks

    def expired():
        raise TimeoutError("expired")

    with pytest.raises(TimeoutError):
        r["generate"](model, tok, [1], observe=True, deadline=expired, **args)
    assert not model._forward_hooks


def test_feedback_failure_stops_with_reserved_charge_and_no_retry(tmp_path):
    import asyncio

    from jev_guided_decoding.experiment_budget import InputTokenBudget
    from jev_guided_decoding.types import ScorerError

    f = runpy.run_path(str(HERE / "feedback.py"))

    class Scorer:
        calls = 0

        async def _evaluate(self, *args, **kwargs):
            self.calls += 1
            raise ScorerError(
                "Jev request failed or timed out; it was not replayed",
                attempts=1,
                usage_unknown=True,
            )

    async def no_sleep(seconds):
        return None

    case = dict(
        id="case/1",
        task="ifeval",
        family="instruction_following",
        prompt="Say hi.",
        format="instruction",
        origin_id="1",
        cluster="case/1",
        split="test",
    )
    scorer = Scorer()
    with InputTokenBudget(tmp_path / "budget.jsonl", max_usd=0.25, usd_per_million=0.042) as budget:
        feedback = f["Feedback"](scorer, budget, tmp_path, sleep=no_sleep)
        with pytest.raises(RuntimeError, match="unresolved"):
            asyncio.run(feedback.score(case, "hi"))
        assert len(budget.unresolved) == 1 and budget.charged_tokens == 65536
        assert scorer.calls == 1


def test_audit_rejects_token_prefix_hook_and_coverage_tampering():
    audit = runpy.run_path(str(HERE / "audit.py"))

    class Tok:
        def decode(self, ids, skip_special_tokens=False):
            return " ".join(map(str, ids))

    row = dict(
        prompt_token_ids=[1, 2],
        generated_token_ids=[3, 9],
        text="3",
        finish_reason="eos",
        gate=0.5,
        events=[
            dict(layer=19, positions=[1], feedback=[0.5, 0.5], relative_delta=0.01),
            dict(layer=19, positions=[2], feedback=[0.5, 0.5], relative_delta=0.02),
        ],
        work=dict(
            batch_size=1,
            forwards=2,
            processed_token_slots=3,
            padded_prompt_tokens=2,
            generated_token_slots=2,
            seconds=0.2,
        ),
    )
    audit["check_row"](row, [1, 2], Tok(), [9], 2048, 0.5)
    for change in [
        dict(prompt_token_ids=[1, 4]),
        dict(text="4"),
        dict(events=[]),
        dict(finish_reason="length"),
        dict(gate=0.8),
        dict(work=row["work"] | {"processed_token_slots": 4}),
    ]:
        with pytest.raises(ValueError):
            audit["check_row"](row | change, [1, 2], Tok(), [9], 2048, 0.5)
    with pytest.raises(ValueError):
        audit["check_complete"]({"cases": 19, "expected_outputs": 60}, 20, 60)
