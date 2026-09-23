"""Editorial tables after the frozen primary audit; no inference or changed grades."""

import argparse
import collections
import json
import re
import runpy
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument("--report", type=Path, required=True)
p.add_argument("--results", type=Path, required=True)
a = p.parse_args()
REPORT, BACKUP = a.report, a.results
names = {"synthetic": "Authored", "hotpot": "HotpotQA", "squad2": "SQuAD2"}
arms = {"native": "Native Granite", "static": "Static instruction", "dual": "Granite + Jev"}
data = json.loads((REPORT / "independent-analysis.json").read_text())
assert data["status"] == "complete"
if not (REPORT / "blind-review.json").exists():
    raise FileNotFoundError("Record the registered blind inspection before interpretation")
rows = [json.loads(x) for x in (BACKUP / "generation/outputs.jsonl").open()]
parts = [
    "# R20 results tables\n",
    "All semantic scores use the frozen, admitted Qwen3-14B judge. Unresolved "
    "judgments count as incorrect in the lower score and correct in the upper "
    "score. These are automated judgments, not human-certified accuracy.\n",
    "## Primary correctness\n",
    "| Domain | Arm | Correct / inputs | Unresolved | Lower–upper (%) |",
    "| --- | --- | ---: | ---: | ---: |",
]
for domain, d in data["domains"].items():
    for arm, s in d["arms"].items():
        parts.append(
            f"| {names[domain]} | {arms[arm]} | {s['correct']} / {s['n']}"
            f" | {s['unresolved']} | {s['lower'] * 100:.2f}–{s['upper'] * 100:.2f} |"
        )
parts += [
    "\n## Six registered paired comparisons\n",
    "Each interval uses 10,000 cluster bootstrap draws and 99.1667% nominal "
    "coverage; together the six comparisons target nominal 95% family coverage "
    "within R20. Effects are percentage points. There is no all-controls "
    "conjunction or pooled score.\n",
    "| Domain | Dual minus | Difference (pp) | Primary interval (pp) | Clusters |",
    "| --- | --- | ---: | ---: | ---: |",
]
for domain, d in data["domains"].items():
    for arm, s in d["comparisons"].items():
        lo, hi = s["interval"]
        parts.append(
            f"| {names[domain]} | {arms[arm]} | {s['difference'] * 100:+.2f}"
            f" | [{lo * 100:+.2f}, {hi * 100:+.2f}] | {s['clusters']} |"
        )
parts += [
    "\n## Answerability groups (descriptive)\n",
    "These groups were registered descriptively, not as additional primary "
    "endpoints. Wrong answerable responses include false refusals as well as "
    "wrong or incomplete answers; the binary grader does not provide a "
    "separately validated refusal taxonomy.\n",
    "| Domain | Evidence | Arm | Correct / inputs | Lower–upper (%) |",
    "| --- | --- | --- | ---: | ---: |",
]
for domain, d in data["domains"].items():
    for missing, v in d["by_missing"].items():
        for arm, s in v.items():
            parts.append(
                f"| {names[domain]} | {'Missing' if missing == 'True' else 'Answerable'}"
                f" | {arms[arm]} | {s['correct']} / {s['n']}"
                f" | {s['lower'] * 100:.2f}–{s['upper'] * 100:.2f} |"
            )
parts += [
    "\n## Historical scoring on these same outputs\n",
    "Authored uses the inherited abstention/answer parser; Hotpot uses answer "
    "F1; SQuAD uses the inherited adapted answer/abstention F1. These different "
    "score types are not substitutes for the semantic endpoint. The last column "
    "counts cases where full lexical credit (exactly 1.0) differs from a valid "
    "semantic Boolean; it is not a lexical error rate, since partial F1 is not a "
    "Boolean judgment.\n",
    "| Domain | Arm | Legacy mean (%) | Full-credit/semantic disagreements |",
    "| --- | --- | ---: | ---: |",
]
for domain, d in data["domains"].items():
    for arm, s in d["arms"].items():
        parts.append(
            f"| {names[domain]} | {arms[arm]} | {s['legacy_mean'] * 100:.2f}"
            f" | {s['legacy_semantic_disagreements']} |"
        )
parts += [
    "\n## Measured generation work (descriptive)\n",
    "One serial L40S study with hosted Jev; these are instrumented per-answer "
    "timings, excluding checkpoint download/loading, admission and independent "
    "judging. Arm order was randomized within input. Different answer lengths "
    "change elapsed work. This is not optimized serving throughput or a "
    "measurement of colocated Jev.\n",
    "| Arm | Final tokens | Mean tokens | Token-cap stops | Mean wall seconds | "
    "Median wall seconds | Mean Jev wait seconds | Physical requests |",
    "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
]
for arm, title in arms.items():
    r = [v for v in rows if v["arm"] == arm]
    tokens = sum(len(v["final"]["token_ids"]) for v in r)
    parts.append(
        f"| {title} | {tokens} | {tokens / len(r):.2f}"
        f" | {sum(v['final']['finish_reason'] == 'token_limit' for v in r)}"
        f" | {statistics.mean(v['wall_seconds'] for v in r):.3f}"
        f" | {statistics.median(v['wall_seconds'] for v in r):.3f}"
        f" | {statistics.mean(v['provider_wait_seconds'] for v in r):.3f}"
        f" | {sum(v['physical_jev_attempts'] for v in r)} |"
    )
