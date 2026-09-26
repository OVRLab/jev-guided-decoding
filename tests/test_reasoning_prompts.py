import pytest

from jev_guided_decoding.framing import REASONING_PROMPT
from jev_guided_decoding.reasoning import ReasoningConfig, prepare_reasoning_request
from jev_guided_decoding.types import Request


def test_instruction_prompt_remains_the_default():
    config = ReasoningConfig()
    request = prepare_reasoning_request(Request("Q", "E"), config.prompt_style)
    assert request.system == REASONING_PROMPT


def test_existing_positional_candidate_configuration_remains_compatible():
    assert ReasoningConfig(2).candidates == 2


def test_example_preparation_is_idempotent_and_preserves_custom_system_and_problem():
    request = Request("CURRENT_QUESTION", "CURRENT_EVIDENCE", "CUSTOM_INSTRUCTION")
    prepared = prepare_reasoning_request(request, "examples")
    repeated = prepare_reasoning_request(prepared, "examples")
    assert prepared == repeated
    assert prepared.system.count("CUSTOM_INSTRUCTION") == 1
    assert prepared.system.count(REASONING_PROMPT) == 1
    assert prepared.question == request.question and prepared.evidence == request.evidence
    assert "CURRENT_EVIDENCE" not in prepared.system
    assert "CURRENT_QUESTION" not in prepared.system
    assert len(prepared.system) > len(REASONING_PROMPT)


def test_switching_styles_does_not_accumulate_demonstrations():
    request = Request("Q", "E", "CUSTOM_INSTRUCTION")
    examples = prepare_reasoning_request(request, "examples")
    instructions = prepare_reasoning_request(examples, "instructions")
    assert instructions == prepare_reasoning_request(request, "instructions")


@pytest.mark.parametrize("style", ["unknown", "", None, [], {}])
def test_unknown_prompt_style_is_rejected_before_inference(style):
    with pytest.raises(ValueError, match="prompt_style"):
        ReasoningConfig(prompt_style=style)
