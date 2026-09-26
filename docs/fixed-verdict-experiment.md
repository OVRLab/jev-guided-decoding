# Fixed final verdicts

The owner proposed supplying final options in code rather than relying on Granite
to generate them. The new opt-in classification modes use the fixed labels
ENTAILED, CONTRADICTED, and UNKNOWN. Existing generation/search modes remain intact.
This three-way task assumes consistent evidence; it is not a generic answer format
for arbitrary questions or inconsistent rule systems.

## Design and plan

1. Add a typed Jev Choice decision using the existing bounded HTTP transport.
   Criteria distinguish a proved claim, a proved explicit negation, and neither.
   Original evidence is authoritative; selected intermediate steps are tentative.
   Never derive UNKNOWN from exhaustion, rejection, or low model confidence.
2. Add `fixed_jev`: run existing step-guided search, then make one fixed-choice
   decision even if Granite never generated a final answer. Reserve one of the
   existing HTTP attempts and ten seconds of the existing 90-second request budget
   for this decision. Stop without another call on cancellation or service/backend
   errors. Reservations do not guarantee hard deadlines for cooperative kernels.
3. Add `direct_jev` as a control: the same Choice judgment sees only the original
   problem, with no Granite load or reasoning. This distinguishes a fixed classifier's
   benefit from the contribution of Granite's intermediate steps.
4. Preserve Granite's exact path, original search outcome, and raw decision
   distribution. A code-rendered verdict has no Granite-generated final token IDs.
   Require a unique winning option with probability at least 0.75; otherwise report
   `uncertain_verdict` with no answer. This threshold is an experimental policy,
   not a calibrated correctness guarantee. Provider confidence is recorded separately.
5. Test contracts before implementation: no-key baselines, missing inference extras,
   invalid/missing/nonfinite Choice data, ties/low confidence, incorrect model finals,
   absent final candidates, exhausted budgets, cancellation, errors, and exact token
   preservation. Verify CLI recording, combined accounting, docs, build, and CI.

Affected files: a verdict scorer/controller module, shared client transport hook,
CLI modes, focused tests/config, fresh symbolic fixtures, and a new dated report.
Fixed verdicts are separate from generated text, not artificial candidates appended
to the model's token prefix. An optional prose explanation is outside this change.

## Frozen small live check

After offline checks, freeze one rubric and six newly authored worlds (two of each
verdict) before any live results. Compare `jev`, `fixed_jev`, and `direct_jev`, seed
42: 18 planned runs, rotating order, 1,200-second stage cap. All use the selected
example prompt, pinned Granite, existing search settings, and Jev 1.13.0; fixed mode
allocates the same overall time/API ceilings between reasoning and decision.
Direct mode makes one call and performs no local generation. No rubric or threshold
tuning after seeing outputs; retain all failures and not-started jobs. Stop on a
service error and do not replay ambiguous requests.

Use the existing deterministic forward-rule oracle and frozen first-word parser;
match recorded question/evidence to the fixture. References never enter inference.
Report completion, verdict matches, per-label results, actual work, timings,
versions, source/fixture hashes, and unknown usage. This is a six-world mechanism
check with one seed, not a broad quality or model-improvement claim. Historical
traces and the previous 48-run experiment remain unchanged.

Primary documentation checked: [Choice](https://docs.typesafe.ai/primitives/choice),
[HTTP API](https://docs.typesafe.ai/api), and the
[classification cookbook](https://docs.typesafe.ai/cookbooks/hierarchical_classification).
Choice supplies alternatives and probabilities; it does not establish their truth.

## Recorded outcome

The [completed check](../reports/2026-09-20-fixed-verdict/README.md) retained all
18 runs: original step guidance matched 2/6 labels, fixed mode 6/6, and direct
Jev 6/6. Both UNKNOWN cases were classified correctly by fixed/direct modes.
Paired generated token sequences and selected paths were identical; the extra
final decision resolved classifications without improving Granite's search.
There was no post-result tuning, service error, or continuation stage.
