# Feature: Jev-guided intermediate reasoning

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
The admitted main study is running on 400 fresh test problems across three seeds
and three arms (3,600 jobs), with source, settings, grading, and exclusions frozen.
