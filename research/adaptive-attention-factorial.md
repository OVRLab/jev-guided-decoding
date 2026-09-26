# R16 supplementary factorial controls

Registered 2026-09-22 after development selection and after the main test started,
before consulting any held-out aggregate accuracy or F1. This is an exploratory
supplement, not a retroactive primary comparison or a change to the main schedule.
The owner asked to explore all three directions and preserve useful controls.

Development selected eleven heads at strength 5, disabling zero-based head
(layer 21, head 13), with strict relevance >0.65. This differs from R15 in three
factors. The primary tuned-versus-R15 comparison therefore tests the combined
policy; it cannot isolate individual-head tuning from strength and threshold.

Evaluate the full 2×2×2 factor combination on the existing 600 constrained contexts:
strength ln(16) or 5, all twelve heads or head (21,13) disabled, threshold .5 or .65.
The R15 and tuned corners already exist in the main study. Run only the six missing
corners, for 3,600 new single-token forwards; never replay the two existing corners.
Use the identical FP32 runtime, prompt tokens, source-score receipts and checkpoints.
The supplement has no API client or credential: a read-only receipt replay store
must reject unknown payloads and preserve existing failed receipts as failed.

This is reuse of exposed test contexts for diagnostic comparison, not an independent
replication or a new tuning set. No policy changes follow these results. Report
conditional contrasts and averaged factor effects with exploratory 95% paired
world-bootstrap intervals; interactions make one-factor changes non-additive.
Report the original primary contrasts and complete main schedule regardless of
this supplement's outcome. No all-controls success requirement is introduced.

Freeze this supplement's source and configuration before its inference. Require
main completion and the exact selected policy. A separate journal/output records
all 3,600 planned outcomes. Keep failed/started outcomes in denominators and do not
replay interrupted jobs. Stop at twenty minutes, within the same VM's original
8-hour expiry and the same $15 cloud allowance; no new server or extra API budget.
Independently verify source receipts, prompt digests, tokens, grades and schedule
against the main artifacts; cost includes this extra GPU time.