parts += [
    "\n## Jev intervention actions\n",
    "These are realized policy actions, not causal estimates within the selected "
    "groups. A relevance decision with uniform source choices may apply no bias. "
    "Instruction attention and relevance attention affect the registered eleven "
    "heads; Jev does not select final tokens.\n",
    "| Domain | Relevance decision | Abstention instruction | Other/native "
    "action | Actual nonempty bias |",
    "| --- | ---: | ---: | ---: | ---: |",
]
for domain, title in names.items():
    r = [v for v in rows if v["arm"] == "dual" and v["domain"] == domain]
    count = collections.Counter(v["intervention_action"] for v in r)
    parts.append(
        f"| {title} | {count['relevance']} | {count['abstention']}"
        f" | {len(r) - count['relevance'] - count['abstention']}"
        f" | {sum(v['intervention_used'] for v in r)} |"
    )
parts += [
    "\nFor unresolved-judgment contrast sensitivities and exact values, see "
    "[independent-analysis.json](independent-analysis.json). All primary values "
    "come from that audit; work and policy counts come from its verified raw "
    "generation records.\n"
]
(REPORT / "tables.md").write_text("\n".join(parts))

# Descriptive examples: first case ID per domain and direction, fixed during grading.
G = runpy.run_path(str(ROOT / "research/iterations/semantic_evaluation/judge.py"))
cases = json.loads((ROOT / "research/protocols/semantic-evaluation-v1/test.json").read_text())
packets = json.loads((BACKUP / "blind-packets.json").read_text())
mapping = json.loads((BACKUP / "blind-mapping.json").read_text())
judgments = [json.loads(x) for x in (BACKUP / "judgments.jsonl").open()]
joined = G["join"](packets, mapping, judgments)
index = {(r["case_id"], r["arm"]): r for r in joined}
raw = {(r["case_id"], r["arm"]): r for r in rows}
selected = []
md = [
    "# R20 illustrative score repairs and regressions\n",
    "These are Qwen-scored examples and include judge mistakes. A citation-only response "
    "is incorrectly credited in the first authored score repair; an unfinished birth-date "
    "response is also credited for the static control. See [transfer diagnostics]"
    "(transfer-diagnostics.md). No grades have been changed.\n",
    "Selection rule fixed during grading, before treatment-level score "
    "inspection: within each domain and direction, take the first case by case "
    "ID where both grades are valid and dual changes native correctness. Show "
    "all three arms for each selected case. These are unblinded descriptive "
    "examples, not a representative error sample or additional endpoint. The "
    "separately registered [24-packet inspection](blind-review.md) has a "
    "different purpose.\n",
]
for domain, title in names.items():
    cohort = sorted(
        (
            c
            for c in cases
            if ("synthetic" if c["family"] not in ("hotpot", "squad2") else c["family"]) == domain
        ),
        key=lambda c: c["id"],
    )
    for direction in ("repair", "regression"):
        matches = []
        for c in cohort:
            n = index[c["id"], "native"]["result"]
            d = index[c["id"], "dual"]["result"]
            if n and d and n["correct"] != d["correct"] and d["correct"] == (direction == "repair"):
                matches.append(c)
        md.append(f"## {title}: {direction}\n")
        if not matches:
            md.append("No case satisfies this selection rule.\n")
            continue
        c = matches[0]
        sample = {"case": c, "direction": direction, "arms": {}}
        md.extend(
            [
                f"Case: `{c['id']}`. Question: {c['question']}\n",
                "Reference alternatives: "
                + json.dumps(c["references"], ensure_ascii=False)
                + ".\n",
            ]
        )
        for arm, title_arm in arms.items():
            r = raw[c["id"], arm]
            g = index[c["id"], arm]["result"]
            sample["arms"][arm] = {"text": r["text"], "judge": g}
            label = "correct" if g and g["correct"] else "incorrect" if g else "unresolved"
            md.append(f"**{title_arm}** — {label}:\n")
            md.append("> " + r["text"].replace("\n", "\n> ") + "\n")
            if g:
                md.append("Judge reason: " + g["reason"] + "\n")
        selected.append(sample)
md.append(
    "Full evidence and exact selected records: "
    "[illustrative-examples.json](illustrative-examples.json). HotpotQA and "
    "SQuAD content retain their report attribution notices. These labels are the "
    "frozen Qwen judgments, not fresh human adjudication.\n"
)
(REPORT / "examples.md").write_text("\n".join(md))
(REPORT / "illustrative-examples.json").write_text(
    json.dumps(selected, indent=2, ensure_ascii=False) + "\n"
)
print(json.dumps({"tables_written": True, "illustrative_cases": len(selected)}))

# Post-hoc syntax count prompted by the fixed examples; primary grades are unchanged.
pattern = r"(?:\s*\[(?:E|D|S)\d+\][.,;:]?\s*)+"
citation_rows = []
for r in rows:
    if re.fullmatch(pattern, r["text"]):
        citation_rows.append(
            dict(
                case_id=r["case_id"],
                arm=r["arm"],
                domain=r["domain"],
                response=r["text"],
                qwen=index[r["case_id"], r["arm"]]["result"],
            )
        )
citation_summary = []
for domain in names:
    for arm in arms:
        group = [r for r in citation_rows if r["domain"] == domain and r["arm"] == arm]
        citation_summary.append(
            dict(
                domain=domain,
                arm=arm,
                citation_only=len(group),
                qwen_correct=sum(r["qwen"] is not None and r["qwen"]["correct"] for r in group),
            )
        )
(REPORT / "citation-only-diagnostic.json").write_text(
    json.dumps(
        dict(
            status="post_hoc_descriptive_syntax_count_after_primary_analysis",
            regex_fullmatch=pattern,
            main_grades_modified=False,
            summary=citation_summary,
            records=citation_rows,
        ),
        indent=2,
    )
    + "\n"
)
