# R25: Jev-gated natural-draft repair

**Status: v1 failed numerical admission; v2 passed FP32 checks then was interrupted; v3 continuation frozen before training/test.**

The owner increased the cumulative research cap to **$75**. R25 now reserves
**$20 combined across all attempts**. Estimated cumulative use before v3 is
**$37.690485** before tax/network. V3 uses one L40S/16vCPU/64GiB with an 80GiB
disk, ten-hour poweroff and nine-hour worker limit. V1 limits below are historical.

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

V1 passed 516 local/server tests before failing numerical admission. V2 passed
518 server tests and real-model FP32 admission. V3 passes 527 local tests; its
server validation, training, quality evaluation and cleanup remain pending.

V1 launched 2026-09-23 at approximately 19:14 UTC, after source/data freeze
and server tests, with 45-second local backups and a separate cleanup supervisor. Initial test temporary-file writes were slow on network
storage; the original complete suite passed in 159.20 seconds before any rerun,
so no test configuration or scientific source was changed.

## Preserved failure and full-precision restart

The [v1 attempt](failed-v1/README.md) stopped before any training draft, Jev call
or optimizer update: BF16 cached/full logit discrepancy was 0.25, above the fixed
0.125 limit. All five artifacts are preserved and owned cloud resources deleted.
Estimated cost $0.293387; cumulative $37.066922 before tax/network.

The [registered v2 amendment](../../research/gated-repair-fp32-amendment.md) keeps
identical data, architecture, seeds and controls, but uses float32 for every arm,
strict 1e-4 cache checks and a separate native/intervened precision diagnostic.
The combined R25 reservation is now $20 within the cumulative $75 cap, allowing
for slower full-precision work. V1's original $14.40 limit above is historical.
The [v2 manifest](../../research/protocols/gated-repair-fp32-v2/manifest.json)
preserves every predecessor data hash. All 518 local tests pass. No quality
measurement or Jev contribution has yet been established by R25.

## Precision diagnostic completed

The [six native/intervened comparisons](precision-diagnostic/summary.json) pass
in float32: maximum absolute discrepancy is 0.0000267029, and all next-token
argmax choices agree. BF16 native discrepancies are 0.25, 0.2890625 and 0.3125;
BF16 intervened discrepancies are 0.25 on each fixture, with identical argmax
choices in all six comparisons. Thus the earlier discrepancy also occurs without
the intervention; it does not establish an adapter-specific cache error. These
three training fixtures do not certify numerical equality for every sequence.

V2 passed its own strict admission (max discrepancy 0.0000211000), then produced
113 training drafts and 112 successful Jev receipts before request 113 failed.
The exact HTTP status was not persisted and is not asserted. No optimizer,
development selection or held-out generation ran. [All records](interrupted-v2/README.md)
are preserved; all owned resources were deleted after verifying 20 final files.
Known usage was 70,834 input tokens, plus a 65,536-token unknown-charge reservation.
Cloud estimate $0.617835, conservative API $0.005728; cumulative $37.690485.

## Frozen continuation v3

[Source/data manifest](../../research/protocols/gated-repair-continuation-v3/manifest.json),
[prospective amendment](../../research/gated-repair-continuation.md), source
`10c968a`, data freeze `05d130b`. All 113 drafts and 112 valid receipts are reused
byte exactly, with no repeated provider request or completed model job. Missing
feedback remains null; a neutral effective value 0.5 is explicitly labeled and
is never counted as a Jev response. Every case remains in primary evaluation.
At most eight transient incidents are admitted including the historical failure;
authentication, schema, integrity, unexpected errors or excess incidents stop.
The copied API ledger retains its original $0.25 cap and all previous charges.

The [retention replay](../../research/gated-repair-retention-supplement.md) was
registered before any test and keeps native answers when valid Jev p(correct)
is at least 0.5; the v3 addition keeps native when feedback is missing. This is
an offline policy analysis, not measured avoided computation or API calls.

See the [mechanism and token ownership](method.md). Quality is still unmeasured;
no scientific settings were changed in response to held-out answer quality.

The [v3 retention registration](../../research/protocols/gated-repair-retention-continuation-v3.json)
prospectively binds the replay to the continuation manifest. It preserves and
hash-links the original registration, threshold, and missing-feedback policy;
no test or training has run on v3 at this point. The original v1 registration
binds v2 and therefore cannot serve directly as the v3 audit input.

V3 launched at approximately 20:11 UTC after all **527 server tests passed in
18.45 seconds**. The GPU's independent expiry timer is active. Local backup and
cleanup supervision run every 45 seconds. New report-only recovery/damage tests
bring the local suite to 529; the frozen worker remains unchanged.
