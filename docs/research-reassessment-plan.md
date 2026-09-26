# Research reassessment plan — 2026-09-21

The owner requested a fresh assessment of where Jev should influence Granite,
and a durable Markdown record suitable for developing a public research paper.
The goal is a defensible integration hypothesis, not a promised positive result.

1. Audit the pinned checkpoint, its actual forward path, Jev's documented
   interface, and relevant primary research before choosing an insertion point.
2. Register every previous experiment, including failed pilots, the mistaken
   final-classifier comparison, the corrected study, and their limitations.
3. Add a reproducible offline analysis of existing traces. Distinguish rejection
   by the controller/scorer from invalid proposals and EOS. Aggregate results
   without publishing external dataset text. Write meaningful counterexample
   tests before the analyzer; retain the observed initial failure.
4. Specify the proposed runtime hook, its mathematics, cache and budget contract,
   ablations, and the evidence required before a new quality claim. Keep an
   actual hidden-layer integration separate from output-logit intervention.
5. Add a research index, study register, architecture review, diagnostic report,
   next-study protocol, related work, and an evidence-grounded paper outline.
   Link them from current project status without rewriting historical reports.

Affected paths: `research/`, a new dated aggregate report, focused analyzer tests,
this plan, and the root navigation/status/guidance files. Existing `src/` and
frozen experiment runners remain unchanged. No paid GPU run is needed to audit
the current evidence. A future experiment must use a new development split and
a fresh test freeze; the already inspected test set cannot serve as a new holdout.

Failure modes: confusing model-family class names with instantiated layer types;
calling Jev's judgment probability a calibrated probability of eventual correctness;
attributing every zero-step run to Jev; treating post-hoc associations as causal;
reward hacking, candidate undercoverage, stale branch state, silent API fallback;
mixing final-classifier accuracy with Granite-generated answer accuracy; and
claiming a design or mock test is an implemented/validated model improvement.

Validation: analyzer tests against deliberately different failure paths; aggregate
reconciliation against original counts and file hashes; exact pinned-model/source
inspection; primary-source links; Markdown navigation and guidance checks; canonical
lint, format, tests, and build; public diff and secret/data review; PR/CI review.
Record new findings and unsuccessful checks as well as successful ones. External
source snapshots and private benchmark traces stay in ignored local storage.
