# Launch verification — 2026-09-24

Both full-task workers passed **606 offline tests** on their L40S hosts before
inference. The GPQA and short-task manifests were made from clean source revisions
`984a9a9` and `3863edf`; all transferred prompt/checkpoint file hashes matched and
reference files were absent on both workers. Each server has a verified active
independent expiry timer and bounded worker service.

Local reporting additions bring the suite to **609 passing tests in 11.50 seconds**.
Lint, formatting, guidance validation, build and diff hygiene pass. Current code
head `61789ff` passed all four Python 3.11/3.12 checks in
[push CI](https://github.com/OVRLab/jev-guided-decoding/actions/runs/35989557970)
and [PR CI](https://github.com/OVRLab/jev-guided-decoding/actions/runs/35989563184).
The new aggregate exporter first failed its three capability tests because the
module did not exist, then passed private-example exclusion, incomplete/invalid
score rejection, and duplicate/unclean/over-cap stage accounting checks.

While generation continues, independent checks passed for the first **166 GPQA**
and **144 short-task** native answers, plus their warmups and initial numerical
admission records. These checks validate exact tokens, prefixes, stopping and
source bindings; they do not consult reference answers or establish correctness.
As of 11:05 UTC, original Granite's 198 GPQA native answers and three repeat probes
are complete; self-refinement and the remaining systems continue. The short-task
worker is also active. No fresh quality grade is available yet.

Both backup/cleanup supervisors and the final audit watcher were detached from
this chat's command session without interrupting either model worker. Their new
processes and fresh backup status were verified. Task-scoped idle-sleep guards
follow the supervisors and end when those processes finish. Model execution and
VM shutdown are independent of this local watcher's availability.

Cloud authentication currently succeeds. Early renewal was not confirmed; the
original local cache was restored exactly and temporary credential copies removed.
If API authentication fails at cleanup, the supervisor schedules SSH shutdown;
resource deletion may then require normal reauthentication. Independent VM timers
remain active. Final deletion/cost evidence is **pending**, not asserted here.

The full PR review context has no human reviews or inline threads. The automated
reviewer is unavailable because its quota is exhausted, not because it approved
the change. The PR remains unmerged and no model/package release was published.

## Deadline-closure status verification — 25 September

Documentation-only update; no generation, protocol, grader or recovery source changed.
Fresh verification matched all 83 GPQA and 60 short-task files to saved remote
SHA-256 inventories, validated both recovery ancestry chains and all 528 Jev
receipts, and checked complete selected-answer coverage with the existing
selection helper. Both worker logs record admission-deadline timeouts; cleanup
receipts record deletion at 02:03:10 UTC. The cost reconciler yields $103.82976781335556
cumulative before tax/separate network. No fresh quality grade was inspected.
The initial system-Python audit import failed because the project package was
unavailable; rerunning the read-only check in the existing uv environment passed.
The complete-run finalizer remains review_required; no completion claim was forced.
Guidance links, aggregate consistency and diff checks are the validation for these
documentation changes. Fresh canonical checks also pass: 49-file guidance checker,
Ruff lint/format, all 634 tests and source/wheel builds. No model inference was rerun.
