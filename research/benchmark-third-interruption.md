# R27 third GPQA interruption — bounded continuation

Registered 24 September 2026 at 22:49 UTC before third-continuation inference.
The GPQA VM stopped at 22:14:13–22:14:33 UTC, after saving 128/198 larger-Granite
answers. The cloud history confirms the stop but does not state its cause.
IFBench/AIME remains active at 286/330 larger-Granite answers; its scheduled
v1-to-v2 handoff succeeded. All original/guided/control outputs and 528 Jev calls
remain complete; Qwen and fresh quality grading are pending.

## Recovery plan

Restart the same owned GPQA VM and preserve its existing disk. Reuse the already
tested, unchanged [v2 recovery runner](iterations/benchmark_recovery_v2/run.py),
passing the original, v1 and v2 raw directories as explicit ancestors and writing
a new v3 directory. Verify hashes, journal consistency and source bindings before
inference. Retain the interrupted job and unknown partial work in the ancestry
ledger. No new Jev call or changed model, seed, prompt, checkpoint or grade.

Extend private control/reporting path selection to this explicit third output;
test that it retains all ancestors, refuses unowned paths and verifies current and
retired network allocations. Replace only the GPQA monitor and completion watcher;
leave the active short-task GPU service and its monitor running. Do not allow
cleanup while recovery is being installed. Verify new output growth after dispatch.

The [existing global admission](../reports/2026-09-24-full-benchmark-tranche/second-recovery-admission.json)
remains unchanged: generation ends 25 September at 02:00 UTC; independent VM
shutdown is at 02:30 UTC. Conservative cumulative bound remains $105.46/$110,
before tax/separate network. No additional GPU, deadline extension or budget
increase. Completion of the remaining comparators is not guaranteed.

The replacement is preemptible. Nebius documents that such VMs can stop at any
time, retain disks but lose dynamic IPs, and cannot be converted in place to a
regular VM ([provider documentation](https://docs.nebius.com/compute/virtual-machines/preemptible)).
This explains why interrupted recovery must preserve disks and track address
changes; it does not establish the cause of this particular stop.

Update the report/register/manuscript with the interruption, exact recovered
counts, checks and resulting status. Missing comparators remain missing; no full
benchmark score is asserted from partial generation.
