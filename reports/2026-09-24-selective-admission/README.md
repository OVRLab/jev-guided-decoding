# R26-A: selective repair admission and full-suite cost profiling

**Preparation in progress; no fresh benchmark result yet.** The owner has raised
the cumulative budget to **$110**, with approximately $67.37 remaining from the
R25 estimate. This stage reserves at most $6 for real-runtime admission and cost
profiling on 50 already-exposed development cases before allocating a larger run.
No GPU has been launched at the time of this note.

The [parent plan](../../research/selective-benchmark-plan.md) covers the requested
benchmark comparison. The [prospective admission protocol](../../research/selective-benchmark-admission-plan.md)
fixes 50 exposed inputs, the unchanged R25 seed-2501 checkpoints, task-specific
prompts/readout, actual selective skips, six repair controls, and native original
Granite 4.0-1B / thinking Granite 4.2-3B / Qwen3-4B-Instruct-2507 profiles. It does
not select a checkpoint by new test scores or treat critic accuracy as generation.

All **572 local tests passed in 10.90 seconds** after 26 new capability/regression
tests. Initial missing-module failures, real batch-cache failures, and the actual
control-strength logging regression are preserved in [execution records](execution/).
The source metadata capture was subsequently moved before data-directory creation;
final source/data binding and clean-source status will be checked before dispatch.
Source and protocol freeze are not yet complete.

GPQA access returns HTTP 403 with the existing owner token. LongBench v2 contains
503 records with contexts up to 16,182,936 characters, beyond the current 16,384-token
prototype cap. Full MMLU-Pro contains 12,032 questions; IFBench contains 300; MuSR
contains 756; AIME 2026 contains 30; SimpleQA Verified contains 1,000. These source
counts are workload metadata, not completed evaluations. Evaluator, context and
agent-scaffold gaps stay visible in the ten-row contract.
