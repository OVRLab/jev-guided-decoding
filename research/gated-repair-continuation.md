# R25 v3: durable feedback continuation and explicit neutral fallback

Registered 2026-09-23 after v2 stopped, before any optimizer update, development
selection or test generation. V1/V2 scientific files and raw prefixes stay immutable.

## Observed interruption and preserved cost

V2 passed all FP32 mechanical checks and produced 113 natural training drafts.
112 Jev requests succeeded (70,834 known input tokens); request 113, for
`gsm8k/train/2355`, raised `Jev retry or request budget exhausted`. The scorer
can produce this message after 429/529 or deadline exhaustion. The exact HTTP
status was not persisted, so it is not asserted. The failed reservation retains
65,536 input tokens, never zero cost. No optimizer step or test case ran.
All 20 worker files were backed up and hash-verified, then all owned resources
were deleted. V2 cloud estimate $0.6178348273 plus conservative API $0.00572754;
with V1, R25 has used $0.9169498445, cumulative $37.6904847666 before tax/network.

## No replay and declared missing-feedback behavior

1. Freeze all prior-file hashes/lengths, new source and this amendment. Verify
   original manifests, receipts, native prompt/token provenance, job coverage and
   model weight digest. Copy the six completed JSONL prefixes and budget ledger
   into a fresh run directory; append only. Reuse all 113 drafts and 112 scores.
   Never replay a dispatched API request or regenerate a completed model job.
2. The original failed request becomes explicitly unavailable feedback. Record
   actual probability as null and the **fixed neutral effective value 0.5** as a
   fallback, never as a Jev response. Retain its full unknown charge. All 384
   training cases remain; both live/constant training use gate 0.5 on unavailable
   cases. No targets, original weights, ranks, layers, seeds or schedules change.
3. Future calls still have one attempt per case. Save sanitized status code,
   Retry-After, response digest, exception category and usage state before recovery.
   Permit at most eight transient incidents including the historical one: explicit
   429/529, or the scorer's explicit transport/timeout error. Retain maximum usage,
   wait 60–300 seconds honoring Retry-After, then move to the next case. Never
   retry the failed case. A ninth incident, excessive cooldown, authentication,
   invalid schema/model, integrity error or unexpected exception stops the run.
   For never-started requests set both HTTP and scorer deadline to 90 seconds.
4. Every case has an availability record. When missing, live/inverted gates use
   neutral 0.5, and a shuffled missing donor contributes neutral 0.5. The text
   control omits the absent probability and uses the blind repair instruction.
   All planned generations still execute and receive independent reference grades.
   Report both failure-inclusive primary scores and feedback availability; do not
   silently exclude API failures or count neutral fallbacks as informative Jev.
5. The retention supplement always keeps the native answer when feedback is
   unavailable. For valid receipts its predeclared threshold remains 0.5. This
   added failure behavior is prospective, reference-free and separately recorded.
   The replay still does not measure avoided execution or avoided Jev calls.
6. Epoch selection still completes before any test draft/API/output. No test
   outcome informed these changes. The study is explicitly operationally amended,
   not an uninterrupted execution of v1/v2. Preserve all original primary endpoints.

## Bounds and verification

The cumulative cap stays $75 and combined R25 reservation stays $20. A replacement
single L40S/16vCPU/64GiB with 80GiB disk has a ten-hour poweroff and nine-hour worker
limit. Prior R25 cost + ten hours at $1.75458082/h + the entire $0.25 API allowance
is below $18.72, leaving cleanup headroom inside the existing stage reservation.
The copied ledger preserves its original $0.25 cap; this is not a fresh API budget.
All previous owned workers are deleted before creation. Backups run throughout;
verify remote/local hashes and owned-resource deletion after completion.

New continuation code inherits the frozen generation/loss/training routines and
adds request/availability ownership, prefix recovery and explicit error accounting.
Tests first: no duplicate dispatch or generation, exact prefix reuse, retained
unknown charges, null-versus-neutral distinction, transient-only recovery,
incident/cooldown bounds, fatal-schema/auth behavior and matched fallback gates.
The revised auditor validates actual receipts separately from neutral values,
charges per reservation, all planned outcomes, exact token framing and checkpoint
selection. Original raw records are never rewritten to satisfy an audit.
