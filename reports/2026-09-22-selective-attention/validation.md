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
frontier tests, the full local suite passes **414 tests**; lint,
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

## Offline reproduction commands

Use the locked development + Transformers environment and cache the tokenizer at
model revision `6a7381ba1f54d684ff508d991aeb7dc580157103`. The final report's raw
manifest maps public compressed files to their original names and SHA-256 values.
The public unpacker verifies both stored and decompressed hashes before creating
a fresh output directory. Its five tests first failed with the module absent,
then passed for reconstruction, duplicate/path rejection and tampered stored/raw
bytes. These analysis commands do not execute Granite or send Jev requests:

```bash
uv run --no-sync python research/diagnostics/unpack_selective_artifacts.py \
  --report reports/2026-09-22-selective-attention \
  --output results/r17-public-replay
export R17_RESULTS=results/r17-public-replay/selective-attention-v1
uv run --no-sync python research/iterations/selective_attention/analyze.py \
  --manifest research/protocols/selective-attention-v1 \
  --results "$R17_RESULTS" --output /tmp/r17-audit.json
uv run --no-sync python research/diagnostics/selective_routing.py \
  --manifest research/protocols/selective-attention-v1 \
  --results "$R17_RESULTS" --main-analysis /tmp/r17-audit.json \
  --output /tmp/r17-routing.json
uv run --no-sync python research/diagnostics/selective_outputs.py \
  --manifest research/protocols/selective-attention-v1 \
  --results "$R17_RESULTS" --main-analysis /tmp/r17-audit.json \
  --output /tmp/r17-outputs.json --examples /tmp/r17-examples.md
uv run --no-sync python research/diagnostics/selective_budget.py analyze \
  --manifest research/protocols/selective-attention-v1 \
  --results "$R17_RESULTS" --main-analysis /tmp/r17-audit.json \
  --selection research/protocols/selective-budget-frontier-v1/selection.json \
  --output /tmp/r17-budget.json
```

Use fresh output paths; scripts refuse to overwrite evidence. Audit timestamps and
the supplementary file bindings to a newly timestamped main audit can differ on
reproduction; underlying grades, counts and seeded statistical results should not.
The live study's scientific source remains frozen at `796873b`; the supplementary
analysis scripts and added tests have their own commits and source hashes.

After audited report JSON exists, regenerate standalone figures with:

```bash
uv run --no-project --python 3.12.13 \
  --with matplotlib==3.11.2 --with numpy==2.5.3 --with pillow==12.3.0 \
  python research/diagnostics/render_selective_attention.py
```

Those exact plotting package versions were resolved and imported locally before
the held-out run completed. The five main figures and optional sixth budget-replay
figure still require visual inspection once actual audited results are available.
