# Granite + Jev research record

This is the persistent research notebook for OVRLab's investigation of Jev during
Granite inference. It includes negative results, corrections, new analyses, and
proposed experiments. It is a basis for a paper, not a claim of a successful model
release. All dates below are report dates; source artifacts retain execution times.

**Current conclusion:** [R14 internal evidence attention](../reports/2026-09-21-evidence-attention/README.md)
completed all 5,760 held-out outputs with no errors: Granite 42.22%, Jev attention
51.25% (+9.03 pp, adjusted interval [5.83, 12.50]). This supports a narrow gain
over native and shuffled controls; superiority over lexical/prompt highlighting
is inconclusive, so the all-four-control success criterion is unmet. Always
UNKNOWN obtains 50% on this balanced task, limiting absolute utility. Weights
remain unchanged; all task resources are deleted; cumulative estimate $9.27/$50.

The earlier step-selection and bounded output-logit policies did not demonstrate
a useful final-answer gain on their different tasks.
The [completed R13 comparison](../reports/2026-09-21-structured-study/README.md)
records 6,300 planned attempts on 300 authored worlds: 42.67% direct Granite,
37.00% staged, 35.44% likelihood and 36.00% Jev. All adjusted primary intervals
include zero. Jev ranks local claims accurately on these fixtures, but this does
not establish better final answers or an effective hidden-layer insertion point.
One provider failure is retained; every completed final belongs to Granite,
weights are unchanged, and both temporary GPU deployments are deleted.

| Read | Purpose |
| --- | --- |
| [Study register](study-register.md) | Every recorded live study, failed pilot, correction, and offline follow-up |
| [Architecture reassessment](architecture-reassessment.md) | Exact checkpoint, interface constraints, insertion-point decision and alternatives |
| [Attention refinement](../reports/2026-09-22-evidence-attention-refinement/README.md) | R15 implemented and locally verified; [fresh evaluation plan](evidence-attention-v2-protocol.md), cloud results pending |
| [Evidence-attention study](../reports/2026-09-21-evidence-attention/README.md) | Completed R14: eight arms, narrow native-baseline gain with inconclusive simpler controls; [frozen plan](evidence-attention-protocol.md), all traces and audit |
| [New diagnostic report](../reports/2026-09-21-architecture-reassessment/README.md) | Reproducible decomposition of 3,600 main and 48 development traces |
| [Next experiment](next-experiment.md) | Staged evidence gates, controls, budgets, held-out evaluation and stop rules |
| [Logit-guidance development](../reports/2026-09-21-logit-guidance/README.md) | Completed/interrupted pilots, full authored traces, mechanical controls and remaining limits |
| [Completed seven-arm study](../reports/2026-09-21-structured-study/README.md) | Full public traces, controls, adjusted intervals, diagnostics, figures and cleanup/cost evidence |
| [Related work](related-work.md) | Primary sources and what they do—and do not—support |
| [Paper draft](paper-draft.md) | Evidence-grounded manuscript scaffold and publication requirements |
| [Work plan](../docs/research-reassessment-plan.md) | Scope and validation for this reassessment |

The owner subsequently authorized [R13 recovery and a complete controlled comparison](structured-study-protocol.md). Two fresh API diagnostics passed. The first GPU pilot failed final formatting; the corrected common-label-grammar pilot passed all operational gates, and the test then stopped after 3,015 complete jobs and one provider failure. A [bounded continuation](structured-study-continuation.md) completed all 3,284 never-started jobs without another failure, retaining the original failure in the combined denominator. New admission tests operational correctness rather than requiring a positive pilot gain; the earlier R12 critic gate remains unpassed. [All attempts](../reports/2026-09-21-structured-study/README.md) are retained.

## Recording subsequent work

Before a live experiment, add a register entry with status **planned**, its
hypothesis, final-answer owner, source and data hashes, comparison arms, metrics,
independent grader, development/test split, budget, and stop rules. Commit the
protocol before inference. Record every attempted run and any change as a new
version; never silently repair an unfavorable result. Change the entry to
**completed**, **failed**, or **interrupted**, and link the dated report and
artifacts. Distinguish an offline reanalysis from additional model inference.

Only independent final-answer evaluation supports an answer-quality claim. A
working hook, a higher Jev score, or an interesting example does not. Updates must
say whether a mechanism is proposed, implemented, mechanically verified, or
evaluated for quality. Preserve this distinction in the eventual title/abstract.

The public record contains authored fixtures and permitted aggregates, IDs and
hashes. Some external benchmark traces remain private under the existing dataset
rights policy. This limits public per-example auditing and must remain disclosed.
No credentials, private operational files, or vendor documentation snapshots belong
in the research record. The earlier DeepSeek/KV-cache and concision work are separate
projects; their outcomes are not pooled into this Granite/Jev study.
