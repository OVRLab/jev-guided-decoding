# R26-A: exposed-case admission and measured cost profiling

Registered 2026-09-24 before new model or Jev calls. This is the engineering first
stage of the owner's requested full benchmark comparison, within the increased
**$110 cumulative cap**. Starting estimated use is $42.62708084740686. Reserve at
most **$6**, including one L40S/16vCPU/64GiB, 80GiB disk, three-hour VM expiry,
2.5-hour worker deadline and a $0.15 conservative Jev ledger. The measured rate is
$1.7545808219/hour including disk, before tax/separate network. No fresh test case
is generated in this stage and no benchmark superiority claim is permitted.

## Fixed inputs and model profiles

Select 50 already-exposed cases deterministically: ten each R25 development math
and science, one per MMLU-Pro subject from R23 (14), two per MuSR family from R23
(six), and ten R23 IFBench prompts. Select by SHA256 of `r26-admission/<id>` within
groups. Keep references in a separate offline-grading file. Subject knowledge and
narrative questions retain their text/options; remove only the old output-format
placeholder instruction. IFBench prompts stay unchanged. New task-specific
repair instructions and the independent readout are fixed in versioned source.

- Original `ibm-granite/granite-4.0-1b`, revision
  `6a7381ba1f54d684ff508d991aeb7dc580157103`: FP32/SDPA, greedy, 2,048 new tokens.
- `ibm-granite/granite-4.2-3b`, revision
  `e459acceac81e5fe67c07d9cfc72329a332e7eb1`: BF16/SDPA, thinking enabled,
  temperature 1, top-p .95, top-k disabled, 8,192 new tokens.
- `Qwen/Qwen3-4B-Instruct-2507`, revision
  `cdbee75f17c01a7cc42f958dc650907174af0554`: BF16/SDPA, non-thinking model,
  temperature .7, top-p .8, top-k 20, min-p 0, 16,384 new tokens.

Use native chat templates, sampling seed 2601, length-sorted batches of four with
fixed ID tie-breaks, maximum 16,384 input tokens, no input truncation. Warm up each
model for eight generated tokens on the first exposed case, with work recorded.
Run eight prespecified exposed cases per model serially as an additional timing
probe; do not select preferred sampled answers from repeats. Batch and serial
sequences may differ numerically or in random-number consumption; profile work,
not best-of-repeat quality.

For the original-model drafts, use one Jev correctness judgment per case. Choices
and math retain the R24 final-decision question. IFBench instead asks whether all
explicit content/format requirements are fulfilled; this is a distinct task-specific
question, pinned before inference. No reference label or hidden test enters Jev.

Use R25 seed 2501's dev-selected live epoch 2 and constant epoch 1, binding exact
checkpoint hashes. No training. Actual selective arms are live, blind, matched
constant, same-live-weights constant .5, inverted and cyclic within-task shuffled
strength. Every arm retains native when p >= .5 or missing; otherwise repairs
serially with a 2,048-token ceiling and a fresh exact-prefix cache. The scalar
branch remains after block 19 and all final tokens come from Granite.

## Admission, failure and interpretation

Before model work, verify every bound source/data/checkpoint hash and no-overwrite
output ownership. On original Granite, run the established FP32 zero-initial,
zero-gate, gradient-ownership and cached/full checks, plus nonzero selected-adapter
cache comparisons on the first three fixed exposed cases. All must pass the
registered 1e-4 tolerances and next-token argmax checks before the profile proceeds.

The independent readout must parse at least 38/40 native math/choice/narrative
outputs (95%); all three models' primary outputs must be recorded, with no input
limit failure. Empty, cut-off and unfinished-thinking answers remain explicit;
length stops are not silently retried. This checks the output contract, not
correctness, general semantic quality or an optimal architecture. Any admission
failure is preserved and requires a new prospective development revision before
fresh evaluation, never a regrade of an already-run test.

Delivery permits four separately reserved attempts only after explicit 429/503/529,
with initial two-second pacing and 30/60/120-second backoff respecting bounded
Retry-After. Ambiguous timeouts are not replayed; retain their maximum charge and
native output. At most four missing cases and sixteen unknown-charge attempts;
auth/schema/integrity errors are fatal. Every receipt and decision is persisted.
No in-place resume of attempted model jobs or dispatched requests is admitted.

Independent post-run audits reconstruct prefixes, token ownership, selected output
references, actual skipped repairs, all forward slots, per-batch time allocation,
receipts and conservative charges. A fresh public-safe replay must reproduce the
analysis. Source counts and measured profiles then support an explicit per-task
full-suite cost/compatibility estimate. A profile is not a guaranteed invoice or
proof that long-context and agent evaluators have been admitted. Delete all owned
resources after hash-verified backup, even if admission fails.
