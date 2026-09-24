# R26-A: selective repair admission and full-suite cost profiling

**GPU profile running; output-format admission has failed; no fresh benchmark result.** The owner has raised
the cumulative budget to **$110**, with approximately $67.37 remaining from the
R25 estimate. This stage reserves at most $6 for real-runtime admission and cost
profiling on 50 already-exposed development cases before allocating a larger run.
One L40S was created at 05:23:26 UTC with a three-hour shutdown timer,
a 2.5-hour worker deadline and continuous backup/owned-resource cleanup supervision.

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
source/data/checkpoint hashes were then verified before dispatch, with clean source
`66d1f01`, data freeze `4e1316c`, attribution completion `39a5f7e`.
Remote setup/offline tests passed before the worker started.

GPQA access returns HTTP 403 with the existing owner token. LongBench v2 contains
503 records with contexts up to 16,182,936 characters, beyond the current 16,384-token
prototype cap. Full MMLU-Pro contains 12,032 questions; IFBench contains 300; MuSR
contains 756; AIME 2026 contains 30; SimpleQA Verified contains 1,000. These source
counts are workload metadata, not completed evaluations. Evaluator, context and
agent-scaffold gaps stay visible in the ten-row contract.


GPU zero-initial, zero-gate, gradient-ownership and cache comparisons passed.
All 50 native original-Granite drafts and eight serial probes are recorded. The
frozen independent readout parses only 14/40 non-IFBench drafts: numerous answers
name a choice but end in an empty `Final:` line. This is an output-contract failure,
not evidence that those 26 answers are all semantically wrong. Full benchmark
quality comparison is not admitted under this revision. Timing and all registered
controls/larger-model profiles continue within the original bounded stage; no
prompt, threshold, model, or scoring rule is being changed during that run.

The first 50 Jev requests produced 50 receipts, 34,885 input tokens and a $0.00146517
API estimate, with no unresolved/maximum-charge reservation. Final byte verification,
independent replay, model profiles and cloud cost/cleanup remain pending.


A [post-hoc format diagnostic](native-format-diagnostic.json) recognizes 19 more
unambiguous labeled full-option answers using the pre-existing R23 reader. The
R26 readout failed to integrate that supported form; this is an evaluation-code
integration defect. The primary 14/40 result and failed admission remain unchanged.
Recognizing these strings does not establish their semantic correctness or make
R26-A a fresh benchmark. Official task prompts and a prospectively corrected
readout are needed before later evaluation.

The [full-suite feasibility review](../../research/selective-benchmark-feasibility.md)
records source sizes, context limits, pending evaluator/access requirements, and
why short-question timings cannot price repository agents or long-context prefill.
The [source inventory](source-inventory.json) binds downloaded metadata/data bytes;
the [LongBench token workload](long-context-workload.json) covers all 503 inputs
on CPU with zero model-generation calls. Its [executed source](execution/long-context-profile.py.txt)
and [provenance](long-context-provenance.json) are retained. Run that source from
the repository root after placing the pinned LongBench `data.json` at
`results/selective-benchmarks-20260924/upstream/longbench.json`; it fetches the
pinned template/tokenizers/configs, never model weights. Compare input-token
counts and source hashes; wall-clock timing naturally varies.


The [separate readout amendment](../../research/selective-readout-amendment.md)
implements the known full-option fix with three regression tests. It is a future
protocol candidate, not a replacement for this run's frozen primary readout.
