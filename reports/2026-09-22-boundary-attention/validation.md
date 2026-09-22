# R18 validation record

The [prospective plan](../../research/boundary-attention-plan.md) defines the new
boundary, controls, cohorts, grading adaptation, budget and separate conclusions.
At this entry, no real-checkpoint admission or live quality result is claimed.

Five initial mechanism tests failed because the new features/runtime modules were
missing, then passed after implementation. They cover one-row native GQA features,
full-vocabulary logit and all-layer cache equality to the previous runtime, exactly
one decision, one prefill, failed receipt fallback, malformed success rejection,
cancellation cleanup, early EOS and rejecting guidance before the boundary.

Two added ownership regressions failed on implemented code: a repeated cancellation
released an active worker too early, and a legacy hook could nest inside the new
attention scope. The fixes drain the worker through repeated cancellations and mark
the new scope for the legacy guard. Both regressions now pass. No paid call occurred.

Five data/schedule/selection/audit tests initially failed (four missing modules,
plus a budget-validation failure). An additional test expectation assumed that
zero-call selection must serialize as `never`; the frozen canonical-JSON tie rule
can select an equally zero-call threshold. The assertion was corrected to test
actual no-call behavior. A nested-list approximate assertion was also corrected
before implementation. These test-harness corrections are not model fixes.

An end-to-end tiny-model trace test exercised real recording, JSON serialization
and independent audit; it first exposed the auditor's hardcoded forty-layer shape.
The auditor now reads the frozen model size and boundary (forty/nineteen in the
real study), and the test passes with two layers/one. Cache, feature, work and
call tampering are rejected. Another regression demonstrated that a forged EOS
termination was accepted; the auditor now checks the frozen generation EOS IDs,
rejects continuation after EOS and requires the full final budget for a non-EOS stop.

The initial lint pass found an unused import, loop-closure bindings and long regex
lines; these were fixed before the scientific freeze. Read-only source inspection
initially looked for a nonexistent cache class name; the actual pinned
`HybridMambaAttentionDynamicCache` was then inspected. No model or paid job ran in
that inspection. A dry preparation produced the planned 260 development, 984 test
and six external admission inputs without loading Granite weights or calling Jev.

The fixed treatment, prompt and original R17 scientific files remain unchanged.
New numerical admission, all live outcomes, costs and cleanup evidence must be
reported from the eventual artifacts, not inferred from offline test success.

Pre-freeze canonical checks: **430 tests pass in 6.87 seconds**, Ruff lint/format
and the 49-file guidance checker pass, and source/wheel builds pass. These include
offline inference dependencies; core-only CI will skip optional model tests.

A pre-freeze audit portability regression supplied a one-ULP entropy difference and
failed exact feature equality. Reconstruction now permits 1e-12 arithmetic error
while rejecting booleans/nonfinite values; gate decisions still use recorded
features exactly. The draft manifest was rebound before the first source commit,
with unchanged cohort hashes and no real-model or provider inference.
