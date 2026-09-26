import copy
import runpy
from pathlib import Path

import pytest

PATH = Path(__file__).parents[1] / "research/diagnostics/selective_admission_audit.py"


def module():
    return runpy.run_path(str(PATH))


def test_batch_audit_counts_padding_and_rejects_missing_or_forged_work():
    m = module()
    rows = [
        dict(id="a", batch_id="b", prompt_token_ids=[1, 2], generated_token_ids=[5, 9]),
        dict(id="b", batch_id="b", prompt_token_ids=[3], generated_token_ids=[9]),
    ]
    batch = dict(
        batch_id="b",
        batch_size=2,
        padded_prompt_tokens=4,
        forwards=2,
        processed_token_slots=6,
        generated_token_slots=4,
        seconds=1.5,
    )
    assert m["check_batch"](batch, rows)["actual_generated_tokens"] == 3
    with pytest.raises(ValueError, match="work"):
        m["check_batch"](batch | {"processed_token_slots": 5}, rows)
    with pytest.raises(ValueError, match="work"):
        m["check_batch"](batch, rows[:1])


def test_selection_audit_catches_fabricated_skips_and_wrong_control_gates():
    m = module()
    native = dict(arm="native", generated_token_ids=[4, 9])
    repaired = dict(arm="constant", generated_token_ids=[5, 9], gate=0.5)
    row = dict(
        arm="constant",
        selected_arm="native",
        repair_executed=False,
        decision="retain_native",
        probability_correct=0.8,
        gate=None,
        selected_tokens_sha256=m["C"]["digest"]("[4, 9]"),
    )
    assert m["check_selection"](row, native, None, 0.8, 0.1) == native
    with pytest.raises(ValueError, match="[Ss]election"):
        m["check_selection"](row, native, repaired, 0.8, 0.1)
    changed = copy.deepcopy(row)
    changed.update(
        selected_arm="constant",
        repair_executed=True,
        decision="repair",
        probability_correct=0.1,
        gate=0.5,
        selected_tokens_sha256=m["C"]["digest"]("[5, 9]"),
    )
    assert m["check_selection"](changed, native, repaired, 0.1, 0.8) == repaired
    with pytest.raises(ValueError, match="[Ss]election"):
        m["check_selection"](changed | {"gate": 0.9}, native, repaired, 0.1, 0.8)


def test_cost_profile_distinguishes_fixed_overhead_and_unmeasured_tasks():
    m = module()
    rows = [dict(task="mmlu_pro", seconds=2.0), dict(task="mmlu_pro", seconds=4.0)]
    result = m["project_cost"](rows, {"mmlu_pro": 12032, "swe_bench": 500}, 1.75)
    assert result["mmlu_pro"]["central_gpu_seconds"] == 36096
    assert result["mmlu_pro"]["upper_observed_gpu_seconds"] == 48128
    assert result["swe_bench"]["measured"] is False


def test_delivery_audit_binds_receipt_probability_usage_and_exact_input(tmp_path):
    import asyncio
    import json

    from jev_guided_decoding.experiment_budget import InputTokenBudget

    f = runpy.run_path(str(PATH.parents[2] / "tests/test_selective_benchmark_feedback.py"))
    c = f["case"]()

    async def sleep(_):
        pass

    with InputTokenBudget(tmp_path / "budget.jsonl", max_usd=0.15, usd_per_million=0.042) as b:
        worker = f["module"]()["Feedback"](f["Provider"]([0.2]), b, tmp_path, sleep=sleep)
        asyncio.run(worker.score(c, "#### 2"))
    m = dict(jev_cap=0.15, usd_per_million=0.042, jev="jev-1.13.0")
    audit = module()["check_delivery"]
    native = {c["id"]: dict(final="#### 2")}
    result = audit(tmp_path, {c["id"]: c}, native, m)
    assert result["known_input_tokens"] == 300 and result["physical_attempts"] == 1
    with pytest.raises(ValueError, match="binding"):
        audit(tmp_path, {c["id"]: c}, {c["id"]: dict(final="#### 3")}, m)
    p = tmp_path / "responses.jsonl"
    row = json.loads(p.read_text())
    row["probability_correct"] = 0.8
    p.write_text(json.dumps(row) + "\n")
    with pytest.raises(ValueError, match="[Rr]eceipt"):
        audit(tmp_path, {c["id"]: c}, native, m)


