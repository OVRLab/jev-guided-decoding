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
