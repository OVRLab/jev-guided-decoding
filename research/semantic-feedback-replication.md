# R21B: fixed replication after insufficient natural error exposure

Registered 2026-09-23 after R21A completed, before replication inference. R21A
judged 384 constructed claims and 192 Granite drafts without an error, including
all 12 incorrect drafts. Its registered admission failed solely because it required
20 naturally incorrect drafts. Preserve `admitted=false`; do not lower that threshold
or describe a 12/12 observation as certain error detection.

Run one fixed fresh cohort of **384 worlds**, 64 per original motif, with the same
templates, greedy FP32 Granite revision, 24-token cap, Jev questions and scoring.
Use independently seeded new worlds (`210923073`), exclude prior entity/world
identities, and register data/source hashes before inference. No enrichment based
on which R21A motif failed, no extra rounds until a desired result, and no changes
to the original frozen code. The replication adapter invokes the frozen runner
with a new manifest verifier; the original manifest remains valid.

Apply the original admission rules to this replication **alone**, including at
least 20 supported/20 unsupported assessed natural drafts, 85% natural balanced
accuracy, 90% constructed balanced accuracy and 75% per motif. This is an adaptive
engineering replication motivated by R21A, not a pristine first confirmatory test
or a population error-rate guarantee. If it passes, proceed to the separately
registered learned-bridge pilot; if not, stop this training direction and report.

Record all attempted tokens and calls, retain incomplete/failed attempts, and
reconstruct source/data/prompt/token/receipt/weight/budget identities with the same
audit. No cloud resources are needed for this local MPS stage. Budget at most $0.50
additional Jev; prior estimate now **$32.56217300454077/$50**. Expected actual API
cost is much smaller. The remaining conditional compute allowance stays $10.

The overall architecture motivation and limitations remain in the
[R21 plan](semantic-feedback-plan.md). No final-answer improvement has been measured.
