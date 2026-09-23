# Conditional larger-model replication after R25

Recorded 2026-09-23 at approximately 22:10 UTC while R25 generates held-out repair
outputs, before inspection of any R25 held-out accuracy. This is a prospective
outline, **not an implemented or frozen run manifest**. It changes no R25 setting
or endpoint and authorizes no extra spending beyond the owner's cumulative $75.

## Admission and resource envelope

Proceed only if R25's registered spending gate passes: live seed-mean accuracy
minus native **and** minus matched constant is positive in **both** domains.
This is a resource decision, not a rule that erases any useful individual gain.
Retain all effects and uncertainty even if the gate is unmet. Require completed
primary/training/delivery audits, byte-verified cleanup and public archive replay
before loading a checkpoint into another paid study.

Provisionally reserve at most **$17** for this follow-up. The pre-R25 cumulative
estimate $36.773535 + the entire $20 R25 reservation + $17 is $73.773535 before
tax/separate network. Actual R25 accounting must be reconciled before admission;
do not treat an estimate as an invoice. One L40S with the existing 16-vCPU/64-GiB
profile and 80-GiB disk at the verified $1.75458082/hour, a nine-hour VM expiry,
eight-hour worker deadline and $0.25 Jev cap costs at most about $16.05 in those
included components. Confirm the live rate and remaining headroom before launch.
No H200, concurrent paid GPU, automatic extension or release claim.

R23 measured 623.44 generation seconds for 24 native-thinking 3B math questions,
about 26 seconds each, and about 70.50 seconds per MMLU-Pro development question.
The latter is only a rough workload proxy for unmeasured ARC science, not an ARC
timing estimate. These observations motivate a bounded run; they do not guarantee
completion. Keep every cutoff, deadline and incomplete case visible.
[Historical measurements](../reports/2026-09-23-public-baseline/analysis.json).

## Fixed candidate and fresh cases

Use R25 seed **2501**, chosen here without test results, for both live and matched
constant adapters. For each mode retain its already selected earliest best-dev
epoch. Do not choose the seed or epoch by R25 test accuracy, ensemble outputs or
train new weights. Bind the actual selected checkpoint hashes in a new manifest.

Target 128 new GSM8K and 128 new ARC-Challenge source-test questions. Use the same
pinned upstream data as R25, select by SHA256 ordering of `r26/<source-id>`, and
exclude every R23/R25 used question by ID and normalized exact question. Preserve
choice order and R25's answer formatting. Record split/content exclusions; this
does not establish freedom from near-duplicates or pretraining exposure. No test
question is discarded based on feedback, generation, length or grading outcome.

Compare original 4.0-1B, blind repair, constant adapter, live Jev adapter and native
4.2-3B on identical question text. The first four inherit R25's unchanged FP32
runtime, prompts, exact-token repair prefix and 1,024/512 draft/repair caps. Retain
the same predeclared p(correct) ≥ 0.5 native-retention replay separately for blind,
constant and live, with missing feedback retaining native. Count every actually
executed branch; offline replay is not measured saved execution or Jev calls.

The larger reference is `ibm-granite/granite-4.2-3b`, revision
`e459acceac81e5fe67c07d9cfc72329a332e7eb1`, with R23's native thinking profile:
BF16/SDPA, temperature 1, top-p .95, top-k disabled, 8,192 new tokens including
thinking, sampling seed 2601. Original 1B remains revision
`6a7381ba1f54d684ff508d991aeb7dc580157103`. These are distinct operating profiles,
not matched computation or a causal parameter-count experiment. Count thinking,
all final tokens, prefills, timings, cutoffs and hosted Jev; do not use card scores.

## Necessary implementation and verification before dispatch

Implement a separately versioned runner and test its capability/negative paths
first. Freeze source, data, selected checkpoint hashes, environment and all bounds.
Verify actual context lengths without truncation. Preserve exact final-token
ownership and apply R25's fixed independent readout to final-answer text only;
unfinished 3B thinking is not an answer. Include admission fixtures for thinking
boundaries, choice parsing, budget/deadline interruption and checkpoint/input
binding. Keep references out of model/API inputs and retry/selection decisions.

Use the tested v4 delivery rules for new Jev requests, with a fresh study ledger
whose costs are added to cumulative accounting. Persist every attempt and retained
unknown charge. Explicit-overload retries are separately reserved; ambiguous
timeouts are not replayed. Freeze exact incident/attempt limits in the new manifest
before requests, with no resets after observing failures.

Report both domains, the equal-domain mean, native-to-repair recovery/damage and
individual paired problem-bootstrap intervals for live versus native, constant,
blind and 3B. Use 10,000 task-stratified draws, seed 2600, and keep all cases in
the denominator. The checkpoint is fixed: no seed-population uncertainty is
estimated. This is a bounded independent-instance replication and larger-model
pilot, not a confirmatory ten-benchmark superiority claim or a model release.

If R25's gate fails, preserve this outline as unexecuted. Diagnose the complete
result without tuning on its exposed test set, and choose any different mechanism
through a separate prospective study. No follow-up launch is implied by writing
this document.
