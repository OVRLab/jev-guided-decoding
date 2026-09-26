"""Artifact-bound R17 subgroups, output-form counts and predefined illustrative examples."""

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def describe(rows, cases):
    authored = all(cases[r["case_id"]].get("family") != "hotpot" for r in rows)
    abstentions = [r for r in rows if r["grade"]["parsed"] == "UNKNOWN"] if authored else []
    bare = [r for r in abstentions if r["text"].strip().upper() == "UNKNOWN"]
    return dict(
        cases=len(rows),
        eos=sum(r["final"]["finish_reason"] == "eos" for r in rows),
        token_limit=sum(r["final"]["finish_reason"] == "token_limit" for r in rows),
        recognized_abstentions=len(abstentions) if authored else None,
        bare_unknown=len(bare) if authored else None,
        natural_abstentions=len(abstentions) - len(bare) if authored else None,
        correct_abstentions=sum(r["grade"]["correct"] for r in abstentions) if authored else None,
        wrong_abstentions=sum(not r["grade"]["correct"] for r in abstentions) if authored else None,
        unparsed=sum(r["grade"]["parsed"] is None for r in rows) if authored else None,
        provider_fallbacks=sum(r["provider_status"] == "failed_fallback" for r in rows),
        logical_calls=sum(r["logical_jev_calls"] for r in rows),
    )


def analyze(manifest, results, main_analysis):
    main = json.loads(main_analysis.read_text())
    if not main["audit_passed"] or any(
        sha(results / name) != digest for name, digest in main["artifact_hashes"].items()
    ):
        raise ValueError("Main audit/artifact binding failed")
    cases = {c["id"]: c for c in json.loads((manifest / "test.json").read_text())}
    outputs = [json.loads(line) for line in (results / "outputs.jsonl").read_text().splitlines()]
    test = [r for r in outputs if r["stage"] == "test"]
    index = {(r["case_id"], r["arm"]): r for r in test}
    groups, subgroups = defaultdict(list), defaultdict(list)
    for row in test:
        c = cases[row["case_id"]]
        domain = "hotpot" if c["family"] == "hotpot" else "synthetic"
        groups[domain, row["arm"]].append(row)
        if domain == "synthetic":
            for field in ("family", "depth", "condition", "missing"):
                subgroups[field, str(c[field]), row["arm"]].append(row)
    diagnostics = [
        dict(domain=d, arm=a, **describe(rows, cases)) for (d, a), rows in sorted(groups.items())
    ]
    subgroup_rows = [
        dict(
            field=f,
            value=v,
            arm=a,
            cases=len(rows),
            accuracy=sum(r["grade"]["correct"] for r in rows) / len(rows),
            call_fraction=sum(r["logical_jev_calls"] for r in rows) / len(rows),
        )
        for (f, v, a), rows in sorted(subgroups.items())
    ]
    names = [
        "Authored: guidance fixes native",
        "Authored: guidance harms native",
        "Authored: gate skips and avoids harm",
        "Authored: gate skips and misses a fix",
        "Hotpot: guidance improves strict EM",
        "Hotpot: guidance harms strict EM",
        "Authored: correct natural abstention",
        "Authored: incorrect positive on missing evidence",
    ]
    selected = {}
    for ident in sorted(cases):
        c = cases[ident]
        native, always, gate = (index[ident, a] for a in ("native", "always", "benefit_gate"))
        n, g = native["grade"]["correct"], always["grade"]["correct"]
        authored = c["family"] != "hotpot"
        matches = [
            authored and g > n,
            authored and g < n,
            authored and not gate["call_decision"] and g < n,
            authored and not gate["call_decision"] and g > n,
            not authored and g > n,
            not authored and g < n,
            authored
            and gate["grade"]["parsed"] == "UNKNOWN"
            and gate["grade"]["correct"]
            and gate["text"].strip().upper() != "UNKNOWN",
            authored and c["missing"] and gate["grade"]["parsed"] not in (None, "UNKNOWN"),
        ]
        for name, hit in zip(names, matches, strict=True):
            if hit and name not in selected:
                selected[name] = ident
    examples = [{"category": name, "case_id": selected.get(name)} for name in names]
    report = dict(
        audit_passed=True,
        main_analysis_sha256=sha(main_analysis),
        script_sha256=sha(__file__),
        new_model_forwards=0,
        new_api_calls=0,
        diagnostics=diagnostics,
        subgroups=subgroup_rows,
        examples=examples,
    )
    lines = [
        "# R17 illustrative outputs",
        "",
        "Selected by the first-by-ID rules registered in the",
        "[diagnostic plan](../../research/selective-output-diagnostics.md), "
        "after the main artifact audit.",
        "These are examples, not representative sampling or blinded human grading. Differences in",
        "Hotpot exact match may reflect formatting instead of different factual content.",
        "",
    ]
    for example in examples:
        lines += ["## " + example["category"], ""]
        ident = example["case_id"]
        if ident is None:
            lines += ["No matching case.", ""]
            continue
        c = cases[ident]
        lines += [
            f"Case `{ident}`; reference **{c['reference']}**.",
            "",
            f"Question: {c['question']}",
            "",
            "Evidence:",
            "",
            *[f"- [{s['id']}] {s['text']}" for s in c["sources"]],
            "",
        ]
        for arm in ("native", "always", "benefit_gate"):
            row = index[ident, arm]
            lines += [
                f"**{arm}**; correct/EM {row['grade']['correct']}; F1 {row['grade']['f1']:.4f}; "
                f"termination {row['final']['finish_reason']}; provider {row['provider_status']}.",
                "",
                "```text",
                row["text"],
                "```",
                "",
            ]
        row = index[ident, "benefit_gate"]
        lines += [
            f"Gate requested Jev: `{row['call_decision']}`. Observed features:",
            "",
            "```json",
            json.dumps(row["features"], indent=2),
            "```",
            "",
        ]
    lines += ["Hotpot-derived evidence retains [CC BY-SA 4.0 attribution](HotpotQA-NOTICE.md).", ""]
    return report, "\n".join(lines)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--results", type=Path, required=True)
    p.add_argument("--main-analysis", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--examples", type=Path, required=True)
    a = p.parse_args()
    report, examples = analyze(a.manifest, a.results, a.main_analysis)
    with a.output.open("x") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")
    with a.examples.open("x") as stream:
        stream.write(examples)
    print(
        json.dumps(
            {
                "audit_passed": True,
                "descriptive_groups": len(report["diagnostics"]),
                "subgroups": len(report["subgroups"]),
            }
        )
    )


if __name__ == "__main__":
    main()
