"""Thin R15 wrapper; the frozen R14 hook/runtime remain unmodified."""

import copy
import runpy
from pathlib import Path

P = runpy.run_path(str(Path(__file__).with_name("policies.py")))


def forward(runtime, encoded, policy, raw_scores, *, full_logits=False):
    bound = copy.deepcopy(encoded)
    kwargs = {"heads": None, "full_logits": full_logits}
    if policy is not None:
        if policy["scope"] not in ("question", "answer"):
            raise ValueError("Unknown query scope")
        if policy["scope"] == "answer":
            bound["query_start"] = len(bound["input_ids"]) - 1
        mapped = P["map_scores"](raw_scores, policy["mapping"])
        kwargs.update(heads=policy["heads"], scores=mapped, strength=policy["strength"])
    result = runtime.forward(bound, **kwargs)
    record = result[0] if isinstance(result, tuple) else result
    record.update(
        policy=copy.deepcopy(policy),
        raw_scores=copy.deepcopy(raw_scores),
        query_start=bound["query_start"],
    )
    return result
