import runpy
from pathlib import Path

import pytest

PATH = Path(__file__).parents[1] / "research/diagnostics/benchmark_execution_v2_audit.py"


def test_terminal_audit_rejects_early_stops_and_changed_tokens():
    m = runpy.run_path(str(PATH))

    class Tok:
        def apply_chat_template(self, *args, **kwargs):
            return [1, 2]

        def decode(self, tokens, **kwargs):
            return "Final: A\n" if tokens == [4, 5] else "Final:"

    case = dict(id="example", prompt="Q?", format="choice")
    row = dict(
        id="example",
        prompt_sha256=m["C"]["digest"]("Q?"),
        prompt_token_ids=[1, 2],
        generated_token_ids=[4, 5],
        arm="native",
        finish_reason="terminal_line",
        text="Final: A\n",
        final="Final: A",
        status="complete",
        events=[],
        gate=None,
    )
    config = dict(thinking=False, max_new_tokens=8)
    m["check_output"](case, row, Tok(), config, [9])
    with pytest.raises(ValueError, match="stop"):
        m["check_output"](case, row | {"generated_token_ids": [4]}, Tok(), config, [9])
    with pytest.raises(ValueError, match="prefix"):
        m["check_output"](case, row | {"prompt_token_ids": [1, 3]}, Tok(), config, [9])


def test_independent_grades_use_selected_outputs_and_preserve_missing_denominators():
    m = runpy.run_path(str(PATH))
    cases = {
        "a": dict(id="a", task="synthetic", cluster="a"),
        "b": dict(id="b", task="synthetic", cluster="b"),
    }
    refs = {k: dict(kind="choice", options=["red", "blue"], answer="B") for k in cases}
    selected = {
        "original": {"a": dict(final="Final: A"), "b": dict(final="Final: B")},
        "guided": {"a": dict(final="B. blue\nFinal:"), "b": dict(final="ambiguous")},
    }
    result = m["score_selected"](cases, refs, selected)
    assert result["summaries"]["guided"]["synthetic"]["correct"] == 1
    assert result["summaries"]["guided"]["synthetic"]["total"] == 2
    assert result["paired_differences"]["guided-original"]["synthetic"]["wins"] == 1
    assert result["paired_differences"]["guided-original"]["synthetic"]["losses"] == 1
    with pytest.raises(ValueError, match="coverage"):
        m["score_selected"](cases, refs, selected | {"guided": {"a": selected["guided"]["a"]}})


def test_ifbench_language_judgment_has_a_fixed_reproducible_seed(monkeypatch):
    import sys
    from types import SimpleNamespace

    factory = SimpleNamespace(seed=None)
    monkeypatch.setitem(sys.modules, "langdetect", SimpleNamespace(DetectorFactory=factory))
    observed = []

    def score(*args):
        observed.append(factory.seed)
        return SimpleNamespace(follow_all_instructions=False)

    evaluator = SimpleNamespace(
        InputExample=lambda **kwargs: SimpleNamespace(**kwargs),
        test_instruction_following_strict=score,
        test_instruction_following_loose=score,
    )
    m = runpy.run_path(str(PATH))
    cases = {"a": dict(id="a", task="ifbench", cluster="a", prompt="Only say red.")}
    refs = {"a": dict(kind="ifbench", key=1, instruction_id_list=["synthetic"], kwargs=[{}])}
    m["score_selected"](cases, refs, {"original": {"a": dict(final="blue")}}, ifbench=evaluator)
    assert observed == [2701, 2701]
