# Fixed final verdict experiment — 2026-09-20

Supplying all three final labels in code resolved the two UNKNOWN cases in this
fresh, six-world check. Existing step-guided generation matched **2/6** verdicts;
step guidance followed by a fixed Jev Choice matched **6/6**. Direct Jev using the
same choices also matched **6/6**, so this check does not establish added accuracy
from Granite's intermediate reasoning. All eighteen planned runs are retained.

## Change under test

`fixed_jev` runs the existing Jev-guided reasoning search, then asks a separate
Choice question with code-defined ENTAILED, CONTRADICTED, and UNKNOWN alternatives.
The decision judges original evidence; selected intermediate steps are tentative
suggestions, not extra facts. It never needs Granite to generate the three options
or correctly spell a final label. It also never equates search exhaustion with UNKNOWN.

The wrapper reserves one HTTP attempt and ten seconds within the existing twelve-
attempt / 90-second limits. Inner search receives eleven attempts and 80 seconds;
the final decision uses at most one attempt and the remaining time. Cancellation
and service/backend errors do not trigger another call. A unique winner must have
probability at least 0.75; low probability or a tie produces `uncertain_verdict`,
separate from semantic UNKNOWN. This threshold is an uncalibrated experiment policy.

The result schema is `fixed-verdict-v1`. Its `text` is a label rendered by code from
Jev's typed choice. The original Granite `token_ids`, intermediate `steps`, and
`reasoning_outcome` remain separately identifiable. The selected Choice label is
not appended to or disguised as Granite-generated tokens. No prose explanation,
model training, changed weights, or serving extension is introduced.

`direct_jev` asks the identical Choice question with an empty list of tentative
steps, making one call and performing no Granite generation. This control tests
whether the original problem already gives Jev enough information to classify it.

## Frozen protocol and results

Six new authored fictional worlds contain two entailed, two contradicted, and two
unknown claims. They cover joined derivations, a seeded cycle, negative routes,
missing conjunctions, and an unseeded cycle required by another rule. The labels,
rubric, threshold, fixtures, model settings, and 1,200-second stage limit were
[frozen before inference](protocol.json). Each mode ran once per world, seed 42,
with rotating order. No prompts or thresholds were revised after seeing results.

The independent symbolic oracle applies all forward rules to closure, requires
every conjunct, and distinguishes explicit negatives from missing facts. The
grader matches question/evidence to the fixture and checks the first verdict word.
Every unfinished run stays in the denominator. The questions ask for labels only;
there is no independent grading of explanations or intermediate natural-language
steps. Existing fixtures still render identically under the original defaults.

| Mode | Completed outputs | Matching verdicts | UNKNOWN cases matched | Mean seconds/run |
| --- | ---: | ---: | ---: | ---: |
| Existing step guidance (`jev`) | 3/6 | 2/6 | 0/2 | 39.10 |
| Step guidance + fixed choice (`fixed_jev`) | 6/6 | 6/6 | 2/2 | 39.28 |
| Direct fixed choice (`direct_jev`) | 6/6 | 6/6 | 2/2 | 0.39 |

| World / expected verdict | Existing step guidance | Fixed choice after reasoning | Direct choice |
| --- | --- | --- | --- |
| Parcel Niva, joined derivations / ENTAILED | ENTAILED | ENTAILED | ENTAILED |
| Toma, seeded cycle / ENTAILED | `ENTAINED` (format failure) | ENTAILED | ENTAILED |
| Valve Suri, conjunctive fault / CONTRADICTED | No eligible branch | CONTRADICTED | CONTRADICTED |
| Arin, negative route / CONTRADICTED | CONTRADICTED | CONTRADICTED | CONTRADICTED |
| Order Lumo, missing signature / UNKNOWN | No eligible branch | UNKNOWN | UNKNOWN |
| Package Zeno, unseeded cycle / UNKNOWN | No eligible branch | UNKNOWN | UNKNOWN |

The Toma failure was a misspelled label accompanying an otherwise sensible
positive conclusion, not a demonstrated logical error. Three other baseline
searches stopped without final answers. Thus the 2/6 score must not be described
as four wrong factual verdicts. Whole-answer exact-match/F1 remains in the CLI's
raw summary, but its comparison mixes bare labels and generated prose; the
dedicated [verdict grades](verdicts.json) are the primary metric here.

All six pairs of existing and fixed-mode searches had **identical actual prompts,
proposal token sequences, and selected token paths**. Their generated/prefill work
also matched. The observed changes came from the added final decision stage;
Granite's underlying search did not improve. The [paired checks](paired-paths.json)
record this result explicitly. The final stage combines fixed option availability,
a Choice rubric, and a probability gate; the experiment does not isolate each
component's causal contribution.

## What happened on missing evidence

For Order Lumo, Granite correctly established that the order met document
requirements, then could not complete a valid derivation without the manager's
signature. Both searches stopped with `no_eligible_branch`. The fixed decision
then selected UNKNOWN with returned probability 1.0; direct Jev also selected
UNKNOWN at 1.0. These are Jev's returned values, not proof of perfect certainty.

