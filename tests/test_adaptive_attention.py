import asyncio
import copy
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "research/iterations/adaptive_attention"


def module(name):
    return runpy.run_path(str(HERE / f"{name}.py"))


def test_fresh_worlds_and_transfer_preserve_independent_visible_truth():
    d = module("data")
    dev, test = d["synthetic"]("development", 12), d["synthetic"]("test", 12)
    assert not {c["world_id"] for c in dev} & {c["world_id"] for c in test}
    assert len(dev) == 12 and len(test) == 24
    for case in test:
        for variant in ("original", "paraphrase", "dependency"):
            changed = d["variant"](case, variant)
            assert d["visible_reference"](changed) == case["reference"]
            assert set(d["public_view"](changed)) == {"id", "question", "sources", "family"}


@pytest.mark.parametrize(
    "text,expected",
    [
        ("The parcel is in the blue room.", "blue"),
        ("There is not enough information to determine its room.", "UNKNOWN"),
        ("It is red or blue.", None),
        ("It is not red.", None),
        ("I cannot determine the room, but perhaps blue.", None),
        ("", None),
    ],
)
def test_natural_answers_do_not_need_unknown_token_and_ambiguity_is_not_a_success(text, expected):
    assert module("data")["parse_synthetic"](text) == expected


def test_head_policies_and_selection_are_bounded_and_deterministic():
    p = module("policies")
    original = p["r15"]()
    candidates = p["diagnostic_policies"]()
    assert len({c["id"] for c in candidates}) == len(candidates)
    assert any(len([w for w in c["weights"] if w > 0]) == 11 for c in candidates)
    row = {"policy": original, "accuracy": 0.5, "mean_logprob": -1}
    worse = {**row, "accuracy": 0.49}
    assert p["choose"]([worse, row]) == row
    invalid = copy.deepcopy(original)
    invalid["weights"][0] = float("nan")
    with pytest.raises(ValueError):
        p["token_maps"](invalid, [[1], [2]], [0.9, 0.1])


def test_cached_head_mask_preserves_causality_and_different_strengths():
    torch = pytest.importorskip("torch")
    a = module("attention")
    mask = a["make_mask"](
        None,
        num_heads=4,
        query_positions=[3, 4],
        key_length=5,
        query_start=3,
        head_bias={1: {0: 1.0}, 2: {1: 4.0}},
        device="cpu",
        dtype=torch.float32,
    )
    assert mask.shape == (1, 4, 2, 5)
    assert mask[0, 1, 0, 0] == 1
    assert mask[0, 2, 1, 1] == 4
    assert mask[0, 0, 0, 0] == 0
    assert mask[0, 1, 0, 4] < -1e20


def test_cache_matches_full_prefix_zero_identity_binding_and_cleanup():
    torch = pytest.importorskip("torch")
    tiny = runpy.run_path(str(ROOT / "tests/test_evidence_attention.py"))["tiny"]
    model = tiny()
    a = module("attention")["AdaptiveAttention"](model)
    ids = [1, 2, 3, 4, 5]
    weights = {k: v.clone() for k, v in model.state_dict().items()}
    with torch.inference_mode():
        raw = model(torch.tensor([ids]), use_cache=False).logits
        with a.apply(ids, query_start=3, maps={}):
            zero = model(torch.tensor([ids]), use_cache=False).logits
        assert torch.equal(raw, zero)
        maps = {(0, 1): {0: 2.0}, (1, 2): {1: 4.0}}
        with a.apply(ids, query_start=3, maps=maps):
            full = model(torch.tensor([ids]), use_cache=False).logits
        with a.apply(ids[:4], query_start=3, maps=maps):
            first = model(
                torch.tensor([ids[:4]]),
                use_cache=True,
                past_key_values=module("attention")["new_cache"](model),
            )
        with a.apply([ids[4]], query_start=3, maps=maps, past_length=4):
            cached = model(
                torch.tensor([[ids[4]]]), past_key_values=first.past_key_values, use_cache=True
            ).logits
        torch.testing.assert_close(full[:, -1], cached[:, -1], atol=1e-6, rtol=1e-5)
        assert not torch.equal(raw[:, -1], full[:, -1])
        with pytest.raises(ValueError, match="binding"):
            with a.apply(ids, query_start=3, maps=maps):
                model(torch.tensor([[1, 2, 3, 4, 9]]), use_cache=False)
        assert not a.active
    assert all(torch.equal(weights[k], v) for k, v in model.state_dict().items())


