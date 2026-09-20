import asyncio

import pytest
from test_fixed_verdict import REQUEST, Decider
from test_reasoning import Backend, candidate

from jev_guided_decoding.reasoning import ReasoningConfig
from jev_guided_decoding.verdict import FixedVerdictController, VerdictConfig


def test_unguided_selects_likelihood_without_step_scores_and_shares_final_choice():
    low = candidate("<step>A</step>", -2)
    high = candidate("<step>B</step>", -0.1)
    final = candidate("<final>CONTRADICTED</final>")
    backend = Backend([[low, high], [final]])
    scorer = Decider()
    controller = FixedVerdictController(backend, ReasoningConfig(), scorer, VerdictConfig())
    result = asyncio.run(controller.run(REQUEST, "unguided_fixed_jev"))
    assert scorer.calls == []
    assert scorer.decisions[0][1] == ["B"]
    assert result.reasoning_outcome["mode"] == "likelihood"
    assert result.reasoning_outcome["text"] == "CONTRADICTED"
    assert result.text == "UNKNOWN" and result.api_calls == 1
    assert result.token_ids == high.token_ids + final.token_ids
    assert backend.prefixes == [(), high.token_ids]


def test_unguided_requires_backend_and_validates_reservation_before_dispatch():
    controller = FixedVerdictController(None, ReasoningConfig(), Decider(), VerdictConfig())
    with pytest.raises(ValueError, match="backend"):
        asyncio.run(controller.run(REQUEST, "unguided_fixed_jev"))
    controller.backend = Backend([])
    controller.config = ReasoningConfig(max_seconds=5)
    with pytest.raises(ValueError, match="reserve"):
        asyncio.run(controller.run(REQUEST, "unguided_fixed_jev"))


def test_unguided_cli_mode_is_accepted():
    from jev_guided_decoding.cli import parser

    args = parser().parse_args(
        [
            "reason",
            "--config",
            "config.toml",
            "--output",
            "out.json",
            "--question",
            "Q",
            "--evidence-file",
            "e.txt",
            "--mode",
            "unguided_fixed_jev",
        ]
    )
    assert args.mode == "unguided_fixed_jev"
