# Controlled ProofWriter evaluation

Plan recorded before implementation or live evaluation on 2026-09-20.

## Question and controls

Does selecting Granite's intermediate text with Jev improve final classification
beyond the same final Jev Choice applied to unguided Granite text, and beyond
direct Jev? This evaluates frozen-weight text search, not neural fusion.

The main arms are `fixed_jev`, `unguided_fixed_jev`, `final_only_fixed_jev`, and
`direct_jev`. The final-only arm uses the existing `final_jev` search and the same
fixed Choice, isolating final-frame filtering from intermediate guidance. The new
unguided arm uses likelihood selection over the same number of candidates, with
the same prompt, seeds, token ceilings, final rubric, and reserved time/API budget.
Granite-alone answers are also graded from the unguided arm's preserved reasoning
outcome, before the final Choice; guided generated answers are a diagnostic control.
These derived outcomes reuse the exact generated path and incur no extra inference;
they are not independent runs. Final Choices never see the generated final label.
Keep actual compute and wall time visible: equal ceilings are not equal computation.

## Data, splits, and analysis

Use the authors' ProofWriter V2020.12.3 release, open-world (OWA) D5 test split,
with one question per distinct theory and 200 questions spanning proof depths
0 through 5 plus unprovable questions. Select deterministically before inference;
balance labels as closely as the strata permit and retain source IDs and hashes.
UNKNOWN has no proof depth; report it separately, not as a fabricated depth.
Use a separate small development split only for integration checks. Do not tune
rubrics or settings against test outcomes. Public benchmark exposure in model
training cannot be ruled out. Follow with independently generated controlled
rule problems, whose labels are computed by code, as a separate stress test.

Run each main arm at seeds 42, 43, and 44. Rotate execution order. Repeated seeds
are repeated measurements of the same 200 problems, not 600 independent problems.
Primary comparisons are guided minus unguided-final, guided minus final-only,
and guided minus direct,
using per-problem seed-averaged correctness and paired confidence intervals;
report all three comparisons with multiplicity accounted for, plus wins/losses/ties.
Count all planned outcomes, including missing, failed, uncertain, and unfinished,
in end-to-end accuracy; also show coverage and accuracy conditional on completion.
Grade exact canonical labels separately from spelling errors. Report UNKNOWN
precision/recall, confusion matrices, per-depth accuracy, and seed variation.
Independent step checking must distinguish supported claims, premise repetition,
unsupported claims, and text that the checker cannot parse; never score unparsed
natural language as valid. Jev's own scores are not independent proof validation.

## Implementation and verification

Affected files: verdict controller, CLI mode registration, offline tests, a new
ProofWriter adapter/oracle and experiment runner, pinned config, protocol, and
new reports. Preserve historical reports. Test the missing unguided behavior first,
including zero intermediate API calls, likelihood choice, exact token path, shared
deadline, final errors, and no reference leakage. Test deterministic selection,
unique theories, source/label checking, missing-run denominators, paired analysis,
and exclusive output handling offline before any live test.

Record source revision/dirty state, data/config/prompt hashes, model revisions,
returned Jev versions, hardware/runtime, model load and warm-up, every candidate
and decision, actual prefill/decode/padded work, API attempts, and unknown usage.
Use existing bounded HTTP transport without replaying ambiguous paid timeouts.
Persist each attempted job before dispatch and its result after completion;
continuation may run only jobs never started, preserving every prior attempt.
Stop on a service/backend failure, cancellation, or the declared global budget;
an incomplete study is not a positive result. Freeze the concrete manifest and
budgets after offline checks and the separate integration pilot, before test calls.

## Concrete first run

The offline oracle matched every author label and provable question depth in the
948 test theories and 482 development theories. Negative `~` conditions in the
OWA release require explicit negative facts, just like `-`; they are not failure
to prove a positive fact. A regression covers this distinction. Unknown questions'
source `QDep` describes failed search and is not treated as a proof depth.

Selection uses seed 20260920, one question per distinct theory and evidence text:
67 ENTAILED, 67 CONTRADICTED, and 66 UNKNOWN. Within each provable label, depths
0--4 have 11 questions each and depth 5 has 12. The pilot uses only three distinct
development theories (one entailed at depth 1, one contradicted at depth 3, and one
unknown) and seed 42. The main study has 2,400 executed jobs: 200 x 3 seeds x 4
arms, plus three generated-answer controls derived without extra computation.

The [pinned config](../configs/granite-4.0-1b-proofwriter.toml) retains the existing
examples prompt and thresholds. Each generation arm permits three candidates,
eight frames, ten expansions, one resample, 512 path tokens, 2,304 padded decode
slots, 60,000 prefill tokens, and 90 seconds including a ten-second final reserve.
The guided and final-only arms each permit at most 16 HTTP attempts including
the final Choice; unguided and direct arms each use at most one. The study
ceiling is 48 active hours and 20,400 HTTP attempts, not an expected duration or
bill. Original Granite weights and the pinned Jev version remain unchanged.

