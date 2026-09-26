# MuSR transfer feasibility, 26 September 2026

This is a **structural inspection with zero model inference and zero Jev calls**,
performed while R30 runs. It is not benchmark completion, a frozen evaluation
protocol, or a reason to tune the active study.

The authors' [TAUR-Lab/MuSR dataset](https://huggingface.co/datasets/TAUR-Lab/MuSR)
is pinned at `7c365b439a222150f317764d4f16ae6c96d7d94a`. The card declares
CC BY 4.0; the external dataset retains that license. Credit Zayne Sprague,
Xi Ye, Kaj Bostrom, Swarat Chaudhuri and Greg Durrett and the
[MuSR paper](https://arxiv.org/abs/2310.16049). The
[official code](https://github.com/Zayne-sprague/MuSR) supplies evaluation context.

## What was checked

All 756 rows have consistent answer indices and answer text. Under an illustrative
zero-shot, direct-answer prompt containing the complete narrative, question and
labeled choices, every row fits the pinned Granite tokenizer's 2,048-input-token
cap. These counts are for this illustrative prompt, not the official few-shot or
chain-of-thought setup. Additional repair prefixes need their own length check.

| Domain | Questions | Distinct narratives | Choices | Input tokens, min–max |
| --- | ---: | ---: | --- | --- |
| Murder mysteries | 250 | 250 | 2 | 831–1,543 |
| Object placements | 256 | 64 | 2–5 | 780–1,485 |
| Team allocation | 250 | 250 | 3 | 557–853 |

[Machine-readable inspection](diagnostics/musr-admission-20260926/summary.json)
contains file hashes, label distributions and counts. Raw external data remain in
private local cache for now; the summary does not include model predictions.

## Consequences for a prospective experiment

Object placement has **four questions per narrative**. Questions sharing a story
must stay together across any development/test partition and uncertainty must
resample stories, not pretend all 256 questions are independent. This task asks
about where a person would look, which can differ from physical location; our
current authored tracking worlds do not validate that belief-tracking capability.

R29/R30 use three numbered answers per prompt; MuSR's standard row has one answer.
The current branch's rigid three-slot input validation cannot honestly be described
as drop-in public transfer. A bounded variable-slot extension could support one
question at a time with unchanged learned matrix dimensions, but needs new tests,
reference-free memory/payload admission and an explicitly frozen protocol. Repeating
one question three times or grouping four questions changes the evaluation prompt;
it must not silently replace the standard row contract.

Freeze the same complete-narrative prompt, generation settings, answer extraction
and denominators for all compared generators. Verify unrestricted token provenance,
format failures, length stops and basic direct-answer competence for original and
larger Granite; earlier truncated thinking outputs were not fair larger-model
comparisons. Include a sensible Granite-only use of repair computation and controls
that distinguish Jev's information from trained correction. Count held-out labels
only in grading and a separately named oracle diagnostic, never in live feedback.

This public-task candidate remains conditional on R30 and the next architecture
study. No claimed win, paid launch or corpus-specific training follows from access
and length feasibility alone.

## Exposure and scenario binding (subsequent structural check)

Prior R23–R27 output/receipt records contain the same 12 MuSR questions selected
for R23 development. They are not untouched test cases. The author's original
JSON also identifies counterfactual murder variants with a shared `story_hash_id`:
250 murder narratives form **125 two-variant scenarios**, despite their distinct
text. Using exact text alone would miss this dependency.

The [frozen grouping/exposure map](diagnostics/musr-admission-20260926/grouping-and-exposure.json)
joins every HF row to the author's data at
`b1f4d4168a9cfc6760e8b74d728e4516023dfaa5`, using exact narrative, question and
choice text. No label, belief state, skill value, best allocation or reasoning
tree enters a grouping key or model input. Team grouping uses task strings and
character names only and finds no repeated identities in this corpus; that is a
specified grouping rule, not proof against every possible latent dependence.

| Domain | Scenario groups | Prior direct questions | Questions excluded with related variants | Eligible fresh questions / groups |
| --- | ---: | ---: | ---: | ---: |
| Murder mysteries | 125 | 4 | 6 | 244 / 122 |
| Object placements | 64 | 4 | 16 | 240 / 60 |
| Team allocation | 250 | 4 | 4 | 246 / 246 |
| Total | 439 | 12 | 26 | **730 / 428** |

The [binding helper](diagnostics/musr_groups.py) has three offline tests covering
counterfactual groups, hidden-label independence, duplicate rejection and exact
source coverage. All 756 real rows bind successfully. A future full 756-row score
must disclose the 26 development-related rows separately; it cannot be called
756 entirely fresh questions. A confirmatory untouched comparison can use the
730 eligible rows with these scenario groups, after a separately frozen protocol.