def test_scorer_payload_excludes_truth_and_marks_generated_text_as_fallible():
    s = module("scorer")
    view = {
        "id": "x",
        "question": "Where is A?",
        "family": "hotpot",
        "sources": [{"id": "E1", "text": "A is in B."}],
    }
    payload = s["payload_for"](view, "jev-1.13.0", "A might be in C.")
    assert payload["state"]["generated_reasoning"] == "A might be in C."
    assert "fallible" in str(payload["questions"])
    assert "reference" not in str(payload) and "labels" not in str(payload)
    with pytest.raises(ValueError):
        s["payload_for"]({**view, "reference": "B"}, "jev-1.13.0")


def test_failed_receipt_is_charged_and_never_dispatched_again(tmp_path):
    from jev_guided_decoding.experiment_budget import InputTokenBudget
    from jev_guided_decoding.types import ScorerError

    s = module("scorer")
    calls = []

    class Fake:
        model = "jev-1.13.0"

        async def _evaluate(self, *args, **kwargs):
            calls.append(1)
            raise ScorerError("timeout", attempts=1, usage_unknown=True)

    view = {
        "id": "x",
        "question": "Where is A?",
        "family": "hotpot",
        "sources": [{"id": "E1", "text": "A is in B."}],
    }
    with InputTokenBudget(tmp_path / "ledger.jsonl", max_usd=1) as budget:
        store = s["ReceiptStore"](tmp_path / "receipts.jsonl", Fake(), budget)
        first = asyncio.run(store.get(view))
        second = asyncio.run(store.get(view))
        assert first == second and first["status"] == "failed"
        assert len(calls) == 1 and budget.charged_tokens == 65536
        assert not budget.unresolved


def test_resume_never_reexecutes_started_job_and_rejects_changed_config(tmp_path):
    j = module("journal")
    with j["Journal"](tmp_path, {"protocol": "a"}) as log:
        assert log.start("one", {"case": "c"})
    with j["Journal"](tmp_path, {"protocol": "a"}) as log:
        assert not log.start("one", {"case": "c"})
        assert log.outputs["one"]["status"] == "interrupted"
    with pytest.raises(ValueError, match="freeze"):
        with j["Journal"](tmp_path, {"protocol": "b"}):
            pass


def test_generation_keeps_semantic_tokens_and_framing_separate_with_no_forced_unknown():
    torch = pytest.importorskip("torch")
    from types import SimpleNamespace

    tiny = runpy.run_path(str(ROOT / "tests/test_evidence_attention.py"))["tiny"]
    model = tiny()

    class Tokenizer:
        def decode(self, ids, **kwargs):
            return " ".join(str(i) for i in ids)

    base = SimpleNamespace(
        model=model,
        tokenizer=Tokenizer(),
        device=torch.device("cpu"),
        eos_ids=set(),
        _sync=lambda: None,
    )
    runtime = module("runtime")["Runtime"](base)
    encoded = {
        "input_ids": [1, 2, 3, 4],
        "query_start": 3,
        "span_token_indices": [[0], [1]],
        "prompt_digest": "test",
    }
    session = runtime.session(encoded)
    one = session.generate(3, "reasoning", maps={})
    session.frame([7, 8], "final cue")
    two = session.generate(2, "final", maps={})
    assert len(one["token_ids"]) == 3 and len(two["token_ids"]) == 2
    assert session.ids == [1, 2, 3, 4] + one["token_ids"] + [7, 8] + two["token_ids"]
    assert all(t["token_id"] == t["argmax_id"] for phase in (one, two) for t in phase["tokens"])
    assert session.forwards == 5 and session.processed == len(session.ids) - 1
    assert session.frames[0]["token_ids"] == [7, 8]


def test_study_schedule_has_free_text_transfer_and_matched_staged_controls():
    s, d = module("study"), module("data")
    cases = d["synthetic"]("test", 12)
    schedule = s["schedule"](cases, [])
    keys = [(j["case_id"], j["contract"], j["arm"]) for j in schedule]
    assert len(keys) == len(set(keys))
    assert {j["contract"] for j in schedule} == {
        "constrained",
        "open_explicit",
        "open_neutral",
        "staged",
    }
    groups = {}
    for j in schedule:
        if j["contract"] == "staged":
            groups.setdefault(j["case_id"], set()).add(j["arm"])
    assert all(arms == set(s["STAGED_ARMS"]) for arms in groups.values())
    assert any("/dependency" in j["case_id"] for j in schedule)


