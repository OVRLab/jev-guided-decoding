"""Fresh matched-memory candidate worlds; no live study is admitted by this helper."""

import runpy
from pathlib import Path

P = runpy.run_path(str(Path(__file__).resolve().parents[1] / "feedback_pairing/common.py"))


def make_data(sizes=(512, 64, 256), seed=31001):
    if (
        not isinstance(sizes, (tuple, list))
        or len(sizes) != 3
        or any(type(n) is not int or n < 2 or n % 2 for n in sizes)
    ):
        raise ValueError("Need three positive even split sizes")
    worlds, answers = P["worlds"](sum(sizes), seed)
    old = P["R29"]["make_data"]()[0] + P["worlds"]()[0]
    if {c["prompt"] for c in worlds} & {c["prompt"] for c in old}:
        raise ValueError("Previously exposed prompt overlap")
    cases, refs, start = [], {}, 0
    for split, size in zip(("train", "development", "test"), sizes, strict=True):
        for index, case in enumerate(worlds[start : start + size]):
            ident = f"contextual/{split}/{case['task']}/{index:04d}"
            cases.append(case | dict(id=ident, split=split))
            refs[ident] = answers[case["id"]]
        start += size
    return cases, refs
