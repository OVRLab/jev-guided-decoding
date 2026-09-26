import runpy
from pathlib import Path

import pytest

G = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "research/experiments/claim_grammar.py")
)


def test_grammar_contains_supported_and_unsupported_claims_without_receiving_truth():
    claims = G["claim_texts"](["Mira"], ["blue", "calm"])
    assert "Mira is blue." in claims and "Mira is calm." in claims
    assert "Mira is not calm." in claims
    assert "It is not established that Mira is calm." in claims
    assert len(claims) == 6


def test_token_trie_preserves_full_sequences_and_excludes_partial_or_appended_claims():
    trie = G["TokenTrie"]([(1, 2, 3), (1, 2, 4, 3)])
    assert trie.allowed(()) == (1,)
    assert trie.allowed((1, 2)) == (3, 4)
    assert trie.complete((1, 2, 3))
    assert not trie.complete((1, 2))
    assert trie.allowed((1, 2, 3)) == ()
    with pytest.raises(ValueError):
        trie.allowed((1, 9))
    with pytest.raises(ValueError):
        G["TokenTrie"]([(1, 2), (1, 2, 3)])


@pytest.mark.parametrize(
    "text,reason,expected",
    [
        ("TRUE", "eos", "TRUE"),
        ("UNKNOWN</final>", "frame", "UNKNOWN"),
        ("<final>FALSE</final>", "frame", "FALSE"),
        ("TRUE", "length", None),
        ("TRUE", "time", None),
        ("TRUE because I think so", "eos", None),
        ("", "eos", None),
        ("<step>TRUE</step>", "frame", None),
    ],
)
def test_final_contract_accepts_explicit_eos_without_inventing_text(text, reason, expected):
    assert G["final_label"](text, reason) == expected
