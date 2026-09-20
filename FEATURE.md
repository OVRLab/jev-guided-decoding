# Next feature: evaluate the verifier's decisions

This is a proposed next experiment, not work already implemented or automatically
authorized by this document. See [LAUNCH.md](LAUNCH.md) and [LIVE.md](LIVE.md).

## Problem

The smoke test proves generation-time intervention but does not establish a quality
gain. It contains both an incorrect EOS rejection and accepted misleading wording.
Changing thresholds on those same examples would not establish generalization.

## Candidate work and acceptance evidence

1. Define a separate validation/test split, answer rubric, and independent grader.
2. Measure candidate quality before selection, selected-answer quality, incorrect
   acceptance, incorrect rejection, completion rate, and budget/error outcomes.
3. Compare baseline, equal-candidate likelihood selection, and Jev guidance using
   multiple seeds and actual compute/call counts; separate retries from selection gains.
4. Record prompt/rubric changes and calibrated thresholds before held-out testing.
5. Publish all scoped results, including regressions, with licensing and provenance.

This experiment should determine whether and where a serving optimization is worth
building. A vLLM implementation or weight training should not be bundled into it.
