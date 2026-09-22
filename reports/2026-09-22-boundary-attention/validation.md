# R18 validation record

The [prospective plan](../../research/boundary-attention-plan.md) defines the new
boundary, controls, cohorts, grading adaptation, budget and separate conclusions.
The full run and public archive reanalysis now pass; results and limitations are
in the [completed report](README.md). The chronological development record follows.

## Before the scientific freeze

At the initial entry, no real-checkpoint admission or live quality result was claimed.

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
At the scientific freeze, numerical admission, live outcomes, costs and cleanup
still required real artifacts; offline test success was not evidence for them.

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
(49 Markdown files), and source/wheel builds. At that entry, figure execution/visual inspection
and full result reconstruction were still pending the completed GPU run.

Direct hardware inspection and Nebius's platform API identify `gpu-l40s-a` as
**Intel Ice Lake**, with a Xeon Gold 6338 visible in the VM. An initial private
cost helper had assumed the AMD CPU rate from the platform suffix; it was corrected
before final accounting to $0.012 per vCPU-hour, giving $1.5484/hour for GPU/CPU/RAM
plus disk. The difference is $0.016 per VM-hour and remains within the registered
reserve. No scientific source or earlier study cost was changed. The
[hardware record](execution/hardware.json) preserves the actual environment;
[Nebius pricing](https://docs.nebius.com/compute/resources/pricing) supplies the rates.

## Completed inference, audits and operational recovery

All 9,376 planned outcomes completed: 520 development and 8,856 test. The original
frozen auditor passes for 1,244 exact inputs, 184,889 final tokens, 188,884 model
forwards, 4,920 branch identities, all 45 scientific source hashes and unchanged
weights. All 1,244 paid Jev attempts succeeded, with 2,383,188 known input tokens
and zero unknown usage. No source, selection, prompt or grade was changed after
the scientific freeze, and no paid/model job was replayed.

All fifteen remote result files were byte-verified before cleanup. The first stop
command failed because the Nebius CLI login expired. A read-only authentication
check had succeeded earlier in the run; it did not prevent later expiry. Refreshing
the existing browser sign-in restored CLI access, then the owned VM, managed disk,
security group/rules and automatic allocations were verified deleted. The original
error remains private to avoid exposing authorization URLs and cloud identifiers;
the [public recovery record](execution/cleanup-auth-recovery.json) contains only
operational facts. The full delay is included in the $3.77 estimate.

Packaging, bound descriptive diagnostics, lossless public unpacking and complete
public reanalysis all passed. Every main-analysis field except its audit timestamp
matches. A subsequent environment-metadata import failed because the orchestration
helper ran under system Python without NumPy. Only the unexecuted metadata/table/
figure stages were resumed with `uv run --no-sync python`; no audit was weakened,
raw artifact replaced, dependency changed or inference rerun. The original failure
log is retained privately and a [public summary](execution/reporting-recovery.json)
records its scope.

Seven scientific PNG/SVG/PDF figures were generated from the audited JSON. Visual
inspection found overlapping annotations in the quality/request plot; only their
positions were adjusted and that figure was rechecked. All seven final layouts
have been inspected. Labels distinguish 98.333% primary intervals, exploratory
comparisons, measured work and reconstructed uncached timing.

Unblinded reading of predetermined examples found a SQuAD lexical-metric reversal:
a shorter wrong answer scores higher F1 than a longer correct one. This is documented
in the report/paper without changing grades or extrapolating its prevalence.
All positive, negative, missing-evidence and empty example categories remain.

The actual PR base is `feat/initial-controller`. The full change inventory and
relevant runtime, ownership, data, audit, reporting and documentation changes were
reviewed with prior historical review records retained. The review bot reports
exhausted code-review quota; no independent automated or human scientific review
is claimed. Current source checks and public-content verification are recorded below.

## Final local checks

- `uv run --no-sync pytest -q`: **435 passed in 6.89 seconds**, with optional
  inference dependencies installed; no live model or provider calls.
- `uv run --no-sync ruff check .`: passed.
- `uv run --no-sync ruff format --check .`: passed, 298 files checked.
- `uv run --no-sync python scripts/check_ai_docs.py`: passed for 49 Markdown files.
- `uv build`: source distribution and wheel built successfully.
- Exact credential/resource/private-key-marker scan: 818 public/tracked files,
  including decompressed archives, checked against 68 sensitive values; no matches.
  This is a scoped check, not a claim to detect every possible secret.
- Full public archive unpack/reanalysis: all fifteen raw file hashes and every
  main-analysis field except timestamp match; zero model forwards or provider calls.

Frozen inference and prior reports were not rerun for these editorial changes.
Fresh PR checks are inspected after the final report commit is pushed; repository
CI uses core environments and does not replace the recorded GPU admission.

The final full PR inventory contains 765 changed files against its actual base;
prior completed report directories have no changes since R18 execution began.
All 45 frozen scientific file hashes match, and 420 local links across 17 affected
Markdown files resolve. The full whitespace check reports Matplotlib-generated SVG
path whitespace and four verbatim, token-capped model-output lines in examples.md.
Those generated/verbatim bytes are retained intentionally. The separately scoped
authored-source/prose whitespace check passes; no scientific output was trimmed.
