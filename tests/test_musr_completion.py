import copy
import runpy
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1] / "research/iterations/musr_transfer"


def test_completion_rejects_wrong_device_dtype_changed_weights_and_incomplete_work():
    module = runpy.run_path(str(HERE / "completion.py"))
    m = runpy.run_path(str(HERE / "contract.py"))["fixed"]()
    digest = m["backbone_digest"]
    adapters = {f"{n}/{s}": "a" * 64 for n, s in m["specs"]}
    hardware = dict(device="cuda:0", dtype="torch.float32", eos=[100257], parameters=1631750144)
    admission = dict(
        passed=True,
        device="cuda:0",
        api_calls=0,
        initial_identity=True,
        off_identity=True,
        cache_max_logit_error=0.00004,
        cache_argmax_equal=True,
        backbone_gradients_absent=True,
        backbone_before=digest,
        backbone_after=digest,
        memory_shape=[2048],
        dummy_adapter_parameters=262144,
    )
    complete = dict(
        outputs=204,
        requests=12,
        charged_input_tokens=1000,
        seconds=300,
        post_original_load_seconds=250,
    )
    original = dict(
        outputs=180,
        backbone_before=digest,
        backbone_after=digest,
        adapters_before=adapters,
        adapters_after=adapters,
        charged_input_tokens=1000,
    )
    evidence = dict(
        hardware=hardware,
        larger_hardware=hardware | dict(dtype="torch.bfloat16", parameters=3300000000),
        admission=admission,
        complete=complete,
        original=original,
    )
    module["metadata"](m, evidence, adapters)
    for section, key, value in (
        ("hardware", "device", "cpu"),
        ("hardware", "dtype", "torch.bfloat16"),
        ("admission", "cache_argmax_equal", False),
        ("original", "backbone_after", "b" * 64),
        ("complete", "outputs", 203),
        ("complete", "post_original_load_seconds", 5500),
    ):
        changed = copy.deepcopy(evidence)
        changed[section][key] = value
        with pytest.raises(ValueError):
            module["metadata"](m, changed, adapters)


def test_development_summary_keeps_unfinished_thinking_and_fix_damage_denominators():
    module = runpy.run_path(str(HERE / "completion.py"))
    cases = [
        dict(
            id=f"case/{i}",
            task="murder_mystery",
            split="development",
            context="Story",
            question="Who?",
            choices=["Alice", "Bob"],
        )
        for i in range(2)
    ]
    refs = {"case/0": 0, "case/1": 1}
    rows = []
    for case in cases:
        for arm, text in (
            ("native", "ANSWER: 1"),
            ("live/contextual-scalar/3101", "ANSWER: 2"),
            ("live/contextual-scalar/3102", "ANSWER: 1"),
            ("larger/thinking", "ANSWER: 2"),
        ):
            rows.append(dict(id=case["id"], arm=arm, text=text, finish_reason="eos"))
    responses = [dict(id=c["id"], probability=0.8) for c in cases]
    summary = module["summarize"](cases, refs, rows, responses)
    assert summary["scores"]["native"]["accuracy"] == 0.5
    assert summary["scores"]["live/contextual-scalar"]["accuracy"] == 0.5
    assert summary["preservation"]["live/contextual-scalar/3101"] == dict(fixed=1, damaged=1)
    assert summary["scores"]["larger/thinking"]["unreadable"] == 1.0
    assert summary["scores"]["larger/thinking"]["accuracy"] == 0.0
    assert summary["feedback_diagnostic"]["native_correct"] == 1
    assert summary["feedback_diagnostic"]["brier"] == pytest.approx(0.34)
