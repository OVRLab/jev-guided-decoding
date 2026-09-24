# R27-A verification record

All 132 outputs and serial work records pass source/data/checkpoint, exact-token,
cache, hook-position/gate, base-weight, API-delivery and charge checks. All 19
compressed inference files reproduce the analysis identically after extraction.
Twenty-one remote files matched local hashes before deletion; all owned resources
are absent. The $5 cap was respected.

The first whole-run audit failed because it reused R26's eight-probe order check
although the R27 worker registers three probes on original Granite only. A new
regression reproduced the unsupported probe-count interface, then passed after
the separate R27 auditor was corrected. Worker sources, frozen cases and all raw
outputs stayed unchanged; no paid inference was repeated. The corrected auditor
also requires exact native-repeat tokens and a Jev-free baseline completed before
the first provider request.

The full PR scope was reviewed against actual base `feat/initial-controller`
(`4c43f489d7bbdcb2bbd464edcaba7505539d1e08`); earlier unchanged artifacts retain
their prior hash/replay checks. New review covers terminal stopping outside
thinking, whole reference separation, serial work accounting, unchanged model
profiles, all controls, source-level exposure, budgets, backup and cleanup.
No human review is recorded. The automated reviewer is unavailable because its
quota is exhausted; this is not approval. No merge or model release was performed.
