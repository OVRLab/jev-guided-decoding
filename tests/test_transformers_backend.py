import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("transformers")

from tokenizers import Tokenizer  # noqa: E402
from tokenizers.models import WordLevel  # noqa: E402
from tokenizers.pre_tokenizers import Whitespace  # noqa: E402
from transformers import (  # noqa: E402
    GenerationConfig,
    LlamaConfig,
    LlamaForCausalLM,
    PreTrainedTokenizerFast,
)

from jev_guided_decoding.backends.transformers import (  # noqa: E402
    ChunkStop,
    TransformersBackend,
    sentence_boundary,
)


def test_per_candidate_stopping_and_decimal_handling():
    class TextTokenizer:
        def decode(self, ids, **kwargs):
            return {1: "Done.", 2: "Still writing", 3: "3.", 4: "Dr."}[ids[-1]]

    stop = ChunkStop(TextTokenizer(), 1, 2, float("inf"))
    assert stop(torch.tensor([[0, 1], [0, 2]]), None).tolist() == [True, False]
    assert stop.stopped_at == [1, None]
    assert not sentence_boundary("The number is 3.")
    assert not sentence_boundary("Dr.")
    assert sentence_boundary('The answer is ready."')


@pytest.mark.parametrize("framed", [False, True])
def test_real_tiny_causal_model_matches_native_greedy_and_keeps_weights_frozen(framed):
    vocab = {"[UNK]": 0, "[PAD]": 1, "[EOS]": 2, "alpha": 3, "beta": 4, "gamma": 5}
    raw = Tokenizer(WordLevel(vocab, unk_token="[UNK]"))
    raw.pre_tokenizer = Whitespace()
    tokenizer = PreTrainedTokenizerFast(
        tokenizer_object=raw,
        unk_token="[UNK]",
        pad_token="[PAD]",
        eos_token="[EOS]",
    )
    torch.manual_seed(11)
    model = LlamaForCausalLM(
        LlamaConfig(
            vocab_size=len(vocab),
            hidden_size=16,
            intermediate_size=32,
            num_hidden_layers=1,
            num_attention_heads=2,
            num_key_value_heads=1,
            max_position_embeddings=64,
            eos_token_id=2,
            pad_token_id=1,
        )
    )
    backend = TransformersBackend(model, tokenizer, model_id="tiny-test")
    before = {name: value.clone() for name, value in model.state_dict().items()}
    propose = backend.propose_frames if framed else backend.propose
    proposal = propose((3, 4), (), count=1, max_tokens=4, seed=7, greedy=True, max_seconds=20)
    with torch.inference_mode():
        expected = model.generate(
            torch.tensor([[3, 4]]),
            attention_mask=torch.ones((1, 2), dtype=torch.long),
            generation_config=GenerationConfig(
                max_new_tokens=4,
                do_sample=False,
                eos_token_id=[2],
                pad_token_id=1,
            ),
        )[0, 2:].tolist()
    assert list(proposal.candidates[0].token_ids) == expected
    assert proposal.decode_token_slots == len(expected)
    assert proposal.prefill_tokens == 2
    assert all(not p.requires_grad for p in model.parameters())
    assert all(torch.equal(value, before[name]) for name, value in model.state_dict().items())
    # Continuation must start with the exact accepted IDs, without decoding/re-tokenizing them.
    accepted = proposal.candidates[0].token_ids
    if proposal.candidates[0].finish_reason != "eos":
        continued = propose(
            (3, 4), accepted, count=2, max_tokens=3, seed=7, greedy=False, max_seconds=20
        )
        assert continued.prefill_tokens == (2 + len(accepted)) * 2
        assert len(continued.candidates) == 2
        for candidate in continued.candidates:
            assert candidate.full_text == backend.decode(accepted + candidate.token_ids)


def test_frame_stopping_ignores_sentence_punctuation_and_waits_for_complete_delimiter():
    from jev_guided_decoding.backends.transformers import FrameStop

    class Pieces:
        def decode(self, ids, **kwargs):
            pieces = {0: "", 1: "<step>Dr. Li: 3.14.\n", 2: "</st", 3: "ep>", 4: "More"}
            return "".join(pieces[i] for i in ids)

    stop = FrameStop(Pieces(), 1, 2, float("inf"))
    assert stop(torch.tensor([[0, 1, 2], [0, 1, 4]]), None).tolist() == [False, False]
    assert stop(torch.tensor([[0, 1, 2, 3], [0, 1, 4, 4]]), None).tolist() == [True, False]
    assert stop.stopped_at == [3, None]
    assert stop.reasons[0] == "frame"


def test_control_encoding_is_literal_delimiters_without_model_answers():
    class Tokenizer:
        def encode(self, text, *, add_special_tokens):
            assert not add_special_tokens
            return [ord(c) for c in text]

    backend = TransformersBackend.__new__(TransformersBackend)
    backend.tokenizer = Tokenizer()
    assert backend.encode_control("\n<final>") == tuple(map(ord, "\n<final>"))
    with pytest.raises(ValueError):
        backend.encode_control("<final>ENTAILED")
