# R27 second interruption and bounded continuation

Registered 24 September 2026 before any second-continuation inference. At 20:05
UTC, the GPQA backup was stale, with 86 larger-Granite answers. The cloud operation
history confirms a stop at 16:24:30 UTC; the cause is not established. The supervisor
kept retrying backups but could not recover inference automatically. IFBench/AIME
remains active, with all original/guided/control cases complete and larger Granite
at 194/330. No fresh quality grades have been inspected. Cloud login was renewed
through the existing account's normal sign-in flow.

## Execution amendment and budget

Use the existing two single-L40S streams. Preserve all earlier raw folders,
receipts, source files and generation settings. Introduce a separately tested
chained-resume adapter around the unchanged v1 runner, with explicit ancestry and
source inventories; no architecture, output limit, seed, prompt or grade change.
Each continuation validates its parent before reusing durable outputs. A started
job without durable batch/output/finish may restart from the same case seed; its
original start is retained in the ancestry ledger. Unknown partial token work is
reported as unmeasured, never zero. No additional Jev call is allowed.

The earlier 11-hour elapsed-run limit could no longer finish the comparisons after
the interruptions. Reallocate the existing $110 authorization, without increasing
it: allow generation through **2026-09-25 02:00 UTC**, with independent VM shutdown
at **02:30 UTC**. A conservative cost bound charges both complete original-create-
to-shutdown wall-clock intervals, including all stopped periods, at
$1.8245808219178083 per stream-hour, adds the closed-stage $47.39595151031136 and
all $0.017775408 settled Jev charges, and must stay below $110. The [hash-bound admission](../reports/2026-09-24-full-benchmark-tranche/second-recovery-admission.json)
stores and recomputes this bound; no caller can silently extend its deadline.
This replaces the earlier per-stage $24 reserves with one bounded two-stream
allocation. It is an upper estimate under the already documented GPU rate,
before tax and separate network costs, not an invoice. No third GPU is admitted.

Restart GPQA and recover its disk before resuming. Keep the active short-task worker
running; launch its continuation only if its existing worker exits incomplete.
If it completes, retain that complete output and do not rerun it. No cleanup may
race with a planned continuation. Restore a single owner for each supervisor,
monitor stale status explicitly, and verify backups before deleting owned disks.

## Verification and reporting

Test first: complete-output reuse across two interruptions; unchanged ancestor
bytes; duplicate/corrupt journals; altered ancestry; missing source binding;
expired or over-budget admission; zero provider replay; and completed-parent
refusal. Test the actual private supervisor transition without GPU/cloud actions.
Run canonical checks, hash-verify additive code on each GPU worker, validate
numerical/token provenance and verify real output growth after launch.

The finalizer checks every lineage step before the original complete-run auditor.
Never turn missing comparator outputs into a completed benchmark. Update the
research register, report, manuscript and PR with the interruption and amendment.
A complete top-ten comparison and a positive result remain unestablished.
