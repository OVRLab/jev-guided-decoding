# R17 validation record

Before live inference, eight new mechanism/controller tests failed because the
new attention, policy and runtime modules were missing. After implementation,
all eight passed: evidence-mass conservation/causality, additive and conserving
cache/full equivalence, scoped dispatcher restoration, bounded timing policies,
benefit-gate selection, no-call native identity, successful guided restart,
provider-error fallback and early EOS.

Three further data/schedule/audit tests first failed because their modules were
missing, then passed. These verify balanced fresh worlds, gate-first complete
test scheduling, and rejection of token/call-provenance tampering. These initial
failures establish missing scaffolding/capability, not a reproduced old-code bug.
The private original test logs are retained; no credentials were used by tests.

Pre-run canonical checks pass: **396 tests**, Ruff lint and formatting, the AI
guidance checker (49 Markdown files), and wheel/source builds. Inference tests use
offline tiny models; the core-only CI environment skips optional dependencies.
GPU numerical admission and live quality remain pending at this initial record.

The prepared cohorts contain 156 development inputs, 704 test inputs and six
external mechanics examples. All 254 Hotpot questions are disjoint from R16's
212 questions; authored entities were checked against earlier protocols. The
scientific source hashes match the frozen manifest. No answers or supporting-fact
annotations enter eligibility, scorer inputs or generation prompts.

A private data-validation helper initially used system Python and could not
import the package. It was rerun successfully in the project environment before
inference or cloud launch. The workflow now explicitly requires that interpreter
for package-importing helpers. This was a local environment mistake, not a model
or API result.

The final report will record GPU admission, all executed counts, artifact audit,
provider failures, source/runtime/weight hashes, actual cost and cleanup evidence.
Do not infer those outcomes from the passing offline suite.
