"""Frozen R25 data, feedback, prefix and paired-analysis contracts."""

import hashlib
import json
import math
import random
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
C = runpy.run_path(str(ROOT / "research/iterations/benchmark_baseline/common.py"))
R = runpy.run_path(str(ROOT / "research/diagnostics/public_baseline_readout.py"))
J = runpy.run_path(str(ROOT / "research/iterations/public_critic.py"))
sha, dump = C["sha"], C["dump"]
SEEDS = (2501, 2502)
REPAIR = (
    "Check your previous solution carefully against the original problem. Correct any errors; "
    "preserve the conclusion if it is already correct. You may reason again. Finish with "
    "a separate line #### <numeric answer> for math, or Final: <letter> for a choice question."
)


def validate_case(case):
    if (
        set(case) != {"id", "task", "split", "prompt", "origin"}
        or any(not isinstance(v, str) or not v.strip() for v in case.values())
        or case["split"] not in ("train", "development", "test")
    ):
        raise ValueError("Invalid case or reference leakage")


def feedback_payload(case, draft):
    validate_case(case)
    return J["payload"]({k: case[k] for k in ("id", "task", "prompt")} | {"response": draft})


def repair_prefix(tokenizer, prompt, draft, *, probability=None):
    if not prompt or not draft:
        raise ValueError("Empty draft/prompt")
    end = tokenizer.convert_tokens_to_ids("<|end_of_text|>")
    framing = [] if draft[-1] == end else [end]
    instruction = REPAIR
    if probability is not None:
        gate_value(probability)
        instruction += (
            f" An independent critic estimates probability {probability:.4f}"
            " that your previous final answer is correct."
        )
    suffix = (
        "\n<|start_of_role|>user<|end_of_role|>"
        + instruction
        + "<|end_of_text|>\n<|start_of_role|>assistant<|end_of_role|>"
    )
    return list(prompt) + list(draft) + framing + tokenizer.encode(suffix, add_special_tokens=False)


def gate_value(value):
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError("Invalid gate probability")
    return value


def donors(cases):
    result = {}
    if len({c["id"] for c in cases}) != len(cases):
        raise ValueError("Duplicate cases")
    for task in sorted({c["task"] for c in cases}):
        group = sorted(c["id"] for c in cases if c["task"] == task)
        if len(group) < 2:
            raise ValueError("No separate donor")
        result.update({ident: group[(i + 1) % len(group)] for i, ident in enumerate(group)})
    return result


def choose_epoch(values):
    if not values or any(type(x) not in (float, int) or not math.isfinite(x) for x in values):
        raise ValueError("Invalid selection scores")
    return max(range(len(values)), key=lambda i: values[i]) + 1


def paired(cases, rows, arm, baseline, *, draws=10000):
    ids = [c["id"] for c in cases]
    if len(ids) != len(set(ids)) or not ids:
        raise ValueError("Invalid case coverage")
    maps = {}
    for name in (arm, baseline):
        selected = [r for r in rows if r["arm"] == name]
        if len(selected) != len(ids) or {r["id"] for r in selected} != set(ids):
            raise ValueError("Missing or duplicate outcomes")
        if any(
            type(r["correct"]) not in (bool, int, float) or not 0 <= r["correct"] <= 1
            for r in selected
        ):
            raise ValueError("Invalid correctness")
        maps[name] = {r["id"]: float(r["correct"]) for r in selected}
    diff = {i: maps[arm][i] - maps[baseline][i] for i in ids}
    groups = [
        [c["id"] for c in cases if c["task"] == task] for task in sorted({c["task"] for c in cases})
    ]
    rng = random.Random(2500)
    boot = sorted(
        100 * sum(diff[rng.choice(g)] for g in groups for _ in g) / len(ids) for _ in range(draws)
    )
    return dict(
        n=len(ids),
        delta_pp=100 * sum(diff.values()) / len(ids),
        ci95_pp=[boot[int(0.025 * draws)], boot[min(draws - 1, int(0.975 * draws))]],
        recovered=sum(max(v, 0) for v in diff.values()),
        damaged=sum(max(-v, 0) for v in diff.values()),
    )


def sources():
    paths = [
        *Path(__file__).parent.glob("*.py"),
        ROOT / "research/gated-repair-plan.md",
        ROOT / "research/iterations/learned_feedback/bridge.py",
        ROOT / "research/iterations/adaptive_attention/attention.py",
        ROOT / "research/iterations/public_critic.py",
        ROOT / "research/iterations/benchmark_baseline/common.py",
        ROOT / "research/diagnostics/public_baseline_readout.py",
        ROOT / "uv.lock",
        ROOT / "pyproject.toml",
        *list((ROOT / "src").rglob("*.py")),
    ]
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted(paths)}


def verify(folder):
    m = json.loads((folder / "manifest.json").read_text())
    if m["sources"] != sources():
        raise ValueError("Source freeze mismatch")
    C["verify_files"](folder, m["datasets"])
    return m


def normalize(text):
    return " ".join(text.casefold().split())


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()
