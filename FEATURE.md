# Feature: Jev-guided intermediate reasoning

Current work completed: [R16 adaptive/free-text study](reports/2026-09-22-adaptive-attention/README.md).
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

Previous work completed: [R15 refinement](reports/2026-09-22-evidence-attention-refinement/README.md)
selected 12 heads, ln(16) and hard relevance gating. Fresh primary accuracy is
38.08% native, 47.33% previous Jev and 68.42% refined Jev, meeting the frozen
advancement criterion. All 34,777 planned records are retained, including 98
provider-dependent failures; 34,679 actual forwards and 1,632 scorer attempts
pass independent audit. All resources are deleted; 355 local tests pass.
Longer-chain challenge accuracy is only 41.67%, below always UNKNOWN (50%).
Remaining research is independent real-task evaluation and stronger long-chain
composition, using new development/test separation; the present test is now exposed.

The [R13 full study](reports/2026-09-21-structured-study/README.md) is complete:
6,300 planned jobs attempted, 6,299 completed and one provider failure retained.
Direct Granite scored 42.67%, staged 37.00%, likelihood 35.44% and Jev token
guidance 36.00%; all three adjusted primary intervals include zero. No useful
accuracy gain is established. Both temporary GPU deployments are deleted.
All 6,300 prompts and 6,299 completed token paths passed independent reconstruction;
weights are unchanged. All failed pilots and interrupted results remain available.

**Earlier external-benchmark comparison:** the [corrected 3,600-job generated-answer study](reports/2026-09-20-generated-answer-study/README.md)
is complete. Granite generated every final answer; Jev did not demonstrate an
accuracy gain over either control. Source, grading and data stayed frozen, and
the temporary cloud resources were deleted after verified backup retrieval.
The earlier experiments below provide historical context for the current contract.

The owner's subsequent request for a fresh architecture assessment and a durable
research record is covered by the [research notebook](research/README.md).
The [offline audit](reports/2026-09-21-architecture-reassessment/README.md) separates
first-batch rejection from absent valid proposals without changing prior results.
The [critic development and bounded logit prototype](reports/2026-09-21-logit-guidance/README.md)
have now run. Jev scoring was interrupted by HTTP 400; all development proposals
were subsequently collected without further paid calls. The real-Granite replay
check verifies probability control, unchanged weights and zero-bias identity, but
does not establish quality: grader coverage is 67% and all 20 final continuations
omit the requested closing frame. The held-out gate remains unexecuted.

The owner requested investigating Jev as an active helper during inference. The
[investigation](docs/reasoning-step-investigation.md) and
[diagnostic report](reports/2026-09-20-reasoning-investigation/README.md) are complete;
the owner then authorized implementing the reasoning-search controller.
The [implementation](docs/reasoning-controller.md) has offline coverage and a
[16-run live mechanism check](reports/2026-09-20-reasoning-controller/README.md).
That initial run completed 0/4 step-guided tasks because the generator supplied
repeated premises. The authorized [proposal follow-up](reports/2026-09-20-proposal-generation/README.md)
adds opt-in worked examples: eligible development batches rose from 0/8 to 6/8.
On six separate worlds with two seeds, step Jev, greedy, and likelihood each
matched 6/12 oracle verdicts; final-only Jev matched 5/12. All 48 attempts are
retained, including one ambiguous timeout and the declared continuation stage.
Early guidance avoided an invalid derivation in one controlled trace, but all
modes failed both UNKNOWN worlds. Broader quality improvement remains unproven.
The subsequent [fixed-choice check](reports/2026-09-20-fixed-verdict/README.md)
supplies all three final labels in code: existing step guidance matched 2/6 fresh
verdicts, fixed mode 6/6, and direct Jev 6/6. Both UNKNOWN cases were classified
correctly, while the paired Granite reasoning paths remained unchanged. This
demonstrates a final-classification improvement in the sample, not added accuracy
from Granite's reasoning or repaired intermediate derivations.
See [LAUNCH.md](LAUNCH.md) and [LIVE.md](LIVE.md) for the initial prototype scope.

## Problem

The fixed step diagnostic gave correct decisions for both scorer rubrics, but the
Granite check exposed duplicate candidates, repeated premises, a missing-premise
hallucination in likelihood selection, and empty rejection in Jev mode. In the earlier engine, correct
final text could also end with `step_budget` because it lacked a final phase.
The experiments establish neither improved quality nor general verifier accuracy.

## Implemented behavior and remaining evidence

1. Explicit reasoning/final states and reliable step boundaries with exact tokens.
2. Deduplicated candidates and bounded diversification before concluding no path exists.
3. Saved alternate branches and tested backtracking under global resource limits.
4. Separate judgments for grounded validity, progress, and final completion.
5. Opt-in proposal examples, a separate six-world/two-seed comparison, and an
   independent symbolic verdict oracle with all unfinished runs in the denominator.
