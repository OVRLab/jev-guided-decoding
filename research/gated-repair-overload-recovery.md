# R25 v4: bounded delivery after explicit overload

Drafted 2026-09-23 while v3 collected training drafts, then finalized after its
HTTP 503 stop and verified deletion. No optimizer, development selection or test
generation occurred. V3 kept its fixed failure limit and unchanged source; every
byte is archived before this separately versioned continuation.
Do not rerun a completed model job or any legacy API request. Legacy unavailable
feedback remains unavailable, with the previously declared neutral gate.

## Diagnosis and changed delivery

V3 received repeated explicit HTTP 529 responses interspersed with successful
receipts, then stopped on HTTP 503 after 165 drafts and 157 valid receipts. A
one-shot local probe also succeeded. The vendor documents 529 as
temporary overload and recommends backoff; HTTP 503 is an explicit service-unavailable
response, also eligible for bounded retry here with full unknown-charge accounting.
Dropping every explicitly rejected
request immediately is unnecessarily brittle for this run. This amendment changes
transport delivery for **never-started cases**, not architecture, targets, examples,
seeds, optimizer, checkpoint selection, generation caps, metrics or test controls.

For a new case allow at most four attempts, retrying only an explicit HTTP 429/503/529.
Each attempt gets its own durable maximum-input reservation before dispatch and
its own request/response/error record. Unknown usage retains the entire 65,536-token
charge, even on explicit overload. Cooldowns are at least 30, 60 and 120 seconds,
respect Retry-After, and never exceed 300 seconds. Pace new cases by at least two
seconds between completed delivery and a new request. This is actual additional
waiting, not hidden inference or a quality-selected retry.

A timeout/transport failure is never retried; retain its charge and mark that
case missing. Authentication, schema, model/version, budget, input-integrity or
other unexpected failure stops. Exhausted explicit-overload attempts produce one
missing-feedback case; at most 16 missing cases including all legacy failures and
64 total unknown-charge attempts across all versions are admitted. The original
copied $0.25 API cap remains binding and may stop sooner. No extra API budget or
reset is introduced. Preserve null actual scores separately from neutral effective
0.5, and retain every planned case in grading.

## Durable reuse, audit and resource bounds

A new manifest binds the complete stopped pre-training v3 snapshot and original
v2 snapshot. Validate legacy prompt/token/request/receipt/model/charge bindings,
complete native jobs, frozen data/source and original backbone digest. Copy native
outputs/jobs and the budget prefix byte exactly. Preserve original API evidence
unchanged; put new per-attempt dispatch/receipt/failure evidence in separate files.
Reconstruct one availability record per case from actual legacy/new receipts or
explicitly missing outcomes. Record which inputs were reused and never dispatch
them again. Training and all later generation routines remain inherited unchanged.

The primary auditor must verify every physical attempt, every retained unknown
charge, successful receipt, unavailable case, final token, gate, checkpoint and
selection order. It must not mistake retried overloads for multiple independent
cases or count unavailable feedback as Jev. Primary repair and the predeclared
retention replay remain separate. Freeze the v4 retention manifest before test.

Keep the $75 cumulative cap and $20 combined R25 reservation. After v3 deletion,
recompute actual remaining stage headroom before any replacement GPU. Use at most
one L40S, nine-hour worker/ten-hour machine limits, backups and verified deletion;
reduce the machine limit if the remaining $20 cannot cover it. No H200 or automatic
extension. Do not provision before local capability tests, source/data freeze and
accounting admit the new run.

## Verification plan

Tests first: explicit overload succeeds on a later independently reserved attempt;
unknown charges retained; no replay on ambiguous timeout; legacy failed inputs
never redispatched; fatal authentication/schema stop; cooldown/attempt/incident
and monetary caps; incomplete/duplicate request or generation refusal; source and
snapshot tamper detection; merged availability retains all cases. Run canonical
checks. Before new quality work require the unchanged real-model FP32 admission.
Independent raw-artifact audit and public replay remain necessary for any result.

Source: https://docs.typesafe.ai/api (Errors and Handling rate limits, checked
2026-09-23). A 529 is evidence of that response, not proof of system-wide outage.

## Post-deletion budget admission

V3 and all its owned resources were deleted at local 20:27:46 UTC. Estimated
cumulative use is $38.33374990195374 before tax/network; combined R25 use is
$1.560214979933174 including the separately logged local availability probe.
Prior R25 use + ten GPU/disk hours at $1.7545808219178083/h + the entire $0.25
API allowance is $19.356024, below the $20 stage reserve. This conservatively
includes already charged API usage twice in the admission bound. Thus the
nine-hour worker/ten-hour VM limits remain affordable without a cap increase.
