# R12-D: local work after provider interruption

Registered 2026-09-21, after V2 returned HTTP 400 on its seventh world. That request
has no receipt; its 65,536-input-token maximum reservation remains charged. The
provider's public API documentation describes error responses but gives no basis
to settle this particular request as zero. Do not replay it or send further paid
requests under this interrupted protocol. The original error and planned 60-world
denominator remain intact. No gate outcomes have been generated.

Two independent local checks remain useful and authorized:

1. Finish only the 53 never-attempted development proposal jobs, with the frozen
   V2 model, seeds and proposal policy. Do not repeat either successful or failed
   attempted jobs. Do not load credentials or dispatch any Jev request. Record a
   separate `proposals_only` status and new source/input/output hashes. Compute
   descriptive opportunity/coverage across all 60 worlds in a separate analysis;
   this is post-interruption development analysis, not a completed critic gate.
2. Replay the four successfully received V2 judgment batches at their exact recorded
   Granite prefixes. Check prefix and candidate identity before using their scores.
   Run native, zero, bounded Jev, shuffled-score and known synthetic-bias selectors,
   each with the same per-world sampling seed. Inspect full-distribution probability
   changes, KL <= 0.02, unchanged weights, and native/zero token-path equality.
   Continue the selected token with original Granite. A final-phase demonstration
   must use a consistent prompt and retain exact token provenance; otherwise label
   this explicitly a single-claim mechanism check, not a final-answer trial.

Replaying already paid judgments tests a control mechanism, not fresh hosted
integration or independent quality. Jev does not choose a final label. The four
available batches are selected by pre-error availability, not their quality.
No minimum number of improved answers is a success criterion for this check.
The synthetic bias is a mechanical positive control, not a Jev result.

Control defaults: strength 2, absolute log-bias <= 0.5, full-distribution KL <= 0.02,
reference = most-probable native root's greedy continuation; unavailable reference
utility produces an exact no-op. Support is usable only when assessability >= 0.5.
Shuffling permutes the utility multiset including missing values with a separate
seed. All unexamined tokens retain zero bias. Every mode has the same pad mask,
temperature 1 and top-p 1; final generation, if run separately, receives no bias.

Local MPS only, no new cloud resource. Completion stage cap 1,800 seconds; mechanism
cap 600 seconds. Freeze new runner/source/input manifests before each local run.
Preserve incomplete attempts, compute and hashes. There will be no third tuned
development proposal version or held-out trial under this follow-up.
