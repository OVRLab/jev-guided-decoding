"""Unmodified larger-model comparator; no verifier, adapter or reference input."""

import hashlib
import json
import math
import runpy
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
S = runpy.run_path(str(HERE / "single.py"))
F = runpy.run_path(str(HERE / "feedback.py"))
MODEL = "ibm-granite/granite-4.2-3b"
REVISION = "e459acceac81e5fe67c07d9cfc72329a332e7eb1"


def dump(path, value):
    with path.open("x") as stream:
        stream.write(json.dumps(value, indent=2, allow_nan=False) + "\n")


def profile(name, ident):
    if name not in ("nonthinking", "thinking") or not isinstance(ident, str) or not ident:
        raise ValueError("Unknown larger-model profile or case")
    seed = int.from_bytes(hashlib.sha256(f"3200/{name}/{ident}".encode()).digest()[:8], "big")
    return dict(
        thinking=name == "thinking",
        limit=8192 if name == "thinking" else 2048,
        context_limit=16384,
        sampling=dict(seed=seed % 2**63, temperature=1.0, top_p=0.95),
    )


def cache_admission(model, ids, runtime):
    import torch

    runtime["idle_frozen"](model)
    if model.config.model_type != "granite" or not runtime["valid_ids"](model, ids):
        raise ValueError("Invalid larger-model cache admission")
    device = next(model.parameters()).device
    x = torch.tensor([ids], device=device)
    tick = time.monotonic()
    with torch.no_grad():
        first = model(
            x, use_cache=True, past_key_values=runtime["new_cache"](model), logits_to_keep=1
        )
        token = first.logits[0, -1].argmax().reshape(1, 1)
        full = model(torch.cat((x, token), dim=1), use_cache=False, logits_to_keep=1).logits.float()
        cached = model(
            token,
            past_key_values=first.past_key_values,
            use_cache=True,
            cache_position=torch.tensor([len(ids)], device=device),
            logits_to_keep=1,
        ).logits.float()
    tolerance = 0.25 if next(model.parameters()).dtype == torch.bfloat16 else 0.001
    error = float((full - cached).abs().max())
    equal = int(full[0, -1].argmax()) == int(cached[0, -1].argmax())
    if (
        not torch.isfinite(full).all()
        or not torch.isfinite(cached).all()
        or error > tolerance
        or not equal
    ):
        raise ValueError("Larger-model cache admission failed")
    return dict(
        passed=True,
        device=str(device),
        dtype=str(next(model.parameters()).dtype),
        cache_max_logit_error=error,
        cache_absolute_tolerance=tolerance,
        cache_argmax_equal=equal,
        seconds=time.monotonic() - tick,
        prompt_tokens=len(ids),
    )


class Comparator:
    def __init__(self, model, tok, eos, output, *, max_seconds):
        if (
            type(max_seconds) not in (float, int)
            or not math.isfinite(max_seconds)
            or not 0 < max_seconds <= 86400
        ):
            raise ValueError("Invalid larger-model deadline")
        self.runtime = runpy.run_path(str(HERE / "runtime.py"))
        self.runtime["idle_frozen"](model)
        if (
            model.config.model_type != "granite"
            or len(eos) != 1
            or not self.runtime["valid_ids"](model, eos)
        ):
            raise ValueError("Invalid larger-model configuration")
        self.model, self.tok, self.eos, self.output = model, tok, eos, output
        output.mkdir(parents=True, exist_ok=False)
        self.started, self.max_seconds, self.used = time.monotonic(), max_seconds, False

    def deadline(self):
        if time.monotonic() - self.started > self.max_seconds:
            raise TimeoutError("Larger-model comparator deadline")

    def run(self, cases, profiles):
        if self.used:
            raise ValueError("Duplicate larger-model phase refused")
        self.used = True
        if (
            not cases
            or len({c["id"] for c in cases}) != len(cases)
            or not profiles
            or len(set(profiles)) != len(profiles)
        ):
            raise ValueError("Invalid larger-model cohort or profile coverage")
        for case in cases:
            S["validate_case"](case)
            for name in profiles:
                profile(name, case["id"])
        before = self.runtime["weight_digest"](self.model)
        rows = []
        try:
            for case in cases:
                for name in profiles:
                    self.deadline()
                    settings = profile(name, case["id"])
                    ids = self.tok.apply_chat_template(
                        [dict(role="user", content=S["prompt_for"](case))],
                        tokenize=True,
                        add_generation_prompt=True,
                        thinking=settings["thinking"],
                    )
                    if not rows:
                        dump(
                            self.output / "mechanical-admission.json",
                            cache_admission(self.model, ids, self.runtime),
                        )
                    F["append"](
                        self.output / "jobs.jsonl",
                        dict(id=case["id"], arm=name, event="start", at=F["now"]()),
                    )
                    row = self.runtime["generate"](
                        self.model,
                        self.tok,
                        ids,
                        eos=self.eos,
                        limit=settings["limit"],
                        context_limit=settings["context_limit"],
                        sampling=settings["sampling"],
                        deadline=self.deadline,
                    )
                    row.update(
                        id=case["id"],
                        task=case["task"],
                        split=case["split"],
                        arm=name,
                        probabilities=None,
                        at=F["now"](),
                    )
                    F["append"](self.output / "outputs.jsonl", row)
                    F["append"](
                        self.output / "jobs.jsonl",
                        dict(id=case["id"], arm=name, event="finish", at=F["now"]()),
                    )
                    rows.append(row)
            after = self.runtime["weight_digest"](self.model)
            self.runtime["idle_frozen"](self.model)
            if before != after:
                raise ValueError("Larger-model weights changed")
            dump(
                self.output / "complete.json",
                dict(
                    outputs=len(rows),
                    backbone_before=before,
                    backbone_after=after,
                    seconds=time.monotonic() - self.started,
                    at=F["now"](),
                ),
            )
            return rows
        except BaseException as exc:
            dump(self.output / "failed.json", dict(error_type=type(exc).__name__, at=F["now"]()))
            raise
