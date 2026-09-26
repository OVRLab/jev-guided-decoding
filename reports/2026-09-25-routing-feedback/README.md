# R28: repair selection versus internal feedback

Status: **completed and independently audited**; final review 26 September 2026, with all **539 eligible cases**,
**1,616 generated answers** and **539 successful Jev judgments** accounted for.
Granite generates every final answer token. This report concerns strict
instruction compliance, not general semantic correctness or a larger-model win.

Original Granite scores **408/539 (75.70%)**;
Jev-selected live repair scores **379/539 (70.32%)**.
Their difference is **-5.38 percentage points**, with a descriptive
95% paired interval **[-7.98, -2.78]**. Attribution rests on the
registered control comparisons below, not this native comparison alone.

## Registered results

| Policy | Strict prompt success | Loose prompt success | Repairs |
| --- | ---: | ---: | ---: |
| Original Granite | 408/539 (75.70%) | 417/539 (77.37%) | 0 |
| Always repair, constant signal | 360/539 (66.79%) | 369/539 (68.46%) | 539 |
| Jev selection, constant signal | 392/539 (72.73%) | 402/539 (74.58%) | 269 |
| Native confidence, constant signal | 381/539 (70.69%) | 391/539 (72.54%) | 269 |
| Random selection, constant signal | 389/539 (72.17%) | 396/539 (73.47%) | 269 |
| Jev selection, live signal | 379/539 (70.32%) | 387/539 (71.80%) | 269 |
| Jev selection, shuffled signal | 375/539 (69.57%) | 383/539 (71.06%) | 269 |

| Primary contrast | Difference (pp) | 98.75% interval | Wins / losses | Blocks (pp) |
| --- | ---: | ---: | ---: | ---: |
| Selection: Jev − random | +0.56 | [-2.23, +3.71] | 22 / 19 | +0.00, +1.12 |
| Selection: Jev − native confidence | +2.04 | [-0.56, +4.64] | 21 / 10 | +1.85, +2.23 |
| Feedback: live − constant | -2.41 | [-5.01, +0.19] | 10 / 23 | -2.22, -2.60 |
| Feedback: live − shuffled | +0.74 | [-1.11, +2.60] | 10 / 6 | +1.48, +0.00 |

Selection criterion: **not met**. Internal-feedback criterion: **not met**.
Each component requires both relevant adjusted lower bounds above zero, both
point estimates at least +2 pp, and a positive difference in each block.
Failure to meet that criterion does not establish equivalence or rule out
smaller benefits. All planned comparisons are retained.

## What failed, and what this does not settle

Every tested repair policy scores below original Granite on this cohort. Live
Jev repair turns **11 originally failing answers into passes** but turns **40
originally passing answers into failures**: a net loss of 29. With the same Jev
selection and checkpoint, constant-strength repair instead fixes five and breaks
21. Live feedback gains ten cases but loses 23 relative to that constant control.
These are paired strict-compliance transitions, not judgments of hidden reasoning.

A separately labeled post-result inspection clarifies the selection/repair gap.
Jev's 269 selected cases contain **116 of the 131 native failures**, alongside 153
native passes. The confidence selector includes 53 failures; the fixed random
selector includes 67. Thus Jev concentrates more existing failures in its selected
set on this cohort, but the repair pass corrects only 11 of those 116 and damages
40 of the 153 selected passes. Identifying an error is not the same outcome as
correcting it. These descriptive counts do not replace the registered policy
comparisons or their inconclusive adjusted intervals.

The fixed 269-repair quota matters: even a perfect error-ranking selector must
include at least 138 native passes because only 131 native answers fail. This
study tests matched-count allocation, not a policy that can abstain from almost
all repairs. It supports neither deploying this checkpoint as an accuracy upgrade
nor ruling out every lower-frequency repair policy. Any such policy needs a new
development protocol and fresh evaluation; this cohort is now exposed.

The [post-result diagnostic record](review-diagnostics.json) preserves these
counts and a grader-warning audit. The unchanged upstream language checker logged
one handled detection exception for a six-character, nonalphabetic candidate in
the **loose** evaluation of native case `ifeval/2596`. Its fallback accepts that
language constraint. Rechecking all 1,616 outputs reproduced every original strict
and loose boolean; no strict evaluation raised that exception. The primary results
are unchanged. The permissive upstream fallback remains a limitation of the
secondary loose metric; no grader patch or post-hoc score substitution was made.

## Design and scope

The [protocol](../../research/routing-feedback-plan-v1.md) was frozen before
inference at source `c418df6`. The
[manifest](../../research/protocols/routing-feedback-v1/manifest.json)
binds data, source, model, evaluator and checkpoint. Google Research IFEval has
541 original cases; keys 1122 and 1129 were excluded prospectively because their
punctuation parameters trigger random letter substitution in the unchanged
upstream checker. The denominator is 539 eligible cases, not an official full
541-case score. No exact or five-word-shingle near overlap was found with 2,040
unique prior project prompts; pretraining exposure and semantic overlap are not
excluded by that check.

