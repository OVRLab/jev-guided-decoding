# Granite + Jev research record

This is the persistent research notebook for OVRLab's investigation of Jev during
Granite inference. It includes negative results, corrections, new analyses, and
proposed experiments. It is a basis for a paper, not a claim of a successful model
release. All dates below are report dates; source artifacts retain execution times.

**Current investigation:** [R17 selective attention](selective-attention-plan.md), with
[architecture/method](../reports/2026-09-22-selective-attention/method.md) and
[prior-art review](selective-attention-related-work.md). Implementation and offline
validation are complete; held-out inference is running. The quality-first development
gate selected calls on every case; the separately registered
[budget frontier](selective-budget-frontier.md) will also examine explicit request
ceilings. No held-out R17 quality result yet.

**Latest completed study:** [R16 adaptive attention](../reports/2026-09-22-adaptive-attention/README.md).
**R16 interpretation:** constrained-task improvement is established within this
study; direct free-text performance regressed against matched R15, while dynamic
refresh and the primary HotpotQA contrast remain inconclusive.

All **16,120 main test outcomes** and **3,600 exploratory factorial outcomes**
are retained. On the new depth 1–6 constrained task, native Granite scores
**30.83%**, matched R15 **59.00%**,
and tuned Jev attention **72.00%**. The primary
tuned-minus-R15 contrast is **+13.00 pp [+8.67, +17.61]**.

Without an answer menu or required UNKNOWN token, open-explicit accuracy is
**27.33% native / 27.17% tuned**;
open-neutral accuracy is **26.17% / 21.50%**.
Refreshed versus static staged guidance changes accuracy by
**+0.42 pp [-3.33, +4.17]**. On 200 length-filtered HotpotQA questions,
direct answer F1 is **26.85% native /
29.67% tuned**, with primary contrast
**+2.82 pp [-1.35, +6.91]**. Primary intervals are 98.333%;
other comparisons are exploratory. These tasks and output contracts have separate
interpretations; historical R15 scores are from a different cohort and precision.

Granite generates every semantic token with unchanged weights; all arms use FP32.
The full report includes natural abstentions, answerable/missing breakdowns,
regressions, factor interactions, API failures, exact traces and three independent
audits. All temporary resources are deleted. New estimated cost is
**$8.52**, cumulative **$19.69/$50**
before tax/separate network charges. This is research-branch evidence, not a trained
checkpoint release or a general reasoning guarantee.

**Previous R15 finding:** [R15 refined evidence attention](../reports/2026-09-22-evidence-attention-refinement/README.md)
R15's fresh 600-world comparison scores **38.08% native Granite**, **47.33%
previous Jev attention**, and **68.42% refined Jev attention**. The paired primary
gains are +30.33 pp [26.67,34.00] versus native and +21.08 pp [17.92,24.25] versus
R14, using individual 97.5% intervals. The prespecified advancement criterion is
met. Lexical/prompt/shuffled comparisons are exploratory and favorable on this
primary cohort. Longer-chain challenge accuracy is only **41.67%**, below the
50% constant-UNKNOWN reference, so broad reasoning utility remains unestablished.

The complete schedule contains 34,777 records and 34,679 actual model forwards,
with two provider failures retained and no paid/model replay. Operational amendments,
including one after test start, are disclosed; the selected policy/test freeze and
weights stayed unchanged. All task cloud resources are deleted. New cost is about
**$1.90**, cumulative **$11.17/$50**. This is research
branch evidence, not a published trained checkpoint or unrestricted chat result.

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
| [Adaptive and unrestricted attention](../reports/2026-09-22-adaptive-attention/README.md) | R16 complete: three primary comparisons, eight panels, factorial controls, natural uncertainty and public HotpotQA traces |
| [Attention refinement](../reports/2026-09-22-evidence-attention-refinement/README.md) | R15 completed: 68.42% versus 38.08% native/47.33% prior; [frozen plan](evidence-attention-v2-protocol.md), full traces, amendments, challenge limits and audit |
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
