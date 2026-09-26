"""Post-result R22 descriptions; no model calls, regrading or policy selection."""

import argparse
import json
from collections import Counter
from pathlib import Path
from statistics import mean


def paired(left, right):
    a, b = ({r["case_id"]: r for r in group} for group in (left, right))
    if len(a) != len(left) or len(b) != len(right):
        raise ValueError("Duplicate case")
    if a.keys() != b.keys():
        raise ValueError("Paired coverage mismatch")
    return dict(
        n=len(a),
        same_tokens=sum(a[k]["token_ids"] == b[k]["token_ids"] for k in a),
        same_correctness=sum(a[k]["grade"]["correct"] == b[k]["grade"]["correct"] for k in a),
        repairs=sum(not a[k]["grade"]["correct"] and b[k]["grade"]["correct"] for k in a),
        regressions=sum(a[k]["grade"]["correct"] and not b[k]["grade"]["correct"] for k in a),
    )


def read_rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def draft_kind(oracle):
    if oracle is None:
        return "unassessed"
    return "supported" if oracle["supported"] else "unsupported"


def describe(cases, output):
    cases = {r["id"]: r for r in cases}
    answers = read_rows(output / "test-answers.jsonl")
    journal = read_rows(output / "outputs.jsonl")
    prepared = {
        r["case_id"]: r
        for r in journal
        if r["job"].startswith("prepare/") and r.get("part") == "test"
    }
    by_arm = {
        f"{mode}/{seed}": [r for r in answers if (r["mode"], r["seed"]) == (mode, seed)]
        for mode, seed in sorted({(r["mode"], r["seed"]) for r in answers})
    }
    groups = {
        kind: [k for k, v in prepared.items() if draft_kind(v["draft_oracle"]) == kind]
        for kind in ("supported", "unsupported", "unassessed")
    }
    pairs = {}
    for seed in (2201, 2202):
        for base in ("native/0", f"constant/{seed}", f"permuted/{seed}", f"oracle/{seed}"):
            pairs[f"{base}->live/{seed}"] = paired(by_arm[base], by_arm[f"live/{seed}"])
    counts = {}
    for name, rows in by_arm.items():
        counts[name] = {}
        for kind, ids in {
            **groups,
            **{
                motif: [k for k, c in cases.items() if c["motif"] == motif]
                for motif in sorted({c["motif"] for c in cases.values()})
            },
        }.items():
            selected = [r for r in rows if r["case_id"] in ids]
            counts[name][kind] = dict(
                n=len(selected), correct=sum(r["grade"]["correct"] for r in selected)
            )
    examples = []
    native = {r["case_id"]: r for r in by_arm["native/0"]}
    live = {r["case_id"]: r for r in by_arm["live/2201"]}
    for category in ("repair", "regression", "invalid"):
        eligible = [
            k
            for k in cases
            if (
                (not native[k]["grade"]["correct"] and live[k]["grade"]["correct"])
                if category == "repair"
                else (native[k]["grade"]["correct"] and not live[k]["grade"]["correct"])
                if category == "regression"
                else not live[k]["grade"]["valid_color"]
            )
        ]
        for k in sorted(eligible)[:2]:
            examples.append(
                dict(
                    category=category,
                    case_id=k,
                    motif=cases[k]["motif"],
                    reference=cases[k]["answer"],
                    draft=prepared[k]["draft"],
                    draft_oracle=prepared[k]["draft_oracle"],
                    feedback=prepared[k]["feedback"]["granite_draft"],
                    native=native[k]["text"],
                    live=live[k]["text"],
                )
            )
    return dict(
        label="Post-result descriptive analysis; no new inference or changed grades",
        pairs=pairs,
        counts=counts,
        color_balance=dict(Counter(c["answer"] for c in cases.values())),
        feedback_accuracy={
            kind: dict(
                n=len(ids),
                support_decisions_correct=sum(
                    (prepared[k]["feedback"]["granite_draft"][0] >= 0.5) == (kind == "supported")
                    for k in ids
                ),
            )
            for kind, ids in groups.items()
            if kind != "unassessed"
        },
        draft_groups={k: len(v) for k, v in groups.items()},
        mean_draft_seconds=mean(r["draft_generation"]["seconds"] for r in prepared.values()),
        mean_api_seconds=mean(r["jev"]["seconds"] for r in prepared.values()),
        first_test_preparation_completed=min(r["at"] for r in prepared.values()),
        first_final_answer=min(r["at"] for r in journal if r["job"].startswith("test/")),
        examples=examples,
        training_input_tokens=sum(
            r["input_tokens"] for r in read_rows(output / "training-steps.jsonl")
        ),
        training_target_tokens=sum(
            r["target_tokens"] for r in read_rows(output / "training-steps.jsonl")
        ),
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cases", type=Path, required=True)
    p.add_argument("--results", type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(describe(json.loads(a.cases.read_text()), a.results), indent=2))


if __name__ == "__main__":
    main()
