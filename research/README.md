# Granite + Jev research record

**R25 completed and audited:** always repairing lowers the combined score from
59.38% to 44.79%. The predeclared selective-retention replay instead reaches
66.67%: science improves **71.88% → 86.46%**, while math stays **46.88%**.
Formatting failures limit interpretation, especially for math. All 3,072 outputs
and 12 adapter checkpoints are archived; public replay matches all four main
analyses. All cloud resources are deleted. Cumulative estimate **$42.63/$75**
before tax/separate network; **546 local tests pass**. The ten-benchmark and
larger-model objectives remain unmet. See the [completed report](../reports/2026-09-23-gated-repair/README.md).


[Active north star](north-star.md), recorded 2026-09-23: substantial gains over
original Granite across ten leading benchmarks and outperformance of named larger
models. Candidate tasks/comparators and the research sequence are documented;
the versioned contract and four-domain diagnostic are implemented, while the full
ten-task suite remains unrun. Earlier experiments remain evidence for their scope.
[Evaluator admission findings](benchmark-evaluator-admission-notes.md) document
random fallback and reference-dependent retry behavior in pinned upstream scripts;
no new full-task evaluator or score is admitted by that source review.

[R23 public baseline — completed](../reports/2026-09-23-public-baseline/README.md):
76 development problems per model, all 152 outputs audited and publicly replayed.
Native 1B / newer thinking 3B score **19/24 / 21/24** math and **2/12 / 7/12**
IFBench; the separately labeled post-hoc choice readout gives **12/28 / 18/28**
MMLU-Pro and **6/12 / 4/12** MuSR. Original strict scores are preserved. Profiles
and token budgets differ; 3B has 13 length stops. These are not official full-suite
scores or a larger-model victory for Granite–Jev.

[R24 critic diagnostic — completed](../reports/2026-09-23-public-critic/README.md):
Jev flags **21/23 wrong native answers**, with **3/37 false flags on correct answers**;
all 60 requests and their original Granite inputs are audited. No answer is repaired
and every eligible answer is queried. This supports testing a feedback-dependent
repair mechanism, without establishing a beneficial insertion layer or call savings.
All cloud resources are deleted. Combined new estimate **$3.01**, cumulative
**$36.77/$50** before tax/separate network. All **507 local tests** pass.

[R22 — completed](../reports/2026-09-23-learned-feedback/README.md): a trained
65,568-parameter residual bridge after block 19 scores **92.19%**, identical to
its equally trained constant-feedback control; native scores **90.89%** on 384
fresh synthetic worlds. Shuffled/oracle feedback changes no final token sequences.
The +1.30 pp native contrast has a 97.5% interval [−1.30, +4.04]; no added Jev
benefit is observed. All artifacts/checkpoints are audited and public; original
model weights stay frozen. Resources are deleted, new cost **$1.18**, cumulative
**$33.76/$50** before tax/network. This is research, not a model release.

[R21 — completed](../reports/2026-09-23-semantic-feedback/README.md): focused local support judgments pass a fixed fresh replication, with 383/384 drafts assessed and all 36 assessed natural errors detected. One partial-name case remains unassessed despite high Jev support. This admits the adapter pilot, not a final-answer improvement claim.