For Package Zeno, the signed/registered rules form a cycle with no starting fact.
Granite derived visibility but did not resolve that missing prerequisite. The
fixed decision selected UNKNOWN at 0.99, compared with 0.97 for direct Jev; both
matched the oracle. A slightly different model probability does not demonstrate
a quality benefit from the supplied step.

The Valve Suri case rules out a simple UNKNOWN-on-failure interpretation: Granite
only proposed restatements of the given conditions, which failed Jev's progress
test. The fixed decision nevertheless selected the provable **CONTRADICTED** label
at 0.97, as did direct Jev. The final options were evaluated against the evidence
even though search returned no useful step.

## Work, provenance, and integrity

| Mode | Generated tokens | Padded decode slots | Repeated prefill tokens | HTTP attempts | Jev input tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| Existing step guidance | 1,675 | 1,827 | 67,551 | 23 | 27,710 |
| Step guidance + fixed choice | 1,675 | 1,827 | 67,551 | 29 | 31,916 |
| Direct fixed choice | 0 | 0 | 0 | 6 | 4,024 |

All 58 HTTP attempts succeeded, recording 63,650 input and 4,520 output tokens;
usage is known for all responses. The six added final decisions used 4,206 input
tokens and 1.96 seconds in total. The historical configured input-only price gives
about $0.00267 across all modes; this excludes output charges and local compute
and is not an invoice. The twelve Choices had winning probabilities from 0.97
to 1.0. Uncertain/error outcomes were covered offline, not encountered in this run.

The source was `40e5683d3e88219758c6b2a4abee2726d3154438`, clean at capture. The model
was original `ibm-granite/granite-4.0-1b`, revision
`6a7381ba1f54d684ff508d991aeb7dc580157103`, zero trainable parameters, on Apple M1 Pro
/ MPS BF16. Python 3.12.13, Torch 2.8.0, Transformers 4.57.1, and macOS 26.3.1 were
recorded. Every response reported `jev-1.13.0`.

This mixed benchmark loaded Granite once (4.08 seconds) for the generation arms,
then warmed two tokens at batch sizes one and three. Loading and warm-up are
excluded from per-run times. Direct rows do no generation despite the model being
loaded for other rows; the standalone direct-only CLI avoids backend loading/import
entirely, as checked offline. There were no restarts, cancellations, service errors,
or stage/time overruns. The longest request was 52.13 seconds. Exit 3 correctly
reported the baseline's incomplete searches.

The offline audit verified frozen hashes, all **52 proposal prefixes**, twelve
Granite token paths plus six empty direct-control paths, four backtracks, child
eligibility, exact original reasoning outcomes, and work summaries/budgets. It
also checked all twelve final payloads against the original problem, fixed rubric,
and selected steps, and matched recorded labels/probabilities to raw responses.
The [integrity record](integrity.json) is a mechanical trace audit, not semantic
validation by another model. Raw files are copied byte for byte from the live output.

## Interpretation and limits

The fixed final choices address a real candidate-availability and output-format
problem in this sample. They let the workflow classify evidence when generation
stalls. They do not repair the stalled search or produce a justified explanation.
Direct Jev's equal result means these tasks do not establish added classification
accuracy from Granite or its intermediate steps.

This is six simple, public synthetic worlds with one seed and motifs related to
earlier fixtures. It is not a broad benchmark, confidence calibration, or evidence
that general questions can be reduced to these three labels. The task assumes
consistent evidence; an inconsistent rule set needs a different decision contract.
Latency is descriptive on this local/hosted setup, with different work across modes;
no colocated or GPU-server speedup was measured. Earlier reports remain unchanged.

## Verification and reproduction

Before the live run, 157 offline tests passed, including the optional tiny-model
checks. Lint, formatting, 44-file guidance validation, package build, and whitespace
checks passed. New tests first failed because the verdict module/runner and CLI
modes were absent, and because label-only fixtures still requested explanations.
Additional checks cover ambiguous transport failures, cancellation in either stage,
reserved budgets, kernel overruns, ties/low probability, invalid Choice responses,
original token identity, and direct operation without the inference backend.

```bash
uv run --no-sync python experiments/fixed_verdict_probe.py evaluate \
  --output results/new-fixed-verdict
uv run --no-sync python experiments/fixed_verdict_probe.py grade \
  --output results/new-fixed-verdict
```

Use fresh output paths. The first command is a live, bounded experiment; grading is
offline. Current-source or provider changes may alter outputs. Supporting artifacts:
[metadata](metadata.json), [all raw rows](runs.jsonl), [resource summary](summary.json),
[grades](verdicts.json), [frozen protocol](protocol.json),
[design](../../docs/fixed-verdict-experiment.md),
[fixtures](../../experiments/fixed_verdict_worlds.json), and
[configuration](../../configs/granite-4.0-1b-fixed-verdict.toml).
