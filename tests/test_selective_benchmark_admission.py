import hashlib
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
PATH = ROOT / "research/iterations/selective_benchmarks/admission.py"


def module():
    return runpy.run_path(str(PATH))


def test_conversion_preserves_problem_and_binds_reference_before_changing_format():
    prompt = (
        "Which color?\n\nA. red\nB. blue\n\nReason through the problem "
        "and finish with a separate line: Final: <letter>."
    )
    case = dict(
        id="fixture/1", task="arc", prompt=prompt, split="development", origin="validation/1"
    )
    ref = dict(
        id="fixture/1",
        prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
        kind="choice",
        answer="B",
        choices=2,
    )
    c, r = module()["convert"](case, ref)
    assert c["prompt"].startswith("Which color?\n\nA. red\nB. blue")
    assert "<letter>" not in c["prompt"] and "answer" not in c
    assert r["answer"] == "B" and r["options"] == ["red", "blue"]
    with pytest.raises(ValueError, match="binding"):
        module()["convert"](case | {"prompt": prompt + " altered"}, ref)


def test_source_verification_rejects_checkpoint_and_case_tampering(tmp_path):
    m = module()
    (tmp_path / "cases.json").write_text("[]")
    (tmp_path / "branch.safetensors").write_bytes(b"fixture-checkpoint")
    manifest = {
        "sources": {},
        "datasets": {"cases.json": m["C"]["sha"](tmp_path / "cases.json")},
        "checkpoints": {
            "live": {
                "file": "branch.safetensors",
                "sha256": m["C"]["sha"](tmp_path / "branch.safetensors"),
            }
        },
    }
    m["verify_bindings"](tmp_path, manifest)
    (tmp_path / "branch.safetensors").write_bytes(b"changed")
    with pytest.raises(ValueError, match="binding"):
        m["verify_bindings"](tmp_path, manifest)


def test_feedback_strength_controls_do_not_change_routing():
    m = module()
    assert m["strength"]("live", 0.1, 0.8) == 0.9
    assert m["strength"]("inverted", 0.1, 0.8) == 0.1
    assert m["strength"]("shuffled", 0.1, 0.8) == pytest.approx(0.2)
    assert m["strength"]("live_constant", 0.1, 0.8) == 0.5
    with pytest.raises(ValueError):
        m["strength"]("unknown", 0.1, 0.8)


def test_all_selective_arms_skip_or_repair_using_same_native_binding():
    m = module()
    native = {"generated_token_ids": [3, 9], "text": "Final: A"}
    calls = []

    def generate(arm, gate):
        calls.append((arm, gate))
        return {"generated_token_ids": [4, 9], "text": "Final: B"}

    retained = m["repair_case"](native, 0.9, 0.1, generate)
    assert len(retained) == 6 and not calls
    assert all(row["output"] is native and not row["repair_executed"] for _, row in retained)
    repaired = m["repair_case"](native, 0.1, 0.8, generate)
    assert len(calls) == 6 and all(row["repair_executed"] for _, row in repaired)
    assert dict(calls)["live"] == 0.9 and dict(calls)["constant"] == 0.5


def test_recorded_gate_is_actual_control_strength_not_routing_score():
    m = module()
    out = dict(m["repair_case"]({}, 0.1, 0.8, lambda arm, gate: {"text": arm}))
    assert out["constant"]["gate"] == 0.5
    assert out["blind"]["gate"] is None
    assert out["inverted"]["gate"] == 0.1
    assert out["shuffled"]["gate"] == pytest.approx(0.2)
