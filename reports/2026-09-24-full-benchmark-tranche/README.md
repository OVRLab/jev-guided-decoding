# R27 full-benchmark tranche — running

**No full-task quality result is available yet.** GPQA Diamond was dispatched on
2026-09-24 after the audited exposed-only pilot passed. The immutable source
revision is `984a9a9bbc3d33809c47efc5336fd96a47f5df46`; its private manifest SHA-256
is `078dd7e7a95337077adff6878ae696e64186fa36af9dc6b7729f84360b0a7947`.
The [public manifest](gpqa-manifest.json) contains hashes and settings, with no
question/answer text. All 606 offline tests also passed on the GPU worker.

| Task | Planned source / untouched | State |
| --- | ---: | --- |
| GPQA Diamond | 198 / 196 | Running on one L40S; local references were not transferred |
| IFBench | 300 / 288 | Final freeze/dispatch pending |
| AIME 2026 | 30 / 30 | Final freeze/dispatch pending |
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
score. Cumulative closed-stage cost is $47.40; GPQA and the proposed short-task
stage each reserve $24, totaling $95.40 including prior spend. The $110 cap remains.
Each stage has an independent 12-hour VM shutdown, regular private backups and
owned-resource cleanup. Active compute is additional to the closed-stage estimate.

GPQA and AIME question/answer-bearing traces remain private. Publish hashes,
aggregate measurements and audit evidence after generation and independent grading.
This tranche cannot establish the full ten-benchmark north star by itself.