6. Code-defined final Choices with separate reasoning provenance, reserved time/API
   budgets, explicit uncertainty/error states, and a direct-Jev control.
7. Remaining: useful reasoning recovery and justified explanations when premises
   are missing; larger fresh evaluation and independent checking of steps; evidence
   that Granite's intermediate reasoning adds value beyond direct classification.

Jev remains the live evaluator; no surrogate critic or weight training is part of
this direction. Serving integration and colocated runtime performance need separate
evidence. Do not tune on the published diagnostic fixtures or treat empty rejection
as a corrected answer. The investigation specifies implementation tests and controls.

The owner authorized the [controlled ProofWriter study](docs/proofwriter-experiment.md):
add unguided and final-only-filtered Granite reasoning with the same fixed final
Jev Choice, retain direct Jev and Granite-alone outcomes, and compare 200 theories across three seeds before
making a broader improvement claim. A separate development pilot precedes the
frozen test run. All attempted outcomes remain in the denominator.
The owner authorized a small cloud GPU for this study. The twelve-job CUDA pilot
completed on one L40S, followed by all 2,400 main jobs and 96 stress jobs across
24 new worlds. The [final report](reports/2026-09-20-controlled-study/README.md)
records 84.5% guided accuracy versus 84.7% direct Jev; all adjusted main comparison
intervals include zero. In 542/600 guided runs no step survived before the Choice.
The generated-answer controls have conflicting label-only versus label-and-reason
instructions, documented without changing their frozen scores. A future experiment
should reconcile this contract and improve useful proposal acceptance on development
data, then freeze a new evaluation on fresh problems. No follow-up tuning or reruns
of held-out cases are part of the completed study. Temporary cloud resources were
deleted after all result files were backed up and verified.

## Corrected owner objective: Granite supplies the final answer

The owner identified that the fixed-choice workaround had changed the research
question. The recorded 84.5% is a pipeline ending in Jev classification, not a
measurement of Granite's own improved answer. The owner authorized rebuilding the
experiment and spending up to $50 total on a small Nebius GPU and Jev.

The [replacement protocol](docs/generated-answer-experiment.md) compares single-path
Granite, multiple-candidate likelihood selection, and intermediate-only Jev selection.
All three retain Granite's accepted token continuation and use the same Granite
final-generation rule, including when no reasoning step is usable. Jev cannot choose
the final answer. Independent grading uses fresh logic cases and numerical word
problems. Development validation and a new test freeze must precede any new claim.

The first replacement pilot failed the shared format gate and remains recorded.
The [second 48-job development pilot](reports/2026-09-20-generated-answer-pilot-v2/README.md)
passed, using explicit EOS termination and a versioned TRUE/FALSE/UNKNOWN contract.
The admitted main study completed all 400 fresh test problems across three seeds
and three arms (3,600 jobs), with source, settings, grading, and exclusions frozen.
Math accuracy was 61.5% single, 67.8% likelihood selection, and 56.5% Jev; logic
was 52.7%, 52.8%, and 52.5%. Jev changed 484 intermediate selections but retained
no step in 572/600 logic runs. The math difference versus likelihood was negative
throughout the adjusted confidence interval; the other intervals included zero.
All 3,600 final generations passed the independent token audit, reproduced locally.
The [report](reports/2026-09-20-generated-answer-study/README.md) includes actual
latency/work, both incomplete outputs, all invalid formats, and the $3.29 estimated
compute/disk/Jev cost before tax and separate network charges.

Useful retained reasoning remains unproven. A next development investigation
should distinguish weak proposals from incorrect rejection before proposing a
fresh test; there is no authority here to tune on or rerun the completed test set.
No model training, changed weights, vLLM integration, merge, or release is claimed.


## R14 completed: internal attention to source evidence

The [frozen plan](research/evidence-attention-protocol.md) and [completed report](reports/2026-09-21-evidence-attention/README.md)
implement and evaluate a static Jev source-relevance map inside selected Granite
attention heads. All 5,760 held-out outputs completed, with a +9.03 pp native-baseline
gain (42.22% to 51.25%; adjusted interval [5.83,12.50]). The stricter all-controls
criterion failed because lexical/prompt comparisons remain inconclusive; always
UNKNOWN scores 50% on these constrained authored cases. All model decisions,
receipts, unchanged weights, costs and cleanup are audited and documented.

At R14 completion, no further cloud run was pending and open-ended transfer
remained untested. R15 and R16 subsequently evaluated their separately frozen
protocols. R16 adds full-vocabulary and external QA evidence above. Any next tuning
study must treat all completed cohorts as exposed and reserve fresh evaluation
cases. Concurrent serving and colocated Jev remain untested; no model training or
release is implied.
