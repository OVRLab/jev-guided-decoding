# Feature: Jev-guided intermediate reasoning

The owner requested investigating Jev as an active helper during inference. The
[investigation](docs/reasoning-step-investigation.md) and
[diagnostic report](reports/2026-09-20-reasoning-investigation/README.md) are complete;
the owner then authorized implementing the reasoning-search controller.
The [implementation](docs/reasoning-controller.md) now has offline coverage; live
mechanism validation is the next check. Broader held-out quality remains unproven.
See [LAUNCH.md](LAUNCH.md) and [LIVE.md](LIVE.md) for the initial prototype scope.

## Problem

The fixed step diagnostic gave correct decisions for both scorer rubrics, but the
Granite check exposed duplicate candidates, repeated premises, a missing-premise
hallucination in likelihood selection, and empty rejection in Jev mode. Correct
final text can also end with `step_budget` because the engine lacks a final phase.
The experiments establish neither improved quality nor general verifier accuracy.

## Implemented behavior and remaining evidence

1. Explicit reasoning/final states and reliable step boundaries with exact tokens.
2. Deduplicated candidates and bounded diversification before concluding no path exists.
3. Saved alternate branches and tested backtracking under global resource limits.
4. Separate judgments for grounded validity, progress, and final completion.
5. Remaining: compare unguided reasoning, likelihood search, final-only Jev selection, and step
   guidance on held-out cases with independent grading, several seeds, and actual work.

Jev remains the live evaluator; no surrogate critic or weight training is part of
this direction. Serving integration and colocated runtime performance need separate
evidence. Do not tune on the published diagnostic fixtures or treat empty rejection
as a corrected answer. The investigation specifies implementation tests and controls.
