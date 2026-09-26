# R15 operational recovery amendment

Registered 2026-09-22 Amsterdam after a development transport failure, before
selection or any held-out model/scorer operation. This amends admission and
scheduling, not the immutable original protocol or its scientific hypotheses.

## Observed interruption

The original frozen `be58b72` run completed 102 development contexts: 9,294 model
outputs including twelve zero checks, and 102 valid Jev receipts. Its 103rd request
failed with an ambiguous transport timeout (no status code or usage receipt).
The runner stopped as specified; its model weights remained identical. There are
no model outputs for that context and no selected policy or test/challenge outputs.
The HTTP client timeout was 30 seconds within the scorer's 45-second deadline.
No paid attempt is replayed. Original files are retained byte-for-byte separately.

## Prospective recovery rules

1. Freeze this amendment, the separate recovery helper and hashes/byte lengths of
   all original result files before restarting. Verify the original inference,
   protocol and dataset hashes. Copy raw JSONL prefixes into a new output directory
   and append only; retain original metadata/completion in the stopped-run artifact.
2. Restore durable started keys and refuse duplicates. Reuse completed development
   blocks. For the failed context run its never-started native forward once, and
   record all ninety guided configurations as provider failures without model
   tokens. Each counts incorrect in its planned accuracy denominator, including
   R14. Compute log-probability tie breaks on the common successful contexts only;
   do not invent logits for failures. Original class floors and selection order hold.
3. Raise both HTTP timeout and scorer deadline to 90 seconds for never-started
   requests only. Keep one attempt, identical provider payload/rubric and model.
   Permit at most three transport/429/529 incidents total, including the original.
   After a new admitted incident wait 60–300 seconds according to Retry-After,
   retain maximum unknown usage, and move to the next context. Never replay the
   failed request. Authentication, schema/model, integrity and model-forward errors
   still stop the run. A fourth transient incident stops it too.
4. On held-out incidents retain all eight dependent arms as failures; independent
   arms still generate. Planned denominators remain intact. Publish both the
   failure-inclusive result and incident counts; no silent case exclusion.
5. The original twelve zero/native pairs retain exact seven-label logits and
   token identity. Their full-vocabulary deltas were only in memory when the run
   stopped, so no persisted full-vocabulary claim is made for them. Add twelve
   zero forwards on the first twelve successful never-started development contexts,
   using their already-planned native forwards, and persist each full-vocabulary
   comparison immediately. This is twelve extra model jobs, never a replay.
6. Freeze selection before opening held-out inference. All 90 policies, cohorts,
   prompts, grading, two primary contrasts, intervals and advancement criteria are
   unchanged. This is a transparently amended study, not pristine execution of the
   initial protocol. No held-out outcome informed the amendment.

## Plan, bounds and verification

Affected files: separate `research/iterations/evidence_v2_recovery.py`, independent
analysis, recovery tests and documentation; the frozen inference glob is untouched.
Test failure-inclusive grading, retained charge, duplicate refusal and bounded
transport admission. The first three new tests failed because the recovery module
did not exist, then passed after implementation; an additional mocked transport
flow checks conservative charging and refusal to replay. Audit original prefixes,
complete/failed/started schedules, independent selection/statistics and source hashes.

With exactly the original one failure and no others, expect 34,776 output records,
34,686 actual model forwards (90 failed grid outcomes), 1,632 scorer attempts,
1,631 valid receipts and one 65,536-token maximum unknown charge. Additional
incidents reduce actual forwards/receipts and remain visible. The API cap stays $1,
cloud allowance $5 and cumulative ceiling $50. Reuse the same single L40S within
its original two-hour expiry; retain final results and delete all task resources.