def test_official_hotpot_normalization_does_not_extract_answer_from_verbose_text():
    d = module("data")
    assert d["hotpot_metrics"]("The Eiffel Tower", "Eiffel Tower") == {"em": 1, "f1": 1.0}
    assert d["hotpot_metrics"]("The answer is Eiffel Tower", "Eiffel Tower")["em"] == 0
    assert d["hotpot_metrics"]("Yes, probably", "yes")["f1"] == 0


def test_all_http_failures_preserve_retry_after_and_auth_failure_stays_fatal():
    import httpx

    s = module("scorer")
    client = s["StudyClient"]("synthetic-unit-key", max_retries=0)
    response = httpx.Response(503, headers={"Retry-After": "120"}, text="overloaded")
    assert client._error_diagnostics(response)["retry_after_seconds"] == 120
    asyncio.run(client._client.aclose())


def test_independent_provenance_audit_rejects_changed_tokens_and_framing():
    a = module("analyze")
    row = {
        "status": "complete",
        "contract": "open_explicit",
        "model_forwards": 1,
        "processed_tokens": 3,
        "generated_tokens": 1,
        "framing": [],
        "final_input_and_output_ids": [1, 2, 3, 7],
        "text": "7",
        "phases": [
            {
                "phase": "final",
                "start": 3,
                "token_ids": [7],
                "text": "7",
                "tokens": [
                    {
                        "token_id": 7,
                        "argmax_id": 7,
                        "selected_logit": 1,
                        "top_ids": [7, 8],
                        "top_logits": [1, 0],
                    }
                ],
            }
        ],
    }
    a["check_tokens"](row, {"input_ids": [1, 2, 3]})
    changed = copy.deepcopy(row)
    changed["final_input_and_output_ids"][-1] = 9
    with pytest.raises(ValueError):
        a["check_tokens"](changed, {"input_ids": [1, 2, 3]})


def test_complete_dynamic_flow_refreshes_after_generated_steps_and_keeps_final_granite_owned(
    tmp_path,
):
    torch = pytest.importorskip("torch")
    from types import SimpleNamespace

    model = runpy.run_path(str(ROOT / "tests/test_evidence_attention.py"))["tiny"]()

    class Tokenizer:
        def decode(self, ids, **kwargs):
            return " ".join(str(i) for i in ids)

        def encode(self, text, **kwargs):
            return [9]

    class Receipts:
        receipts = {}
        new_failure = None

        async def get(self, view, reasoning=""):
            return {
                "status": "complete",
                "key": "prefix:" + reasoning,
                "scores": [0.1, 0.9] if reasoning else [0.9, 0.1],
            }

    base = SimpleNamespace(
        model=model,
        tokenizer=Tokenizer(),
        device=torch.device("cpu"),
        eos_ids=set(),
        _sync=lambda: None,
    )
    runtime = module("runtime")["Runtime"](base)
    journal = module("journal")["Journal"]
    study = module("study")
    case = {
        "id": "test",
        "world_id": "world",
        "family": "original",
        "question": "Where?",
        "sources": [{"id": "A", "text": "First fact"}, {"id": "B", "text": "Second fact"}],
        "reference": "blue",
    }
    policy = module("policies")["identified"](
        {"heads": [[0, 1], [1, 2]], "weights": [2, 4], "mapping": "threshold", "threshold": 0.5}
    )
    encoded = {
        "input_ids": [1, 2, 3, 4],
        "query_start": 3,
        "span_token_indices": [[0], [1]],
        "prompt_digest": "test",
    }
    with journal(tmp_path, {}) as log:
        runner = study["Runner"](runtime, log, Receipts(), {"max_seconds": 60})
        runner.input_cache["test", "staged"] = encoded
        row = asyncio.run(runner.job(case, "staged", "dynamic", policy))
    assert row["status"] == "complete"
    assert [u["after_generated_tokens"] for u in row["updates"]] == [0, 24, 48]
    assert row["phases"][-1]["phase"] == "final"
    module("analyze")["check_tokens"](row, encoded, base.tokenizer)
    changed = copy.deepcopy(row)
    changed["phases"][0]["tokens"][0]["argmax_id"] = 9
    with pytest.raises(ValueError):
        module("analyze")["check_tokens"](changed, encoded)
