# Execution plan: local critic and bounded logit guidance

2026-09-21. The owner authorized carrying the reassessment through implementation
and evaluation. This plan operationalizes [R12](../research/next-experiment.md);
results are not known when written. Existing $50 total authorization remains.

1. Implement the bounded sparse-bias calculation and capability/negative tests
   first, keeping the core import independent of Torch.
2. Create fresh authored rule worlds, a strict full-claim parser and independent
   forward-closure oracle. Declare unparseable prose unassessed, not false. Include
   generated candidate batches and separate authored contrast diagnostics.
3. Freeze the Gate A program/data/rubric before live inference: 60 development
   worlds, then 100 separate gate worlds, three Granite proposals per world.
   Judge local claims using Jev; retain every proposal and exact model token path.
4. Evaluate candidate availability, grader coverage, critic discrimination,
   calibration and selection versus likelihood. A second development-only rubric
   is allowed only as a separately recorded version before opening gate outcomes.
5. Build and mechanically check an explicit token-selection backend/controller
   with isolated lookaheads, zero-bias/shuffled controls and unchanged final-answer
   ownership. An independent mechanism check is not a quality claim and does not
   bypass the critic gate. No expensive Gate C study is admitted if Gate A fails.
6. If the gates pass, freeze and execute a new final-answer comparison with the
   controls in R12. Otherwise record the failed/inconclusive admission, retain
   usable implementation and diagnostics, and do not invent a positive result.

Files: new core bias/scorer modules, optional inference backend, focused tests,
new research experiment scripts and authored data, dated reports, register and
current navigation/status. Historical runners/results remain preserved. Any source
change needed for a live study is committed before that study begins.

Failure cases: no valid/mixed-quality candidate opportunities, unassessed generated
prose, absent labels in original evidence, all-good/all-bad sets, confidence mistaken
for correctness, ineffective zero bias, RNG contamination, stale scores, mutable
branch state, wrong token provenance, all-rejected early-final collapse, context/time/
token exhaustion, unavailable credentials, malformed provider output and unknown
paid usage. No scorer failure may silently become a successful baseline trial.

Verification: observe new tests fail before implementation; exercise the complete
offline flows; exact model check with a bounded real run; independent oracle
counterexamples; aggregate reconciliation and hashes; canonical lint/format/tests/
guidance/build; PR review and current CI. All live attempts and development changes
get reports, including gate failures. Cloud launch, if useful, follows code readiness
with a hard timer, conservative shared spending record and verified cleanup.

## Execution outcome

The [dated report](../reports/2026-09-21-logit-guidance/README.md) records completed
V1 development, provider-interrupted V2 scoring, all 53 unpaid proposal-completion
jobs and the four-prefix real-model mechanism check. The sparse bias, token backend,
bound-score selector and asynchronous live checkpoint function are implemented.
Fresh hosted checkpoint execution is unverified after the paid stop; the real-model
check replays already received judgments. Final framing failed in all 20 mechanical
continuations, although token ownership and no-op/probability invariants passed.
No held-out gate or Gate C was admitted. Broader authored diagnostics and ablations
remain unexecuted under this stopped protocol, not quietly replaced by pilot results.