Source `f97ef49` added the missing control and runner. The three new control tests
first failed because the mode was absent; oracle/runner tests first failed at
collection because their new modules did not exist. The tilde-negation regression
then reproduced rejection of a real dataset representation before its fix. The
full offline suite passed 170 tests before the pilot. No live test answers were
used to choose prompts, thresholds, or controller settings.

### Reproduction

Download the archive from the authors' link below into ignored local storage, then:

```bash
uv run --no-sync python experiments/controlled_study.py freeze \
  --archive results/proofwriter-source/proofwriter-dataset-V2020.12.3.zip \
  --config configs/granite-4.0-1b-proofwriter.toml \
  --output results/proofwriter-study
uv run --no-sync python experiments/controlled_study.py run \
  --output results/proofwriter-study
uv run --no-sync python experiments/controlled_study.py analyze \
  --output results/proofwriter-study
```

Add `--pilot` to `freeze` with a separate output directory for the development
check. `run` verifies frozen code/data hashes and acquires an exclusive lock; a
second invocation skips every already-started job, including failed or ambiguous
attempts. It never repeats a poor answer. A leftover lock requires checking that
its process has actually stopped before a maintainer removes it. Analysis files
use new timestamped names and do not overwrite prior analyses.

The exact leading-claim checker is a partial semantic audit, not a proof verifier:
it recognizes atomic consequences, checks them against the full symbolic closure,
and reports premise copies, repeats, unsupported claims, and unparsed text. It does
not certify a generated explanation's cited reasoning or silently count unparsed
text as correct. Report this limitation next to all step-quality results.

## Sources and rights

- [ProofWriter paper](https://arxiv.org/abs/2012.13048)
- [Authors' dataset archive](https://aristo-data-public.s3-us-west-2.amazonaws.com/proofwriter/proofwriter-dataset-V2020.12.3.zip)
- [Related RuleTaker source](https://github.com/allenai/ruletaker)

Inspect the release's notices before redistributing examples; the project's MIT
license does not relicense the external dataset. Store the downloaded archive in
ignored local results and retain provenance rather than committing the full archive.
The downloaded archive has a format README but no explicit dataset license file;
keep its raw examples and full traces local and publish aggregate findings, case
identifiers, hashes, and reproduction code. The related generator's Apache license
is not automatically a license for the separately distributed dataset.

## Pre-test control amendment and stress test

After the original three-arm development pilot, code inspection identified a
confound: `fixed_jev` filters generated final frames as well as intermediate steps.
Before any test-set inference, the protocol therefore added `final_only_fixed_jev`,
which leaves steps unjudged but filters generated finals before the same Choice.
Its separate capability test failed for the absent mode before implementation.
On the same hardware, an additional development pilot would run only this new arm
on the same three dev problems. The owner subsequently selected a cloud GPU, so a
fresh four-arm development pilot will verify CUDA execution and estimate runtime.
This is a declared hardware integration check on development data; preserve the
nine completed MPS attempts separately and do not pool their timing with CUDA.

The three primary comparisons each receive a 98.333% problem-cluster bootstrap
interval (5,000 resamples, analysis seed 20260920), giving a nominal 95% familywise
level by Bonferroni adjustment. These are approximate finite-sample intervals,
not a mathematical proof. Positive accuracy evidence requires all three lower
bounds above zero, all planned jobs recorded, and no service/backend/unknown-usage
failures. A null or negative outcome does not authorize tuning and rerunning test
questions. Exact-label accuracy is primary; first-label accuracy is a secondary
formatting diagnostic for generated answers.

The [stress generator](../experiments/reasoning_stress.py) creates 24 fictional
worlds independently of model outcomes: depths 2, 4, 6, and 7; a chain/cycle and a
conjunction motif; and all three labels. Each world includes six distracting
facts, shuffled rules, and an unseeded cycle where a premise may be missing.
The same forward oracle checks every label and provable depth. These are new
instances of known logical patterns, not evidence of contamination-free reasoning.
Run all four arms at seed 42 only (96 jobs, three active hours and 816 HTTP-attempt
ceilings) as a separate diagnostic; it cannot meet the main study's success rule.
Use `freeze --stress` without `--archive`, a fresh directory, and the same config.
The seven-rule cases fit the configured eight-frame path limit in principle;
branching, verbosity, and rejected steps can still exhaust the budget.

## Cloud execution

Use one inexpensive GPU sufficient for the frozen 1B model. Install the locked
development and Transformers extras, download the pinned model revision, and record
the GPU and driver separately from the runner's backend metadata. Run the four-arm
development pilot before freezing the main and synthetic datasets; do not adjust
prompts or thresholds using held-out outcomes. Retain the original 90-second limit
on CUDA and disclose that faster generation can use more of the token budget.

Use a committed source revision, a private key file outside the checkout, a bounded
server lifetime, and periodic result backups. A provider interruption must preserve
the started-job journal; resumption skips every previously started job. Stop GPU
billing after completion or failure, retrieve evidence, then delete only the
temporary resources created for this study. Never reuse production model servers.
