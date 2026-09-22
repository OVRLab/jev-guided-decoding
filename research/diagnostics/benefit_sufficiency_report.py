"""Editorial tables/examples from completed, independently audited R19 outcomes only."""

import argparse
import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--controls-results", type=Path)
    args = parser.parse_args()
    report, raw, folder = args.report, args.results, args.manifest
    data = runpy.run_path(str(ROOT / "research/iterations/benefit_sufficiency/data.py"))
    analysis = json.loads((report / "independent-analysis.json").read_text())
    if analysis["outcomes"] != 6096 or not analysis["weights_unchanged"]:
        raise ValueError("Completed audited R19 results required")

    rows = [json.loads(line) for line in (raw / "outputs.jsonl").read_text().splitlines()]
    cases = json.loads((folder / "test.json").read_text())
    lookup = {(r["case_id"], r["arm"]): r for r in rows if r["stage"] == "test"}
    example_arms = ["native", "relevance", "sufficiency", "dual", "benefit_gate"]
    if args.controls_results:
        control_rows = [
            json.loads(line)
            for line in (args.controls_results / "outputs.jsonl").read_text().splitlines()
        ]
        lookup.update({(r["case_id"], r["arm"]): r for r in control_rows})
        example_arms += ["instruction_always", "shuffled_sufficiency"]

    def pct(x):
        return f"{100 * x:.2f}"

    def interval(x):
        return (
            f"{100 * x['difference']:+.2f} [{100 * x['interval'][0]:+.2f}, "
            f"{100 * x['interval'][1]:+.2f}]"
        )

    lines = [
        "# R19 complete tables",
        "",
        "Quality is authored parser accuracy, Hotpot full-answer F1, or adapted SQuAD F1.",
        "Calls are standalone logical requests; benefit-gate requests were executed "
        "physically first.",
        "No cross-domain quality average is reported.",
        "",
    ]
    for domain in ("synthetic", "hotpot", "squad2"):
        group = analysis["domains"][domain]
        lines += [
            f"## {domain} · {group['count']} test inputs",
            "",
            "| Arm | Quality % | Calls | Active interventions | Mean uncached "
            "seconds* | Tokens | Capped |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
        for arm, r in group["arms"].items():
            lines.append(
                f"| {arm} | {pct(r['quality'])} | {r['calls']} | "
                f"{r['interventions']} | {r['mean_seconds']:.3f} | {r['tokens']} | "
                f"{r['token_caps']} |"
            )
        lines += [
            "",
            "Primary differences (percentage points), individual 99.1667% intervals:",
            "",
            f"- Dual minus relevance: **{interval(group['primary']['sufficiency'])}**.",
            "- Benefit-gate routing value above expected random at the same call "
            f"count: **{interval(group['primary']['routing'])}**.",
            "",
            "Exploratory differences, ordinary 95% intervals:",
            "",
        ]
        lines += [f"- {name}: {interval(r)}." for name, r in group["secondary"].items()]
        lines += [
            "",
            "| Arm | Answerable count / score % | Missing-evidence count / score % |",
            "| --- | ---: | ---: |",
        ]
        for arm, r in group["arms"].items():
            cells = []
            for cohort in ("answerable", "missing"):
                sub = r["subgroups"][cohort]
                cells.append(
                    f"{sub['count']} / "
                    + (pct(sub["quality"]) if sub["quality"] is not None else "n/a")
                )
            lines.append(f"| {arm} | " + " | ".join(cells) + " |")
        if domain == "squad2":
            lines += [
                "",
                "| Arm | Raw EM % | Raw F1 % | Adapted F1 % |",
                "| --- | ---: | ---: | ---: |",
            ]
            for arm, r in group["arms"].items():
                lines.append(
                    f"| {arm} | {pct(r['raw_em'])} | {pct(r['raw_f1'])} | {pct(r['quality'])} |"
                )
        suff = group["sufficiency_classification"]
        lines += [
            "",
            "Separate Jev sufficiency classification at 0.5: "
            f"{suff['correct_at_half']}/{suff['count']} correct against dataset "
            "answerability. This is not Granite answer accuracy.",
            "",
        ]
    lines += [
        "*Benefit-gate elapsed time includes physical HTTP waits. Other guided arms may reuse",
        "receipts; their uncached estimates add the original call duration. Serial FP32 L40S,",
        "hosted Jev, no throughput or colocated serving claim.",
        "",
    ]
    controls_path = report / "controls-analysis.json"
    if controls_path.exists():
        controls = json.loads(controls_path.read_text())
        lines += [
            "## Separately registered static/shuffled controls",
            "",
            "These are exploratory 95% comparisons registered during fitting, before test.",
            "Static instruction requires no Jev. Shuffling reuses main receipts; it "
            "adds no paid calls.",
            "",
            "| Domain | Control | Control score % | Dual minus control, pp [95% interval] |",
            "| --- | --- | ---: | --- |",
        ]
        for domain, group in controls["domains"].items():
            for arm, value in group.items():
                lines.append(
                    f"| {domain} | {arm} | {pct(value['quality'])} | "
                    f"{interval(value['dual_minus_control'])} |"
                )
        lines += [
            "",
            "One fixed permutation and the dual-calibrated instruction strength are used;",
            "this is not a search for the strongest possible static intervention.",
            "",
        ]
    (report / "tables.md").write_text("\n".join(lines))
    examples = [
        "# R19 first-by-ID diagnostic examples",
        "",
        "Selected deterministically from frozen metric differences; unblinded qualitative",
        "inspection is supplementary, not independent semantic regrading. F1 improvement",
        "can reflect answer length or incidental word overlap. No grades or policies change.",
        "Static control signals are canned; shuffled signals come from a recorded donor.",
        "",
    ]
    diagnostics = {}
    for domain in ("synthetic", "hotpot", "squad2"):
        cohort = sorted([c for c in cases if data["domain"](c) == domain], key=lambda c: c["id"])
        counts = {
            f"{called}_{outcome}": 0
            for called in ("called", "skipped")
            for outcome in ("benefit", "harm", "tie")
        }
        suffconf = {
            "answerable_low": 0,
            "answerable_middle": 0,
            "answerable_high": 0,
            "missing_low": 0,
            "missing_middle": 0,
            "missing_high": 0,
        }
        categories = {}
        for c in cohort:
            native, rel, dual, gate = (
                lookup[c["id"], arm] for arm in ("native", "relevance", "dual", "benefit_gate")
            )

            def quality(r, c=c):
                return data["quality"](c, r["grade"])

            delta = quality(dual) - quality(native)
            outcome = "benefit" if delta > 0 else "harm" if delta < 0 else "tie"
            called = "called" if gate["call_decision"] else "skipped"
            counts[f"{called}_{outcome}"] += 1
            prob = dual["sufficient"]
            if prob is not None:
                suffconf[
                    ("missing" if c["missing"] else "answerable")
                    + "_"
                    + ("low" if prob <= 0.35 else "high" if prob >= 0.65 else "middle")
                ] += 1
            for label, yes in [
                ("dual_metric_benefit", delta > 0),
                ("dual_metric_harm", delta < 0),
                ("sufficiency_improves_missing", c["missing"] and quality(dual) > quality(rel)),
                ("sufficiency_harms_answerable", not c["missing"] and quality(dual) < quality(rel)),
                ("gate_missed_benefit", not gate["call_decision"] and delta > 0),
                ("gate_avoided_harm", not gate["call_decision"] and delta < 0),
            ]:
                if yes and label not in categories:
                    categories[label] = c
        diagnostics[domain] = {
            "routing": counts,
            "sufficiency_bands": suffconf,
            "example_ids": {k: v["id"] for k, v in categories.items()},
        }
        for label, c in categories.items():
            references = json.dumps(c.get("references", [c["reference"]]), ensure_ascii=False)
            examples += [
                f"## {domain}: {label}",
                "",
                f"Case `{c['id']}`. Question: {c['question']}",
                f"Reference(s): {references}; missing evidence: {c['missing']}.",
                "",
                "| Arm | Frozen score | Sufficiency signal | Action | Output |",
                "| --- | ---: | ---: | --- | --- |",
            ]
            for arm in example_arms:
                r = lookup[c["id"], arm]
                text = r["text"].replace("|", "\\|").replace("\n", "<br>")
                signal = (
                    "canned 0.0"
                    if arm == "instruction_always"
                    else f"donor {r['sufficient']}"
                    if arm == "shuffled_sufficiency"
                    else str(r["sufficient"])
                )
                examples.append(
                    f"| {arm} | {data['quality'](c, r['grade']):.4f} | "
                    f"{signal} | {r['intervention_action']} | {text} |"
                )
            examples += (
                ["", "Evidence:", ""] + [f"- [{s['id']}] {s['text']}" for s in c["sources"]] + [""]
            )
    (report / "examples.md").write_text("\n".join(examples))
    (report / "descriptive-diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
    print(
        json.dumps(
            {"tables": True, "examples": sum(len(v["example_ids"]) for v in diagnostics.values())}
        )
    )


if __name__ == "__main__":
    main()