def test_selected_record_cannot_hide_a_different_executed_gate():
    m = module()
    native = dict(arm="native", generated_token_ids=[4, 9])
    repaired = dict(arm="constant", generated_token_ids=[5, 9], gate=0.9)
    d = dict(
        arm="constant",
        selected_arm="constant",
        repair_executed=True,
        decision="repair",
        probability_correct=0.1,
        gate=0.5,
        selected_tokens_sha256=m["C"]["digest"]("[5, 9]"),
    )
    with pytest.raises(ValueError, match="[Ss]election"):
        m["check_selection"](d, native, repaired, 0.1, 0.8)


def test_output_audit_reconstructs_exact_prefix_and_rejects_unregistered_arms():
    class Tokenizer:
        def apply_chat_template(self, *args, **kwargs):
            return [1, 2]

        def decode(self, tokens, **kwargs):
            return "Final: A" if tokens == [4] else "changed"

    m = module()
    c = dict(id="a", prompt="Q?")
    config = dict(thinking=False, max_new_tokens=4)
    row = dict(
        id="a",
        prompt_sha256=m["C"]["digest"]("Q?"),
        prompt_token_ids=[1, 2],
        generated_token_ids=[4, 9],
        arm="native",
        finish_reason="eos",
        text="Final: A",
        final="Final: A",
        status="complete",
        events=[],
        gate=None,
    )
    m["check_output"](c, row, Tokenizer(), config, [9])
    with pytest.raises(ValueError, match="prefix"):
        m["check_output"](c, row | {"prompt_token_ids": [1, 3]}, Tokenizer(), config, [9])
    with pytest.raises(ValueError, match="arm"):
        m["check_output"](c, row | {"arm": "best_of_hidden_retries"}, Tokenizer(), config, [9])


def test_numerical_admission_audit_rejects_failed_cache_or_gradient_checks():
    import copy

    m = module()
    comparison = dict(max_abs=3e-5, argmax_equal=True, allclose=True)
    value = dict(
        initial=dict(
            passed=True,
            zero_gate_exact=True,
            zero_initial_exact=True,
            base_gradients_absent=True,
            precision="float32",
            atol=1e-4,
            rtol=1e-4,
            comparison=comparison,
        ),
        selected=[comparison] * 3,
    )
    m["check_numerical"](value)
    changed = copy.deepcopy(value)
    changed["initial"]["base_gradients_absent"] = False
    with pytest.raises(ValueError, match="admission"):
        m["check_numerical"](changed)
    changed = copy.deepcopy(value)
    changed["selected"][0]["argmax_equal"] = False
    with pytest.raises(ValueError, match="admission"):
        m["check_numerical"](changed)


def test_full_cost_weights_actual_subject_counts_and_preserves_unknowns():
    m = module()
    rows = [
        dict(task="mmlu_pro", family="a", seconds=1),
        dict(task="mmlu_pro", family="b", seconds=10),
    ]
    out = m["project_stratified_cost"](
        rows, {"mmlu_pro": {"a": 10, "b": 100}, "unseen": {"x": 5}}, 1.8
    )
    assert out["mmlu_pro"]["gpu_seconds"] == 1010
    assert out["mmlu_pro"]["profile_cases"] == 2
    assert out["unseen"]["measured"] is False


def test_native_batch_order_and_warmup_are_bound_to_input_lengths():
    m = module()
    cases = {k: dict(id=k) for k in ["a", "b", "c", "d"]}
    ids = ["b", "a", "c", "d"]
    native = [
        dict(id=k, arm="native", prompt_token_ids=[1] * n, batch_id="batch")
        for n, k in enumerate(ids, 1)
    ]
    rows = [dict(id="b", arm="warmup"), *native, *[dict(id=k, arm="serial_probe") for k in cases]]
    m["check_profile_order"](cases, rows, 4)
    changed = copy.deepcopy(rows)
    changed[1], changed[2] = changed[2], changed[1]
    with pytest.raises(ValueError, match="order"):
        m["check_profile_order"](cases, changed, 4)
