# R15 checkpoint repair before held-out inference

Prospective second amendment, 2026-09-22 Amsterdam. Preserve both the original
transport interruption and the first recovery segment. No policy was selected and
no held-out inference started in either segment.

The first recovery helper reused a write-once JSON utility for repeated zero-check
snapshots. Its second snapshot raised FileExistsError after saving the native and
zero model outputs. This was an implementation error, not a provider or model
quality failure. The segment contains 9,479 output records (90 retained provider
failures), 105 paid attempts (104 valid receipts and the original timeout), and
one saved full-vocabulary zero comparison. Model weights remained unchanged.
A preliminary detached-Git checkout launch also exited before any inference; its
log and exit status are retained separately.

The separate `evidence_v2_recovery2.py` helper now writes zero-check snapshots to a
new temporary file and atomically replaces the derived snapshot. It restores
completed individual jobs, reuses the existing successful receipt and native
output for the partial development block, and runs only that block's never-started
policy forwards. Existing completed blocks are skipped, including the common
failed provider block. No paid call or model operation is replayed.

Keep the one saved full-vocabulary comparison; add eleven on the next successful
contexts whose native forward has never started. The failed snapshot's second
zero output remains available for seven-label/token equality only. Thus there are
thirteen extra zero forwards across recovery segments, twelve with persisted
full-vocabulary comparisons, one without. Compared with the original schedule,
expect 34,777 output records and 34,687 actual forwards if no further incident
occurs; 1,632 scoring attempts remain unchanged. No scientific policy, selection
floor/tie break, data, grammar, statistics or API/cloud cap changes.

Two mocked full-development tests first reproduced FileExistsError and rejection
of a partially completed model block in the old helper, then exercised complete
selection with repeated checkpoint writes and partial-block resume in the repaired
helper. The fake scorer rejects duplicate case requests and the durable scheduler
rejects duplicate model jobs. These are offline orchestration tests, not live
model-quality evidence. Preserve source hashes for both earlier helpers and
register this new helper plus all segment hashes before continuation. Independently
audit both immutable raw prefixes, original timeout/charges and final schedules.
