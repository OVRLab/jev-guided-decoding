"""Development-frozen request-budget replay; never runs a model or provider."""

import argparse
import hashlib
import json
import runpy
import statistics
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
P = runpy.run_path(str(HERE.parent / "iterations/selective_attention/policies.py"))
A = runpy.run_path(str(HERE.parent / "iterations/selective_attention/analyze.py"))
R = runpy.run_path(str(HERE / "selective_routing.py"))
PLAN = ROOT / "research/selective-budget-frontier.md"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def choose_budgets(rows):
    scored = []
    for candidate in P["fit_gates"](rows)["candidates"]:
        gate = candidate["gate"]
        calls = sum(P["gate_decision"](gate, r["features"], r["case_id"]) for r in rows)
        scored.append(
            dict(
                gate=gate,
                quality=candidate["quality"],
                calls=calls,
                call_fraction=calls / len(rows),
                balanced_call_fraction=candidate["call_fraction"],
            )
        )
    return [
        dict(
            ceiling=ceiling,
            selected=min(
                [r for r in scored if r["call_fraction"] <= ceiling],
                key=lambda r: (-r["quality"], r["calls"], json.dumps(r["gate"], sort_keys=True)),
            ),
            candidates=scored,
        )
        for ceiling in (0.25, 0.5, 0.75)
    ]


def freeze_selection(selected, development_sha, plan_sha):
    return dict(
        protocol="r17-development-frozen-budget-frontier",
        development_selection_sha256=development_sha,
        plan_sha256=plan_sha,
        script_sha256=sha(__file__),
        policy=selected["selected"]["policy"],
        development_inputs=len(selected["gate_development"]),
        budgets=choose_budgets(selected["gate_development"]),
    )


def verify_selection(frozen, selected, development_sha, plan_sha):
    expected = freeze_selection(selected, development_sha, plan_sha)
    if {k: v for k, v in frozen.items() if k != "at"} != expected:
        raise ValueError("Frozen budget selection binding/reconstruction failed")


def branch_work(called, native, guided, pilot):
    branch = guided if called else native
    return dict(
        model_forwards=branch["model_forwards"] + (pilot["model_forwards"] if called else 0),
        processed_tokens=branch["processed_tokens"] + (pilot["processed_tokens"] if called else 0),
        discarded_tokens=len(pilot["token_ids"]) if called else 0,
        prefills=2 if called else 1,
    )


def analyze(manifest, results, main_analysis, selection):
    audit = json.loads(main_analysis.read_text())
    if not audit["audit_passed"] or any(
        sha(results / name) != digest for name, digest in audit["artifact_hashes"].items()
    ):
        raise ValueError("Main audit/artifact binding failed")
    selected = json.loads((results / "selected.json").read_text())
    frozen = json.loads(selection.read_text())
    verify_selection(frozen, selected, sha(results / "selected.json"), sha(PLAN))
    cases = json.loads((manifest / "test.json").read_text())
    outputs = [json.loads(s) for s in (results / "outputs.jsonl").read_text().splitlines()]
    index = {(r["case_id"], r["arm"]): r for r in outputs if r["stage"] == "test"}
    receipts = {
        r["key"]: r
        for r in map(json.loads, (results / "receipts.jsonl").read_text().splitlines())
        if r["status"] != "started"
    }
    summaries = []
    for budget in frozen["budgets"]:
        gate = budget["selected"]["gate"]
        groups = defaultdict(list)
        for c in cases:
            native, guided = index[c["id"], "native"], index[c["id"], "always"]
            observed = index[c["id"], "benefit_gate"]
            domain = "hotpot" if c["family"] == "hotpot" else "synthetic"
            key = "f1" if domain == "hotpot" else "correct"
            called = P["gate_decision"](gate, observed["features"], c["id"])
            receipt = receipts[guided["receipt_key"]] if called else None
            groups[domain].append(
                dict(
                    world=c["world_id"],
                    called=called,
                    native=native["grade"][key],
                    guided=guided["grade"][key],
                    quality=(guided if called else native)["grade"][key],
                    input_tokens=receipt["input_tokens"]
                    if receipt and receipt["status"] == "complete"
                    else 65536
                    if receipt
                    else 0,
                    unknown_calls=int(bool(receipt and receipt["status"] != "complete")),
                    **branch_work(called, native["final"], guided["final"], observed["pilot"]),
                )
            )
        all_rows = [r for rows in groups.values() for r in rows]
        domains = []
        for domain, rows in sorted(groups.items()):
            diffs = defaultdict(list)
            losses = defaultdict(list)
            for r in rows:
                diffs[r["world"]].append(r["quality"] - r["native"])
                losses[r["world"]].append(r["quality"] - r["guided"])
            domains.append(
                dict(
                    domain=domain,
                    **R["routing_value"](rows),
                    versus_native=A["paired"]([statistics.mean(v) for v in diffs.values()]),
                    versus_always=A["paired"]([statistics.mean(v) for v in losses.values()]),
                    called_benefits=sum(r["called"] and r["guided"] > r["native"] for r in rows),
                    called_harms=sum(r["called"] and r["guided"] < r["native"] for r in rows),
                    missed_benefits=sum(
                        not r["called"] and r["guided"] > r["native"] for r in rows
                    ),
                    avoided_harms=sum(not r["called"] and r["guided"] < r["native"] for r in rows),
                    work={
                        k: sum(r[k] for r in rows)
                        for k in (
                            "model_forwards",
                            "processed_tokens",
                            "discarded_tokens",
                            "prefills",
                            "input_tokens",
                            "unknown_calls",
                        )
                    },
                )
            )
        summaries.append(
            dict(
                development_ceiling=budget["ceiling"],
                gate=gate,
                development_call_fraction=budget["selected"]["call_fraction"],
                test_call_fraction=statistics.mean(r["called"] for r in all_rows),
                domains=domains,
            )
        )
    return dict(
        protocol=frozen["protocol"],
        audit_passed=True,
        main_analysis_sha256=sha(main_analysis),
        selection_sha256=sha(selection),
        script_sha256=sha(__file__),
        live_calls=0,
        new_model_forwards=0,
        interpretation=(
            "Offline deterministic branch replay; work and calls are reconstructed, "
            "not measured savings."
        ),
        budgets=summaries,
    )


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write("\n")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    f = sub.add_parser("freeze")
    f.add_argument("--development-selection", type=Path, required=True)
    f.add_argument("--output", type=Path, required=True)
    a = sub.add_parser("analyze")
    for arg in ("manifest", "results", "main-analysis", "selection", "output"):
        a.add_argument("--" + arg, type=Path, required=True)
    args = p.parse_args()
    if args.command == "freeze":
        selected = json.loads(args.development_selection.read_text())
        value = freeze_selection(selected, sha(args.development_selection), sha(PLAN))
        value["at"] = datetime.now(UTC).isoformat()
    else:
        value = analyze(args.manifest, args.results, args.main_analysis, args.selection)
    dump(args.output, value)
    print(json.dumps({"command": args.command, "budgets": len(value["budgets"])}))


if __name__ == "__main__":
    main()
