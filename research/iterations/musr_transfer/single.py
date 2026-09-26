"""Unpaid single-question interface prototype; no public study is admitted here."""

import json
import math
import re
import runpy
from pathlib import Path

M = runpy.run_path(str(Path(__file__).resolve().parents[1] / "contextual_memory/memory.py"))
READOUT_VERSION = "musr-exact-selection-v2"


def normalized(text):
    return " ".join(text.strip().strip("\"'().[] ").casefold().split())


def valid_choices(choices):
    if (
        not isinstance(choices, list)
        or not 2 <= len(choices) <= 5
        or any(not isinstance(c, str) or not normalized(c) for c in choices)
    ):
        raise ValueError("Invalid choices")


def validate_case(case):
    if (
        set(case) != {"id", "task", "split", "context", "question", "choices"}
        or case["task"] not in ("murder_mystery", "object_placements", "team_allocation")
        or case["split"] not in ("development", "test")
        or any(
            not isinstance(case[k], str) or not case[k].strip()
            for k in ("id", "context", "question")
        )
    ):
        raise ValueError("Invalid case or reference-bearing input")
    valid_choices(case["choices"])


def decision_text(case):
    validate_case(case)
    return (
        case["question"]
        + "\n\nChoices:\n"
        + "\n".join(f"{i + 1}. {choice}" for i, choice in enumerate(case["choices"]))
    )


def prompt_for(case):
    decision = decision_text(case)
    return (
        "Read the story and choose the best answer.\n\n"
        + case["context"]
        + "\n\n"
        + decision
        + "\n\nEnd with exactly one final line in the form ANSWER: <choice number>."
    )


def parse_choice(text, choices, *, thinking=False):
    """Reference-free exact selection; never randomly fill an unreadable answer."""
    valid_choices(choices)
    if not isinstance(text, str):
        raise ValueError("Answer text must be a string")
    invalid = dict(index=None, span=None, explicit_marker=False, format=False)
    offset = 0
    close = text.rfind("</think>")
    if close >= 0:
        offset = close + len("</think>")
    elif thinking:
        return invalid
    if "<think>" in text[offset:]:
        return invalid
    visible = text[offset:]
    fields = list(re.finditer(r"(?im)^[ \t]*ANSWER:[ \t]*([^\n]*)$", visible))
    raw = fields[-1][1] if fields else visible
    field_offset = fields[-1].start(1) if fields else 0
    lines = list(re.finditer(r"(?m)^[^\n]*\S[^\n]*$", visible))
    final_line_fallback = not fields and len(lines) > 1
    if final_line_fallback:
        raw = lines[-1][0]
        field_offset = lines[-1].start()
    start = offset + field_offset + len(raw) - len(raw.lstrip())
    field = raw.strip()
    if not field:
        return invalid
    index = None
    numeric = re.fullmatch(r"(?:\((\d+)\)|(\d+))(?:[.)])?(?:[ \t]+(?:[-–:][ \t]+)?(.+))?", field)
    if final_line_fallback and (numeric is None or numeric[3] is None):
        return invalid
    if numeric:
        index = int(numeric[1] or numeric[2]) - 1
        if not 0 <= index < len(choices) or (
            numeric[3] is not None and normalized(numeric[3]) != normalized(choices[index])
        ):
            return invalid
    else:
        hits = [i for i, choice in enumerate(choices) if normalized(field) == normalized(choice)]
        if len(hits) != 1:
            return invalid
        index = hits[0]
    end = start + len(field)
    return dict(
        index=index,
        span=[start, end],
        explicit_marker=bool(fields),
        format=bool(fields) and numeric is not None and not text[end:].strip(),
    )


def positions_for(tok, case, native, *, eos, limit=2048):
    validate_case(case)
    if type(limit) is not int or not 1 <= limit <= 4096:
        raise ValueError("Invalid memory token limit")
    prompt = tok.apply_chat_template(
        [dict(role="user", content=prompt_for(case))], tokenize=True, add_generation_prompt=True
    )
    if native["prompt_token_ids"] != prompt:
        raise ValueError("Original prompt token mismatch")
    generated = native["generated_token_ids"]
    if not generated or eos in generated[:-1]:
        raise ValueError("Invalid native token completion")
    body = generated[:-1] if generated[-1] == eos else generated
    ids = prompt + body
    if len(ids) > limit or any(type(i) is not int or i < 0 for i in ids):
        raise ValueError("Oversized or invalid memory tokens")
    kwargs = dict(skip_special_tokens=False, clean_up_tokenization_spaces=False)
    prefix = tok.decode(prompt, **kwargs)
    if tok.decode(body, **kwargs) != native["text"]:
        raise ValueError("Native token/text mismatch")
    text, spans = M["decoded_spans"](tok, ids)
    decision = decision_text(case)
    if text != prefix + native["text"] or prefix.count(decision) != 1:
        raise ValueError("Unstable token boundary or ambiguous decision section")
    start = prefix.index(decision)
    intervals = [(start, start + len(decision))]
    readout = parse_choice(native["text"], case["choices"])
    if readout["span"] is not None:
        intervals.append(tuple(len(prefix) + x for x in readout["span"]))
    positions = [
        i
        for i, (a, b) in enumerate(spans)
        if a < b and any(a < end and b > begin for begin, end in intervals)
    ]
    if not positions:
        raise ValueError("Empty decision memory")
    return dict(ids=ids, positions=positions, readout=readout)


def as_three_slots(vector, probability):
    import torch

    if (
        vector.ndim != 1
        or not len(vector)
        or vector.requires_grad
        or not vector.is_floating_point()
        or not torch.isfinite(vector).all()
        or type(probability) not in (float, int)
        or not math.isfinite(probability)
        or not 0 <= probability <= 1
    ):
        raise ValueError("Invalid detached memory or probability")
    return vector.repeat(3, 1), torch.full((3,), float(probability), device=vector.device)


def repair_prefix(tok, prompt, draft, *, feedback=None):
    end = tok.convert_tokens_to_ids("<|end_of_text|>")
    if (
        not prompt
        or not draft
        or type(end) is not int
        or end < 0
        or any(type(i) is not int or i < 0 for i in list(prompt) + list(draft))
        or end in draft[:-1]
    ):
        raise ValueError("Invalid repair prefix")
    instruction = (
        "Check your answer against the original story and question. Correct it if mistaken "
        "and preserve it if already correct. End with exactly one final line in the form "
        "ANSWER: <choice number>."
    )
    if feedback is not None:
        if (
            type(feedback) not in (int, float)
            or not math.isfinite(feedback)
            or not 0 <= feedback <= 1
        ):
            raise ValueError("Invalid text-feedback probability")
        instruction = (
            "A verifier estimates a probability of "
            + json.dumps(float(feedback), allow_nan=False)
            + " that your previous answer is correct. Use this fallible judgment when "
            "checking the original story.\n\n" + instruction
        )
    suffix = (
        "\n<|start_of_role|>user<|end_of_role|>"
        + instruction
        + "<|end_of_text|>\n<|start_of_role|>assistant<|end_of_role|>"
    )
    return (
        list(prompt)
        + list(draft)
        + ([] if draft[-1] == end else [end])
        + tok.encode(suffix, add_special_tokens=False)
    )
