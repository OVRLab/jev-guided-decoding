# R27 full-benchmark tranche — second recovery active

**No full-task quality result is available yet.** GPQA Diamond, IFBench and AIME 2026 were dispatched on
2026-09-24 after the audited exposed-only pilot passed. The immutable source
revision is `984a9a9bbc3d33809c47efc5336fd96a47f5df46`; its private manifest SHA-256
is `078dd7e7a95337077adff6878ae696e64186fa36af9dc6b7729f84360b0a7947`.
The [public manifest](gpqa-manifest.json) contains hashes and settings, with no
question/answer text. All 606 offline tests also passed on the GPU worker.

| Task | Planned source / untouched | State |
| --- | ---: | --- |
| GPQA Diamond | 198 / 196 | Resumed: original/guided/controls complete; larger Granite in progress, Qwen pending |
| IFBench | 300 / 288 | Original/guided/controls complete; larger Granite in progress, Qwen pending |
| AIME 2026 | 30 / 30 | Original/guided/controls complete; larger Granite in progress, Qwen pending |
| Other seven contracted tasks | See ten-task contract | Full comparisons not completed |

[GPQA protocol](../../research/gpqa-diamond-execution-v1.md),
[IFBench/AIME protocol](../../research/full-short-execution-v1.md),
[ten-task contract](../../research/benchmark-suite-contract-v1.md).
Compare the frozen internal repair architecture with original Granite, Jev-free
self-refinement, matched routed controls, Granite 4.2-3B and Qwen3-4B. Preserve
exact output tokens and all real compute/API work; no fresh grades select the
architecture, checkpoints, threshold, prompts or task order.

The previous [pilot](../2026-09-24-benchmark-execution-pilot/README.md) tied original
Granite on its 18 exposed cases. It is an engineering result, not a fresh benchmark
score. Cumulative closed-stage cost is $47.40; GPQA and the running short-task
stage each reserve $24, totaling $95.40 including prior spend. The $110 cap remains.
Each stage has an independent 12-hour VM shutdown, regular private backups and
owned-resource cleanup. Active compute is additional to the closed-stage estimate.

GPQA and AIME question/answer-bearing traces remain private. Publish hashes,
aggregate measurements and audit evidence after generation and independent grading.
This tranche cannot establish the full ten-benchmark north star by itself.

The combined IFBench/AIME manifest was frozen at clean source
`3863edfd6d9d3bc2b581c26f533b222ed83b8bef`, SHA-256
`46fa4011cf34f25a36cae2eb904fe447efa2f140dc6338723973885349bf9c24`;
[settings and hashes](short-manifest.json). Its worker also passed all 606 offline
tests; transferred prompt-only inputs and checkpoints matched local hashes and
references remained local. Both worker services and independent expiry timers
were confirmed active. Initial SSH attempts during boot were retried before any
inference; no failed model/API attempt was silently repeated.

A local completion watcher waits for complete generation and verified cloud
cleanup, then runs the frozen v3 auditor with exact-token verification, checks
IFBench evaluator/environment hashes, exports aggregates without private examples,
and reconciles both stage costs once. It generates a local Markdown draft for
review; it does not create missing benchmark results, alter grading or claim an
unreviewed draft has been published. Operational errors stop this reporting path
and preserve partial artifacts for inspection.

## Interruption and recovery

Both VMs stopped around 13:23 UTC on 24 September. Backup supervisors reported
connection failures and stopped after their retry limit; the completion watcher
correctly refused to publish incomplete results. The owner resolved the account
issue and authorized resumption. Two restarts returned `NotEnoughResources`.
Replacement single-L40S instances are being allocated with the original disks;
no model has resumed yet at this documentation checkpoint.

The last local backups contain 1,463 GPQA and 1,215 IFBench/AIME outputs, including
warmups/probes and controls; these are not numbers of benchmark questions. All
528 Jev receipts validate against their exact drafts and settled charges, with no
provider failure or retry. One unfinished model job per stage is explicit. The
[recovery protocol](../../research/benchmark-interruption-recovery-v1.md) preserves
the interrupted raw folders and creates hash-bound continuations, reusing every
completed output and all Jev judgments. No fresh grades have been inspected.
Ten new tests first failed because recovery was absent, then passed; the complete
local suite passes 619 tests, plus lint, formatting, guidance checks and build.
The original per-stage deadlines, reserves and cumulative $110 cap remain.

### Resumption verified at 14:15 UTC

