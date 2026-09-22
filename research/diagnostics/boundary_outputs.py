"""Artifact-bound descriptive R18 diagnostics; no new grading rule or inference."""

import argparse
import hashlib
import json
import runpy
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_binding(binding, main, cohort, results):
    if (
        not json.loads(main.read_text()).get("audit_passed")
        or sha(main) != binding["main_analysis_sha256"]
        or sha(cohort) != binding["test_cohort_sha256"]
        or not binding["artifact_hashes"]
    ):
        raise ValueError("Main audit/cohort binding failed")
    for name, digest in binding["artifact_hashes"].items():
        path = (results / name).resolve()
        if not path.is_relative_to(results.resolve()) or not path.is_file() or sha(path) != digest:
            raise ValueError("Raw artifact binding failed")


def abstained(row, domain):
    if domain == "squad2":
        return row["grade"]["abstained"]
    return domain == "synthetic" and row["grade"]["parsed"] == "UNKNOWN"


def describe(rows, cases, domain):
    supports_abstention = domain in ("synthetic", "squad2")
    abstentions = [r for r in rows if abstained(r, domain)]
    bare = sum(r["text"].strip().upper() == "UNKNOWN" for r in abstentions)
    return dict(
        cases=len(rows),
        eos=sum(r["final"]["finish_reason"] == "eos" for r in rows),
        token_limit=sum(r["final"]["finish_reason"] == "token_limit" for r in rows),
        empty_outputs=sum(not r["text"].strip() for r in rows),
        recognized_abstentions=len(abstentions) if supports_abstention else None,
        bare_unknown=bare if supports_abstention else None,
        natural_abstentions=len(abstentions) - bare if supports_abstention else None,
        wrong_abstentions=sum(not cases[r["case_id"]]["missing"] for r in abstentions)
        if supports_abstention
        else None,
        unparsed=sum(r["grade"]["parsed"] is None for r in rows) if domain == "synthetic" else None,
        provider_fallbacks=sum(r["provider_status"] == "failed_fallback" for r in rows),
        logical_calls=sum(r["logical_jev_calls"] for r in rows),
        physical_attempts=sum(r["physical_jev_attempts"] for r in rows),
    )


def call_outcomes(native, guided, calls):
    counts = Counter()
    for n, g, call in zip(native, guided, calls, strict=True):
        if call not in (0, 1):
            raise ValueError("Invalid logical call")
        effect = "beneficial" if g > n else "harmful" if g < n else "tied"
        counts[("called" if call else "skipped") + "_" + effect] += 1
    return {
        f"{c}_{e}": counts[f"{c}_{e}"]
        for c in ("called", "skipped")
        for e in ("beneficial", "harmful", "tied")
    }


def intervention_outcomes(rows, native):
    successful = [r for r in rows if r["logical_jev_calls"] and r["provider_status"] == "complete"]
    active = sum(any(t["active_heads"] for t in r["final"]["tokens"]) for r in successful)
    changed = [
        r for r in rows if r["final"]["token_ids"] != native[r["case_id"]]["final"]["token_ids"]
    ]
    return dict(
        successful_active_calls=active,
        successful_noop_calls=len(successful) - active,
        called_changed_token_paths=sum(r["logical_jev_calls"] for r in changed),
        changed_token_paths=len(changed),
    )


