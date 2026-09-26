# R25 prospective retention-policy replay supplement

Registered 2026-09-23 while v2 collects training drafts, before adapter training,
checkpoint selection or any test draft/API/output. The original primary study,
source/data hashes, live inference and all planned denominators remain unchanged.
This adds an explicitly labeled **offline policy replay**, not another paid run.

## Reason and fixed policy

An internal gate of zero preserves the *blind repair pass*, not necessarily the
original native draft. Asking the model to reconsider an already correct answer
can itself cause damage. Test the fixed R24 decision threshold as a repair gate:

    if Jev probability(native final answer correct) >= 0.5:
        retain the native Granite token sequence exactly
    else:
        use the registered repair arm's Granite token sequence exactly

No threshold sweep or test-outcome selection. Apply the identical routing decision
to live, constant, blind and text-feedback repair arms, retaining both training
seeds and their per-problem mean. Routing receives only probabilities and case IDs;
references are used afterward for independent grading, never for branch choice.
Report retained wrong answers as well as avoided damage; a high Jev score does
not certify correctness. Do not call the retained answer a Jev-generated answer.

## Comparisons and limits

Show accuracy, recovered native errors, damaged native successes, percentage of
cases sent to repair, and paired per-domain differences against native and against
identically routed blind/constant repair. The main full-repair comparisons remain
primary; a replay gain cannot retroactively turn a failed primary endpoint into a
success. All native, repair and Jev computations actually executed by R25 continue
to count in cost and timing. Replayed routing does not establish measured latency,
actual skipped repair execution, avoided Jev calls or deployed throughput. Jev is
still called on every case; selective *Jev dispatch* is a separate future study.

A promising replay would motivate fresh prospective execution of the conditional
architecture. It would not by itself establish a new LLM architecture, larger-model
outperformance, full-suite generalization or a performance release.

Implementation: independent `research/diagnostics/gated_repair_retention.py`, tests
that high-confidence wrong answers are retained and low-confidence correct answers
can be damaged (prevent reference-dependent routing), and source/manifest digests
saved in the supplemental result. Freeze this supplement in Git before test starts.
