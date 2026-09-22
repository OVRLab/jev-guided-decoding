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

## Executed admission and registered diagnostics

The GPU server checked out scientific freeze `7e570c0` cleanly. Its 430 offline
tests passed in 129.96 seconds with both CPU thread pools pinned to one. Model
download completed before study launch. The Jev credential was privately copied,
SHA-verified and restricted to mode 0600; only boolean verification metadata is
public. Both [executed launchers](execution/launcher-verification.json) were
byte-verified against their public copies.

Real-checkpoint admission completed **27/27** checks on nine fixtures. Maximum
full-vocabulary logit difference and maximum all-layer KV difference were both
**0.0**. Accepted tokens, cache lengths and one-prefill work matched in every
native, always-guided and forced-failed-receipt comparison. Admission used canned
scores and zero live Jev calls. Quality execution then began on development data.

The [descriptive output supplement](../../research/boundary-output-diagnostics.md)
was registered after launch, before any development/test quality aggregates
were inspected. Three initial diagnostics tests failed because the new module was
missing, then passed. A fourth integration test passes for all three domains and
nine arms, verifying first-by-ID example selection and rejecting modified grades.
Artifact tampering, raw empty output and provider failure remain distinct checks.
The supplement changes no frozen inference or primary analysis source.

A descriptive addendum, recorded during test execution before quality-aggregate
inspection, separates paid successful no-ops, active guidance and final-token-path
changes. Its added test first failed on the missing function, then passed after
implementation. This adds no inference, policy change or significance test.

After the five descriptive tests were added, local canonical checks passed:
**435 tests in 6.80 seconds**, Ruff lint, Ruff format (294 files), guidance checker
(49 Markdown files), and source/wheel builds. Figure execution/visual inspection
and full result reconstruction remain pending the completed GPU run at this entry.