def analyze(manifest, results, main_analysis, binding):
    verify_binding(binding, main_analysis, manifest / "test.json", results)
    d = runpy.run_path(str(ROOT / "research/iterations/boundary_attention/data.py"))
    cases = {c["id"]: c for c in json.loads((manifest / "test.json").read_text())}
    outputs = [json.loads(line) for line in (results / "outputs.jsonl").read_text().splitlines()]
    test = [r for r in outputs if r["stage"] == "test"]
    index = {(r["case_id"], r["arm"]): r for r in test}
    if len(index) != len(test) or len(test) != len(cases) * 9:
        raise ValueError("Incomplete or duplicate diagnostic outcomes")
    groups, subgroups = defaultdict(list), defaultdict(list)
    for row in test:
        c = cases[row["case_id"]]
        domain = d["domain"](c)
        if d["grade"](c, row["text"]) != row["grade"]:
            raise ValueError("Frozen grade reconstruction failed")
        groups[domain, row["arm"]].append(row)
        fields = (
            {f: c[f] for f in ("family", "depth", "condition", "missing")}
            if domain == "synthetic"
            else {"missing": c["missing"], "article": c["article"], "sources": len(c["sources"])}
            if domain == "squad2"
            else {"question_type": c["question_type"]}
        )
        for field, value in fields.items():
            subgroups[domain, field, str(value), row["arm"]].append(row)

    def scores(rows):
        return dict(
            quality=statistics.mean(d["quality"](cases[r["case_id"]], r["grade"]) for r in rows),
            em=statistics.mean(r["grade"]["correct"] for r in rows),
            raw_em=statistics.mean(r["grade"].get("raw_em", r["grade"]["correct"]) for r in rows),
            raw_f1=statistics.mean(r["grade"].get("raw_f1", r["grade"]["f1"]) for r in rows),
            call_fraction=statistics.mean(r["logical_jev_calls"] for r in rows),
        )

    native = {ident: index[ident, "native"] for ident in cases}
    diagnostics = [
        dict(
            domain=dom,
            arm=arm,
            **describe(rows, cases, dom),
            **scores(rows),
            **intervention_outcomes(rows, native),
        )
        for (dom, arm), rows in sorted(groups.items())
    ]
    subgroup_rows = [
        dict(domain=dom, field=field, value=value, arm=arm, cases=len(rows), **scores(rows))
        for (dom, field, value, arm), rows in sorted(subgroups.items())
    ]
    routing = []
    for domain in ("synthetic", "hotpot", "squad2"):
        cohort = [c for c in cases.values() if d["domain"](c) == domain]
        native, guided = (
            [d["quality"](c, index[c["id"], arm]["grade"]) for c in cohort]
            for arm in ("native", "always")
        )
        for arm in ("boundary_gate", "pilot_gate", "boundary_random"):
            calls = [index[c["id"], arm]["logical_jev_calls"] for c in cohort]
            routing.append(dict(domain=domain, arm=arm, **call_outcomes(native, guided, calls)))
    names = (
        "Guidance improves quality",
        "Guidance harms quality",
        "Gate skips a benefit",
        "Gate skips a harm",
        "Correct recognized abstention",
        "Wrong recognized abstention",
        "Unrecognized nonempty output on missing evidence",
    )
    selected = {}
    for ident in sorted(cases):
        c = cases[ident]
        domain = d["domain"](c)
        native, always, gate = (index[ident, a] for a in ("native", "always", "boundary_gate"))
        n, g = (d["quality"](c, r["grade"]) for r in (native, always))
        abstention = abstained(gate, domain)
        matches = (
            g > n,
            g < n,
            not gate["logical_jev_calls"] and g > n,
            not gate["logical_jev_calls"] and g < n,
            abstention and c["missing"],
            abstention and not c["missing"],
            c["missing"] and not abstention and bool(gate["text"].strip()),
        )
        for name, hit in zip(names, matches, strict=True):
            if hit:
                selected.setdefault((domain, name), ident)
    examples = [
        dict(domain=domain, category=name, case_id=selected.get((domain, name)))
        for domain in ("synthetic", "hotpot", "squad2")
        for name in names
    ]
    lines = [
        "# R18 illustrative outputs",
        "",
        "First-by-ID examples from the [registered diagnostic rules]"
        "(../../research/boundary-output-diagnostics.md). These are neither representative",
        "samples nor blinded human judgments. Whole-answer lexical differences can reflect",
        "formatting or verbosity. Empty categories are retained. No grades were changed.",
        "",
    ]
    for item in examples:
        lines += [f"## {item['domain']}: {item['category']}", ""]
        ident = item["case_id"]
        if ident is None:
            lines += ["No matching case.", ""]
            continue
        c = cases[ident]
        lines += [
            f"Case `{ident}`; reference(s): `{json.dumps(c.get('references', [c['reference']]))}`.",
            "",
            f"Question: {c['question']}",
            "",
            "Evidence:",
            "",
            *[f"- [{s['id']}] {s['text']}" for s in c["sources"]],
            "",
        ]
        for arm in ("native", "always", "boundary_gate"):
            r = index[ident, arm]
            lines += [
                f"**{arm}**: quality {d['quality'](c, r['grade']):.4f}; "
                f"EM/correct {r['grade']['correct']}; {r['final']['finish_reason']}; "
                f"provider `{r['provider_status']}`.",
                "",
                "````text",
                r["text"],
                "````",
                "",
            ]
        gate = index[ident, "boundary_gate"]
        lines += [
            f"Gate requested Jev: `{gate['call_decision']}`. Recorded native features:",
            "",
            "```json",
            json.dumps(gate["features"], indent=2),
            "```",
            "",
        ]
    lines += [
        "External evidence retains [HotpotQA](HotpotQA-NOTICE.md) and "
        "[SQuAD2.0](SQuAD-NOTICE.md) CC BY-SA 4.0 attribution.",
        "",
    ]
    report = dict(
        audit_passed=True,
        main_analysis_sha256=sha(main_analysis),
        script_sha256=sha(__file__),
        artifact_binding=binding,
        new_model_forwards=0,
        new_api_calls=0,
        diagnostics=diagnostics,
        subgroups=subgroup_rows,
        routing_outcomes=routing,
        examples=examples,
    )
    return report, "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("manifest", "results", "main-analysis", "binding", "output", "examples"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    report, examples = analyze(
        a.manifest, a.results, a.main_analysis, json.loads(a.binding.read_text())
    )
    with a.output.open("x") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")
    with a.examples.open("x") as stream:
        stream.write(examples)
    print(json.dumps(dict(passed=True, groups=len(report["diagnostics"]))))


if __name__ == "__main__":
    main()
