"""Shared claim syntax, independent of evidence truth and external judgments."""

import re

from jev_guided_decoding.framing import parse_frame
from jev_guided_decoding.generated_answer import final_body


def claim_texts(entities, properties):
    if (
        not entities
        or not properties
        or len(set(entities)) != len(entities)
        or len(set(properties)) != len(properties)
    ):
        raise ValueError("Nonempty unique lexicons required")
    if any(not re.fullmatch("[A-Z][a-z]+", e) for e in entities):
        raise ValueError("Invalid entity")
    if any(not re.fullmatch("[a-z]+", p) for p in properties):
        raise ValueError("Invalid property")
    return tuple(
        text
        for e in entities
        for p in properties
        for text in (f"{e} is {p}.", f"{e} is not {p}.", f"It is not established that {e} is {p}.")
    )


class TokenTrie:
    def __init__(self, sequences):
        self.children, self.terminals = {}, set()
        for sequence in sequences:
            sequence = tuple(sequence)
            if not sequence or any(type(t) is not int or t < 0 for t in sequence):
                raise ValueError("Nonempty integer token sequence required")
            for position, token in enumerate(sequence):
                prefix = sequence[:position]
                if prefix in self.terminals:
                    raise ValueError("A complete sequence cannot prefix another")
                self.children.setdefault(prefix, set()).add(token)
            if sequence in self.children:
                raise ValueError("A complete sequence cannot prefix another")
            self.terminals.add(sequence)
        if not self.terminals:
            raise ValueError("Empty grammar")

    def allowed(self, prefix):
        prefix = tuple(prefix)
        if prefix in self.terminals:
            return ()
        if prefix not in self.children:
            raise ValueError("Token prefix is outside the grammar")
        return tuple(sorted(self.children[prefix]))

    def complete(self, prefix):
        return tuple(prefix) in self.terminals


def final_label(text, finish_reason):
    if finish_reason not in {"eos", "frame"}:
        return None
    frame = parse_frame(text)
    body = frame.body if frame and frame.kind == "final" else final_body(text, finish_reason)
    if body is None:
        return None
    label = body.strip()
    return label if label in {"TRUE", "FALSE", "UNKNOWN"} else None
