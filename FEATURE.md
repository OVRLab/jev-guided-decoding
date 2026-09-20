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
6. Remaining: proposals that identify missing premises and finish with UNKNOWN;
   exact verdict-label reliability; larger fresh evaluation and independent checking
   of explanations/steps, beyond agreement on the final verdict word.

Jev remains the live evaluator; no surrogate critic or weight training is part of
this direction. Serving integration and colocated runtime performance need separate
evidence. Do not tune on the published diagnostic fixtures or treat empty rejection
as a corrected answer. The investigation specifies implementation tests and controls.
