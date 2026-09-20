# Controlled ProofWriter evaluation

Plan recorded before implementation or live evaluation on 2026-09-20.

## Question and controls

Does selecting Granite's intermediate text with Jev improve final classification
beyond the same final Jev Choice applied to unguided Granite text, and beyond
direct Jev? This evaluates frozen-weight text search, not neural fusion.

The main arms are `fixed_jev`, `unguided_fixed_jev`, and `direct_jev`. The new
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
Primary comparisons are guided minus unguided-final and guided minus direct,
using per-problem seed-averaged correctness and paired confidence intervals;
report both comparisons with multiplicity accounted for, plus wins/losses/ties.
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

## Sources and rights

- [ProofWriter paper](https://arxiv.org/abs/2012.13048)
- [Authors' dataset archive](https://aristo-data-public.s3-us-west-2.amazonaws.com/proofwriter/proofwriter-dataset-V2020.12.3.zip)
- [Related RuleTaker source](https://github.com/allenai/ruletaker)

Inspect the release's notices before redistributing examples; the project's MIT
license does not relicense the external dataset. Store the downloaded archive in
ignored local results and retain provenance rather than committing the full archive.
