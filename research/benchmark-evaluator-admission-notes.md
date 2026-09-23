# Evaluator admission findings before the full suite

Recorded 2026-09-23 during R25 training, before its held-out results. This is a
read-only upstream-code review and synthetic scoring probe, not a new benchmark
run, an evaluator implementation, or a change to any frozen study.

## MMLU-Pro

At revision `f418b116db00b065c2aea046518d8fcf74d39872`, the
[local evaluator](https://github.com/TIGER-AI-Lab/MMLU-Pro/blob/f418b116db00b065c2aea046518d8fcf74d39872/evaluate_from_local.py)
removes `N/A` options, uses subject-specific demonstrations, reduces their count
when the prompt exceeds its token allowance, and falls back to random choices
when answer extraction returns none. It calls its result scorer twice, advancing
the shared random state. A synthetic probe of the inspected scorer with ten
unparseable outputs, ten choices each and seed 12345 awarded **1/10 correct**,
although no model selected any answer. [Probe and source hashes](../reports/2026-09-23-evaluator-admission/probe.json).

The [API evaluator](https://github.com/TIGER-AI-Lab/MMLU-Pro/blob/f418b116db00b065c2aea046518d8fcf74d39872/evaluate_from_api.py)
also uses random fallback when rebuilding summaries. Its prompt serialization
and handling of markdown emphasis differ from the local runner. Therefore a
repository revision alone does not identify one invariant evaluation procedure.

The newer [API-X runner](https://github.com/TIGER-AI-Lab/MMLU-Pro/blob/f418b116db00b065c2aea046518d8fcf74d39872/evaluate_from_apiX.py)
supports retrying based on reference-answer correctness. The CLI default for
`retry_wrong` is zero, but the upstream README's example explicitly enables two.
That option cannot be used for our pass@1 comparison or for selecting a repair:
held-out reference truth would control which model attempt becomes the outcome.

Before final admission, freeze the exact entrypoint, prompts, demonstrations,
context treatment, option remapping, extraction and retry settings. Report
official-compatibility scoring separately from generated-answer correctness if
random fallback is retained for comparability. Count unparseable answers and
actual attempts explicitly. No full-task score is admitted by this review.

## MuSR and the existing readout boundary

The earlier [R23 readout amendment](public-baseline-readout-amendment.md) already
records MuSR's numbered-answer prompt and random fallback. Its project readout
is a separately named development measurement. The same distinction applies to
MMLU-Pro: neither a custom parser nor random scoring credit should silently become
evidence of improved reasoning. Existing R23–R25 metrics and results stay intact.

The [ten-task contract](benchmark-suite-contract-v1.md) remains the task inventory;
its pending admissions still require implementation, fixture parity and a frozen
run manifest before any complete-suite claim.