The fixed rank-64 residual adapter has 262,144 parameters and acts after
zero-indexed decoder block 19. Original Granite 4.0-1B weights are frozen. One Jev
probability per native answer selects repairs and/or scales the branch during
second-pass generation. Jev is not queried every layer or token and supplies no
textual correction. Original prompt/draft token IDs are preserved; each repair
uses a fresh cache. All arms use FP32, greedy decoding and a 2,048-token ceiling.

Two fixed hash-balanced blocks contain 270 and 269 cases. Each selector chooses
135 and 134 repairs. Jev ranks by lowest compliance probability; native confidence
ranks by lowest mean generated-token log probability; random uses seed 2801.
The constant-signal potential outcome is generated on every case, while live and
shuffled outcomes are generated on the 269 Jev-selected cases. Shuffling preserves
the selected score distribution exactly within each block and forbids self-donors.

These policies reuse freshly collected deterministic potential outcomes; they are
not independently measured deployment latency or API-savings experiments. The
study called Jev on every native answer. Confidence/random/always-constant policies
have no inference-time Jev dependency but share a checkpoint trained using Jev
judgments in R25. They do not establish Jev-free training performance.

Twenty thousand paired, block-stratified bootstrap draws use seed 2800. The four
primary comparisons use 98.75% intervals; native comparisons use descriptive 95%
intervals. Inference conditions on this selection/donor assignment. Blocks are
consistency checks, not independent trained-model replications. Equal repair
counts and token ceilings do not imply equal realized computation.

## Work and incomplete answers

| Policy | Empty | Length stops | Generated tokens* | Processed slots* | Seconds* |
| --- | ---: | ---: | ---: | ---: | ---: |
| Original Granite | 0 | 13 | 158,265 | 198,645 | 5478.57 |
| Always repair, constant signal | 5 | 13 | 293,405 | 555,620 | 11099.41 |
| Jev selection, constant signal | 5 | 13 | 235,988 | 397,663 | 8948.29 |
| Native confidence, constant signal | 2 | 13 | 216,414 | 356,258 | 7760.40 |
| Random selection, constant signal | 1 | 13 | 225,509 | 375,452 | 8207.11 |
| Jev selection, live signal | 9 | 24 | 245,489 | 407,164 | 9332.56 |
| Jev selection, shuffled signal | 9 | 28 | 246,331 | 408,006 | 9402.07 |

* Policy work attribution includes native generation plus that policy's selected
repair generations. It excludes loading, warm-up, hosted Jev and orchestration;
reused times do not constitute separate policy latency measurements. Whole-study
collection produced **468,695 tokens**, with
**18876.90 generation seconds**.
The counterfactual collection cost is greater than any single selective policy.

The registered secondary 100-seed random-selection sensitivity gives
375–395 strict successes, mean
383.91; the primary random seed remains unchanged. No near
overlap cases were flagged, so that sensitivity uses the same cohort. Loose and
instruction-level scores are in the [complete analysis](replay/analysis.json);
they do not replace the registered strict primary outcome.

## Integrity, cost and resources

The independent audit covers exact prompt/repair prefixes and decoded final-token
paths, stopping decisions, native likelihoods, hook positions/scalars, donors,
allocation, complete job/work records, model bindings, unchanged base weights and
all provider request/response/usage receipts. The pinned original checker runs
locally after admission; references and checker metadata were absent on the GPU.
The checker passed 48 upstream tests and 12 strict pass/fail/empty fixtures before
inference. Numerical public replay reconstructs all seven policy scores and ten
paired contrasts without new inference or API calls.

Jev reports **374,322 charged input tokens**, **$0.01572152**,
with zero unresolved or maximum-charged requests. A separate successful preflight
cost $0.000015204. The AWS NVIDIA L4 instance was terminated after a
fresh exact-inventory/hash backup; its disk, security group and owned temporary
subnet are verified deleted. The existing default VPC was retained.

Compute is estimated at **$5.8434** using the verified Frankfurt
on-demand rate of $1.0064/hour and a conservative lifetime through cleanup. The
additional **$4.31** retains reserved disk, public-IP,
egress and contingency allowances rather than assuming unbilled usage is zero.
The resulting stage estimate is **$10.1691** and
cumulative estimate **$114.00 / $125**.
These are conservative accounting estimates, not invoices; final tax and network
charges remain unconfirmed. See [cost and cleanup summary](cost-and-cleanup.json).

## Reproducibility and interpretation

The [numeric replay](replay/) contains case-level boolean outcomes, fixed policy
allocation, the complete analysis and file hashes. It excludes questions,
generated answer strings/token IDs, API payloads and credentials. This supports
statistical replay; it does not replace independent response grading or reproduce
the private raw-token integrity audit. Use the
[reproduction guide](../../research/routing-feedback-reproduction.md) for acquisition,
a deliberate newly budgeted run, audit, grading and export.

All **652 repository tests** pass after completion, as do lint, formatting,
documentation checks and the package build. The final figure was visually reviewed.

The [focused manuscript](../../research/manuscript.md) places these results beside
[R27's complete Granite comparisons](../2026-09-25-completed-granite/README.md).
This study tests one adapter, backbone, layer and task family. It does not identify
an optimal insertion point or establish broad superiority, parameter efficiency,
colocated serving speed, or a novel general model architecture. The ten-benchmark
and larger-model objective remains unachieved. No additional architecture sweep,
model release or paper submission follows automatically from these results.
