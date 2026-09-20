# Test-first guide

Follow [AGENTS.md](../AGENTS.md) and [the detailed workflow](../.claude/skills/tdd-workflow.md).
Write a behavior-focused test, run it, and verify the failure's reason before
implementation. Implement the smallest fix, rerun the regression, then check the
affected complete flow. A failure caused only by a broken environment does not
reproduce the target behavior; say what the observed failure actually establishes.

Include least-initialized and negative states, exact selected tokens, bounded
retries, empty/early EOS, malformed scores, and unknown usage when relevant.
Do not manufacture code tests for prose edits; validate links, commands, and docs
instead. Do not invent a coverage threshold or claim live checks from mocks.

For experimental changes, define the evaluation before tuning, capture baseline
results, and keep calibration/test separation. Report only metrics actually run;
do not require pass@k or repeated trials for unrelated small changes.
