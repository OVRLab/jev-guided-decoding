# R27 interruption recovery, 24 September 2026

The two frozen full-task workers stopped unexpectedly around 13:23 UTC. At
13:44 UTC both cloud instances were independently confirmed STOPPED and local
supervisors had exited after three failed backups. The owner identified a payment
issue, reported it fixed, and explicitly requested restarting and continuing.
Restart requests were accepted at 13:49 UTC. No fresh task grades were inspected.

## Prospective recovery plan

1. Recover the same owned disks, hash-verify their artifacts, and preserve the
   interrupted attempts unchanged; never delete a disk before verified retrieval.
2. Add a separately versioned recovery worker and tests, leaving the source-bound
   original runtime, manifests, prompts, seeds, weights and evaluator untouched.
   Completed output records are reused exactly; only a started job without a
   durable batch/output/finish may be retried from its original per-case seed.
   Keep its original start record in an interruption ledger and disclose lost work.
   Partial/corrupt output or ambiguous completed work must fail closed.
3. Require complete audited Jev receipts and settled budgets before continuation;
   reuse all scores and make no new Jev request. Validate regenerated decisions
   against saved decisions, preserve completed model weight certificates, and
   compare newly loaded hardware/model files and weight digests with prior records.
4. Write continuation into a new derived directory with a hash-bound parent and
   recovery source inventory. Preserve original timings; separately record restart,
   model loading, downtime and interrupted work. Do not call these uninterrupted
   end-to-end latency measurements.
5. Keep the original absolute deadlines and the two existing $24 stage reserves
   within the $110 cumulative cap. Reboot must not reset the independent cloud
   shutdown deadline. Restore durable backup/status supervision and final auditing;
   report interrupted or timed-out tasks as incomplete.
6. Before dispatch, observe test failures for missing recovery, then cover replay
   avoidance, incomplete jobs, duplicate/corrupt records, missing feedback, changed
   weights/inputs, expired deadlines, and reference-free operation. Run canonical
   checks. After dispatch verify live output growth and offline token integrity;
   publish only safe aggregate results after the complete independent audit.

Affected paths: this plan, a new research recovery module/worker, offline tests,
private cloud supervision scripts, status/research/register/paper documentation.
No architecture tuning, evaluation change, new API call or additional budget.

## Capacity fallback, before new inference

Both ordinary L40S restart operations returned `NotEnoughResources`. The live
capacity advisor offered Intel-hosted L40S preemptible capacity while the original
AMD-hosted L40S pool had none. Use at most two replacement single-L40S VMs, with a
provider-enforced maximum GPU price of $1.82/hour, unchanged original absolute
shutdown deadlines and unchanged $24-per-stage reserves. Mount the original
owned boot disks only after confirming their original VMs STOPPED; keep originals
until artifacts are hash-verified. Record the CPU/platform change and resumed
cold-loading timing separately. GPU model, model files, precision, runtime and
sampling stay unchanged and are checked before dispatch. Preemption is another
explicit interrupted outcome, never automatic permission to rerun paid requests.
Provider pricing/capacity references: [spot policies](https://docs.nebius.com/signup-billing/manage-pricing-policy),
[capacity advisor](https://docs.nebius.com/compute/virtual-machines/capacity-advisor),
[pricing](https://nebius.com/prices). A task-local current CLI is used; the owner's
existing installed CLI and authentication configuration are preserved.

The requested L40S pricing policy was rejected because this platform is not yet
supported by the pricing-policy endpoint (only H100/H200 pairs were listed).
No policy was created. The fallback is admitted only under a conservative $1.82
GPU-hour reserve, the listed regular price for the 16-vCPU Intel L40S. The provider's
[spot pricing documentation](https://docs.nebius.com/signup-billing/pricing-policy)
states that its spot-price upper range is below regular pricing. This is a reserved
cost ceiling based on provider terms, not a successfully configured bid policy.
The fixed absolute shutdown bound remains mandatory; retain actual billing records.