Both replacement L40S servers are running. GPQA resumed its larger Granite native
stage from 30 completed questions; IFBench/AIME is producing new repair/control
outputs. GPU activity and new job timestamps were checked directly. Full remote
retrieval recovered 17 additional durable IFBench/AIME outputs, bringing its parent
to 1,232; GPQA's parent remains 1,463. All original result files matched remote
hashes (16 GPQA files, 14 short-task files). Both derived runs pass exact parent
preservation checks; each records one interrupted job. No new Jev request occurred.

Recovery source `7334521` passed all four CI jobs and 619 local tests; both frozen
remote environments passed 616 tests. The resumed original-model cache admission
also passes. The GPU stays L40S; the CPU platform changed from AMD to Intel and the
replacement instances are preemptible. Their original absolute worker deadlines
are 21:34:54 and 21:44:20 UTC, with independent VM shutdown at 22:31:19 and
22:39:49 UTC. These limits do not guarantee completion of the remaining work.

Detached supervisors back up every 45 seconds plus transfer time, retain stale
status on connection failures, and retry; the actual supervisor scripts passed an
offline transport-failure/recovery check. A restarted completion watcher verifies
recovery lineage before the unchanged full-coverage/token/grade audit. Cleanup
includes both original and replacement instances and the preserved disk, only
after hash-verified retrieval. No full-task quality score is available yet.

The attempted L40S bid policy was rejected by the provider; no policy was created.
The replacement uses spot pricing, with a conservative regular-price estimate over
the entire original-to-cleanup wall time, including downtime. The existing two
$24 reserves and cumulative $110 cap remain; final billing may be lower. Cloud
authentication renewal may be needed for final API cleanup; an independent VM
shutdown and SSH shutdown fallback still bound running compute if it is unavailable.

## Second interruption and new bounded admission — 20:05 UTC

GPQA stopped at 16:24 UTC; the cloud operation confirms the stop, but not its
cause. After restart, its service is inactive, with 86/198 larger-Granite native
outputs saved. IFBench/AIME stays active, reaching 201/330 larger-Granite outputs
at 20:16 UTC. All original/guided/control generations and all 528 Jev requests
are complete; no additional Jev request is needed or permitted. No fresh quality
grade was inspected.

The [second recovery protocol](../../research/benchmark-interruption-recovery-v2.md)
adds a chained state adapter around the unchanged worker, keeps the active short
worker running, and resumes it only if it exits incomplete. Earlier source/parent
files stay unchanged. The [new admission](second-recovery-admission.json) replaces
the two per-stage $24 reserves: generation through 02:00 UTC, VM shutdown by
02:30 UTC on 25 September. The conservative cumulative bound is **$105.46/$110**,
including stopped time at the regular GPU rate, before tax/separate network.
This does not guarantee that all comparators will finish.

Fifteen new offline tests cover chained preservation, budget refusal, wrapper
source inventories, active-worker handoff and false completion. State/handoff
tests first failed because the implementation was absent, then passed. All
**634 local tests**, lint/format, guidance checks and build pass. Actual private
monitor/finalizer checks also reject false progress and changed source inventories.
Dispatch of the new continuation remains pending at this checkpoint.

### Second resumption verified — 20:32 UTC

Both cloud instances are running, both GPUs are active, and the new GPQA native
job started at 20:30:20 UTC after reloading the unchanged larger-Granite weights.
Its 86 completed larger-model answers were preserved; the interrupted case is
being regenerated from its original seed. IFBench/AIME continued without a model
restart and reached 209/330 larger-Granite outputs. Qwen has not started.
[Status snapshot](second-recovery-status.json) contains aggregate execution state.

Both independent shutdown timers now point to 02:30 UTC on 25 September. The
short-task controller waits for its original service to stop, then either accepts
a complete run or starts the admitted continuation. Two local backup monitors
and the final audit watcher are alive; GPQA's two-hop ancestry and the short
worker's first-hop ancestry pass preservation checks. No Jev request was repeated.
Source `680bab3` passed all four CI jobs and **631 tests on each frozen remote
environment**, alongside the **634 local tests**. Runtime/hardware/weight bindings
pass on the resumed model. The new network allocations assigned during restart
are included in cleanup verification along with retired allocations; this path
also passed an offline regression. No model service was restarted for that fix.

The finalizer checks every ancestry/source envelope and complete coverage before
the unchanged v3 audit. Monitoring and cleanup use the new global admission;
earlier 11-hour/$24-per-stage limits above describe the superseded first attempt.
No full-task accuracy result is available yet.

Output growth confirmed at 20:35 UTC: GPQA saved its first new answer at
20:33:08, reaching 87/198 larger-Granite outputs; IFBench/AIME remains active
at 209/330. Both backup monitors and the final audit watcher are alive. No fresh
quality grade has been inspected.
