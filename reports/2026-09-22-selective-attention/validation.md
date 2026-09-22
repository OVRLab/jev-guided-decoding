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
GPU numerical admission subsequently passed all nine real-checkpoint fixtures for
both additive and mass-preserving cached/full-prefix computation. The held-out run is
running; no held-out quality result is claimed at this stage.

The first cloud bootstrap had 395 passing tests and one pre-existing test's
60-second wall-time timeout (134.96 seconds total). CPU intra-op threads were one
but inter-op threads defaulted to four. Explicitly setting both to one produced
**396 passing tests in 11.96 seconds** before loading the real checkpoint. The
original failure log is retained, and no paid/model-study job was replayed. The
inference launcher already sets both thread counts to one.

Four additional offline checks exercise actual tiny-model phase boundaries and
uniform-score no-op/weight identity. The separately registered
[routing supplement](../../research/selective-routing-supplement.md) has three
tests that first failed because its module was missing, then passed. Its offline
counterfactual does not change the frozen cloud source or live schedule.
With the additional output diagnostic, additive-hook equivalence and four budget
frontier tests, the full local suite passes **409 tests**; lint,
formatting, guidance checks and builds also pass. The cloud's frozen checkout
remains `796873b`; later test/docs/offline-analysis commits do not alter its model run.

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

The four budget-frontier tests first failed because the new module was missing,
then passed. They check development-only selection under call ceilings, rejection
of uniformly harmful guidance, exact pilot/prefill work accounting and frozen-rule
tampering. The first lint check flagged a long line and the UTC alias; both were
fixed before freezing the supplementary script and selection.

The final report will record GPU admission, all executed counts, artifact audit,
provider failures, source/runtime/weight hashes, actual cost and cleanup evidence.
Do not infer those outcomes from the passing offline suite.
