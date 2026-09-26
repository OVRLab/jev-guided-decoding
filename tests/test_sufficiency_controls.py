import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load():
    return runpy.run_path(str(ROOT / "research/iterations/sufficiency_controls.py"))


def test_sufficiency_permutation_is_bijective_label_free_and_within_domain():
    s = load()
    cases = [
        dict(id=f"{domain}/{i}", family=domain, reference="secret")
        for domain in ("hotpot", "squad2")
        for i in range(5)
    ]
    mapping = s["donors"](cases)
    assert set(mapping) == set(mapping.values()) == {c["id"] for c in cases}
    assert all(k != v and k.split("/")[0] == v.split("/")[0] for k, v in mapping.items())
    assert mapping == s["donors"]([{**c, "reference": "changed"} for c in reversed(cases)])


def test_control_receipts_distinguish_fixed_instruction_from_semantic_judgment():
    s = load()
    own = dict(key="own", status="complete", scores=[0.9, 0.1], sufficient=0.9)
    donor = dict(key="donor", status="complete", scores=[0.1], sufficient=0.1)
    fixed = s["control_receipt"]("instruction_always", 2, None, None)
    assert fixed["sufficient"] == 0 and fixed["scores"] == [0.5, 0.5]
    shuffled = s["control_receipt"]("shuffled_sufficiency", 2, own, donor)
    assert shuffled["scores"] == own["scores"] and shuffled["sufficient"] == donor["sufficient"]
    failed = s["control_receipt"](
        "shuffled_sufficiency", 2, own, dict(status="failed", key="failed")
    )
    assert failed["status"] == "failed" and "sufficient" not in failed
    assert own["sufficient"] == 0.9


def test_supplement_canned_and_permuted_inputs_use_the_same_free_token_runtime():
    import asyncio

    import pytest

    pytest.importorskip("torch")
    s = load()
    fixture = runpy.run_path(str(ROOT / "tests/test_benefit_sufficiency.py"))
    _, old, encoded, view, policy = fixture["tiny"]()
    runtime = runpy.run_path(str(ROOT / "research/iterations/benefit_sufficiency/runtime.py"))
    active = runtime["Runtime"](old.base, boundary=1)
    own = dict(key="own", status="complete", scores=[0.9, 0.1], sufficient=0.9)
    donor = dict(key="donor", status="complete", scores=[0.2], sufficient=0.1)
    for arm in s["ARMS"]:
        response = s["control_receipt"](arm, 2, own, donor)

        async def callback(v, response=response):
            return response

        result = asyncio.run(
            runtime["generate"](
                active,
                encoded,
                view,
                policy,
                callback,
                gate={"kind": "always"},
                mode="sufficiency" if arm == "instruction_always" else "dual",
                instruction_strength=2,
                limit=2,
                capture=True,
            )
        )
        assert result["intervention_action"] == "abstention"
        assert result["prefills"] == 1
        assert result["final"]["token_ids"] == [int(x.argmax()) for x in result["_debug"]["logits"]]
