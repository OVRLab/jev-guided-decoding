# R25: Jev-gated natural-draft repair

**Status: running on one Nebius L40S; no quality result yet.**

The owner increased the cumulative research cap to $75. R25 reserves $14.40 from
$38.22647 remaining before tax/network. One L40S/16vCPU/64GiB with an 80GiB disk
has an eight-hour poweroff timer; worker runtime is capped at seven hours.

- [Frozen plan](../../research/gated-repair-plan.md)
- [Source/data manifest](../../research/protocols/gated-repair-v1/manifest.json)
- [Data attribution](../../research/protocols/gated-repair-v1/NOTICE.md)
- [Prior art and limits](../../research/gated-repair-related-work.md)

Source commit `9246708`; data freeze commit `4197f8e`. A rank-64 residual branch
has 262,144 new trainable parameters after block 19. Jev's error probability
multiplicatively controls its strength during a second generation pass. Original
Granite and Jev weights stay frozen. The native draft and blind/text repair,
matched constant adapters and shuffled/inverted feedback are all retained.

The dataset has 384 training, 64 development and 192 fresh pilot evaluation cases
from GSM8K and ARC-Challenge. Two training seeds, two epochs, earliest best-dev
checkpoint selection, and independent final-answer grading are registered. These
two auxiliary tasks are not the project's full ten-benchmark scorecard.

All 516 local tests, 516 server tests and four current CI jobs pass. Cloud admission, training,
quality results, artifact replay, actual cost and verified deletion are pending.

Worker launched 2026-09-23 at approximately 19:14 UTC, after source/data freeze
and server tests. Automatic 45-second local backups and a separate cleanup
supervisor are active. Initial test temporary-file writes were slow on network
storage; the original complete suite passed in 159.20 seconds before any rerun,
so no test configuration or scientific source was changed.
