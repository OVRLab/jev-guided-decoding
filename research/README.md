# Granite + Jev research record

This is the persistent research notebook for OVRLab's investigation of Jev during
Granite inference. It includes negative results, corrections, new analyses, and
proposed experiments. It is a basis for a paper, not a claim of a successful model
release. All dates below are report dates; source artifacts retain execution times.

**Current conclusion, 2026-09-21:** the tested intermediate text-selection policy
did not improve Granite-generated answers. The best next *testable hypothesis*
with the available interfaces is sparse, bounded intervention at Granite's output
logits, informed by Jev's judgments of short counterfactual continuations. This
requires a critic-quality gate first. The [new implementation and development report](../reports/2026-09-21-logit-guidance/README.md)
now verifies bounded probability changes, unchanged weights and zero-bias identity
on real Granite using replayed Jev scores. Development scoring was interrupted by
HTTP 400; unpaid proposal analysis found 67% grader coverage. No held-out gate or
new answer-quality study ran. No hidden layer has an established benefit.

| Read | Purpose |
| --- | --- |
| [Study register](study-register.md) | Every recorded live study, failed pilot, correction, and offline follow-up |
| [Architecture reassessment](architecture-reassessment.md) | Exact checkpoint, interface constraints, insertion-point decision and alternatives |
| [New diagnostic report](../reports/2026-09-21-architecture-reassessment/README.md) | Reproducible decomposition of 3,600 main and 48 development traces |
| [Next experiment](next-experiment.md) | Staged evidence gates, controls, budgets, held-out evaluation and stop rules |
| [Logit-guidance development](../reports/2026-09-21-logit-guidance/README.md) | Completed/interrupted pilots, full authored traces, mechanical controls and remaining limits |
| [Related work](related-work.md) | Primary sources and what they do—and do not—support |
| [Paper draft](paper-draft.md) | Evidence-grounded manuscript scaffold and publication requirements |
| [Work plan](../docs/research-reassessment-plan.md) | Scope and validation for this reassessment |

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