[R20 blinded evaluation — completed](../reports/2026-09-23-semantic-evaluation/README.md):
native/Jev Qwen-judged scores are **30.21%/42.71% authored**, **74.17%/73.33%
Hotpot** and **61.67%/67.50% SQuAD**. Only the authored primary contrast excludes
zero; no domain establishes superiority over static instruction steering. The
blind review agrees on 21/24 packets and exposes answer-completeness errors in the
judge, so reliable semantic improvement and architectural superiority remain
unproven. All 1,584 generations, 30,112 final tokens and 528 successful Jev requests
pass reconstruction; public replay matches. All cloud resources are deleted.
Estimated new cost is **$2.32**, cumulative **$32.55/$50** before tax/network.
See the [evaluator failures](../reports/2026-09-23-semantic-evaluation/transfer-diagnostics.md)
and [paper draft](paper-draft.md#79-r20-blinded-semantic-evaluation-of-fixed-attention-interventions).

Previous completed work: [R19 expected benefit and evidence sufficiency](../reports/2026-09-22-benefit-sufficiency/README.md),
with [all controls](../reports/2026-09-22-benefit-sufficiency/tables.md),
[answer examples](../reports/2026-09-22-benefit-sufficiency/examples.md) and
[public reconstruction](../reports/2026-09-22-benefit-sufficiency/reproduce.md).
Native/dual scores are 26.74%/43.06% authored parser accuracy, 27.68%/32.95%
Hotpot answer F1 and 25.44%/33.10% adapted SQuAD F1. Material phrase-matching and
lexical-F1 artifacts prevent interpreting these as proven semantic improvements.
Static instruction steering without Jev scores 46.53%/32.90%/34.49%; dual
superiority is unestablished. A learned gate saves 54.44% of requests without
demonstrating reliable within-domain call selection. Both schedules, the failed
initial supplement, all corrections and 7,312 successful generations are retained.
Both GPU servers are deleted; estimated new cost is $3.00, cumulative $30.23/$50
before tax/network. R20, above, is the subsequent blinded evaluation.

Previous completed work: [R18 single-prefill boundary study](../reports/2026-09-22-boundary-attention/README.md),
with [method](../reports/2026-09-22-boundary-attention/method.md),
[all controls](../reports/2026-09-22-boundary-attention/tables.md) and
[prior-method comparison](boundary-attention-related-work.md).

**R18 completed:** the single-prefill gate raises authored accuracy from
**26.98% to 31.75%**, close to always Jev's **31.94%**, while saving **27.58%**
of requests. The exploratory selective-minus-native interval is **+4.76 pp
[1.79, 7.94]**. Hotpot native/always/selective F1 is **27.96% / 29.40% / 27.08%**;
SQuAD adapted F1 is **26.49% / 26.72% / 26.55%**. Primary routing intervals
include zero in all three domains, so reliable call selection is unestablished.

The gate uses **425/984 test requests**, saving **56.81% overall**, with one
prefill and zero discarded pilot tokens. Its domain call fractions are
72.42% / 18.33% / 6.67%; missing-evidence handling remains weak. Granite generates
every final token with unchanged weights and no required UNKNOWN spelling.
All **9,376 outcomes**, **184,889 final tokens** and **1,244 successful Jev
receipts** pass reconstruction; public archive replay reproduces the analysis.
There are zero provider failures. All temporary resources are deleted after
verified retrieval. New estimated cost is **$3.77**, cumulative **$27.23/$50**
before tax/separate network. This is research-branch evidence, with mixed external
quality, not a generally improved checkpoint or a serving-throughput benchmark.


This is the persistent research notebook for OVRLab's investigation of Jev during
Granite inference. It includes negative results, corrections, new analyses, and
proposed experiments. It is a basis for a paper, not a claim of a successful model
release. All dates below are report dates; source artifacts retain execution times.

**Previous completed study:** [R17 selective attention](../reports/2026-09-22-selective-attention/README.md),
with [architecture/method](../reports/2026-09-22-selective-attention/method.md),
[request-budget results](../reports/2026-09-22-selective-attention/budget-frontier.md)
and [prior-art review](selective-attention-related-work.md).

**R17 completed:** Jev guidance raises authored free-text accuracy from
**28.77% to 33.13%**, and HotpotQA answer F1 from **25.23% to 28.76%**.
The primary 98.75% intervals include zero: **+4.37 pp [0.00, 8.93]** and
**+3.53 pp [−1.47, 8.58]**. Development selected the existing R16 policy;
new timing/conservation variants did not win that selection.

The live gates called on **every input**, saving no requests and adding pilot work.
In a separately registered **offline replay**, a development-frozen budget rule
uses 21.43% of calls on authored tasks for 31.55% accuracy, but only 25.00% Hotpot F1
at 18.50% calls. This is a limited routing signal, not measured deployment savings
or reliable transfer. All three replay budgets and negative findings are retained.
Natural abstention remains poor, and overall authored scores stay below the 50%
constant-abstention reference. Granite owns every final token; weights are unchanged.

All **8,364 development/test outcomes** pass token/input/source/weight and public
archive replay audits. **860 Jev attempts succeeded, with no provider failures**.
New estimated cost is **$3.77**, cumulative **$23.46/$50** before tax/separate
network; all temporary GPU, disk and network resources are deleted. No generally
superior architecture or trained model release is established.

**Previous completed study:** [R16 adaptive attention](../reports/2026-09-22-adaptive-attention/README.md).
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
| [Single-prefill boundary attention](../reports/2026-09-22-boundary-attention/README.md) | R18 complete: nine arms, actual conditional dispatch, authored gain, uncertain routing, mixed external transfer and seven figures |
| [Selective evidence attention](../reports/2026-09-22-selective-attention/README.md) | R17 complete: nine held-out arms, all-call gate failure, three offline budgets, natural-answer failures and six figures |
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

The first broad-capability stage is the completed [R23 public baseline diagnostic](../reports/2026-09-23-public-baseline/README.md),
with [pinned development inputs](protocols/public-baseline-v1/manifest.json).
It establishes native 1B/3B behavior before selecting another Jev mechanism.

The [ten-benchmark contract v1](benchmark-suite-contract-v1.md) records primary
metrics, source revisions, admission gaps and final-scorecard rules.

[R24 public-answer critic diagnostic](../reports/2026-09-23-public-critic/README.md)
is complete: 21/23 native errors flagged, with 3/37 correct answers falsely flagged.
This supports a selective-repair hypothesis; it does not measure repaired outputs.

[R25 gated natural-draft repair](../reports/2026-09-23-gated-repair/README.md) is
complete: the internal live branch changes answers when feedback changes but
always-repair regresses. Predeclared retained-live science rises from 71.88% to
86.46%, with math unchanged; post-hoc inspection identifies real choice corrections
and substantial format confounds. All attempts, checkpoints, raw evidence and
public replays are preserved. The larger-model gate is false; that outline remains
unexecuted. Combined R25 estimate $5.85; cumulative $42.63/$75, resources deleted.

The separate [evaluator admission inspection](benchmark-evaluator-admission-notes.md)
finds a pinned MMLU-Pro scoring path that can randomly credit failed answer parsing,
and a separate gold-controlled retry option. These read-only findings are not
R25 results and do not admit a full-suite evaluator; the recorded source revisions
and synthetic probe preserve the evidence for correcting the future evaluation path.
