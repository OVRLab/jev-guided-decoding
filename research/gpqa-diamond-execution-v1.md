# R27-B: full GPQA Diamond comparison

Prospective protocol, 2026-09-24. Dispatch is conditional on the exposed-only R27
engineering pilot passing source, numerical, token and receipt audits and fitting
the cost estimate. This document records the task contract before test inference;
the exact private manifest records final budget/timing and source hashes.

## Data and exposure

Use all **198** rows of `gpqa_diamond.csv` from `Idavidrein/gpqa` revision
`83022cefff930aea54f654c0b282e74b9eeda5c6`; original-file SHA-256
`41d1213cd7a4998605a26c2798500652572007161b3a92817ba46b35befcd305`.
The owner accepted access conditions. Questions, options, references, token IDs,
Jev payloads and generated answer traces remain private; publish source code,
manifests stripped of local paths, hashes and aggregate findings.

Use `Question`, `Correct Answer`, and `Incorrect Answer 1/2/3`, matching the pinned
official loader's field selection. Do not send explanations, validator comments,
author identities, answer labels or reference files to the inference worker/Jev.
There are 198 nonblank unique questions. Source rows 89 and 126 contain duplicate
**distractors**; retain all four positions, as upstream does. Correct-answer text
is unique in every row. No row is dropped or rewritten to improve model scores.

During source review, the upstream repository's five public demonstrations were
viewed. Exact normalized question comparison identifies Diamond rows **39 and
124** among them. They were not used for model/adapter training, but are manually
exposed and cannot count as untouched. Report full-source 198 and the separate
**196 untouched** subset. Mark these two as `development` in the case manifest
solely to make the exposure boundary executable. Do not tune from either subset.

`benchmark_inputs_v1.gpqa_case` uses a per-row deterministic permutation seeded
by SHA-256 of `2701/gpqa_diamond/ROW/shuffle`, independently of model answers.
The fixed resulting correct-label counts are A=35, B=70, C=52, D=41; report the
largest constant-label reference, 70/198 (35.35%), alongside model accuracy.
This is a single fixed ordering, not an average over permutation seeds.

## Generation and independent scoring

Use the [R27 engine and comparisons](benchmark-execution-v2-plan.md), including
the untouched original Granite anchor, Jev-free self-refinement, six routed
repair arms and both named larger models. Freeze adapter/checkpoint/threshold,
model revisions and sampling profiles without looking at fresh grades.
All final answer tokens remain generator-owned. Serial stopping recognizes a
complete requested answer line; no forced answer grammar or reference-controlled
retry is used. All compared models receive the same question/options and output
instruction, inside their native chat templates.

This is **full-dataset zero-shot generated-answer accuracy under the OVRLab R27
contract**, not an exact reproduction of an upstream leaderboard recipe. The
upstream code at `56686c06f5e19865c153de0fdb11be3890014df7` offers several prompts,
including few-shot demonstrations, zero-shot and multi-sample voting; our run uses
no demonstrations and one native sample per model. It uses lettered options and
`Final:` ending, choice readout v2 and matched prompts for all systems. Upstream's
first parenthesized-letter fallback is not used because an explanation can name
several options. Never compare these results directly to different model-card
protocols as if they were matched experiments.

Independent local reference grading occurs only after generation. Unparseable,
empty or unfinished-thinking responses are wrong; correct extraction never
consults the reference label. No hidden truth reaches Jev. Report accuracy,
numerator/denominator, format failures, unfinished answers, actual selected
answer tokens, all executed inference work, latency, receipt/API charges and
paired differences with descriptive 95% intervals. Show live-minus-original,
live-minus-self-refine, all routed controls and larger-model comparisons.
Intervals are descriptive, without multiplicity-adjusted superiority claims.

The inference worker must finish a complete case set for each arm/model before
the run can be called full. Interrupted runs remain partial, with known completed
coverage and failure reasons, and cannot silently use smaller denominators.

## Cost and cleanup

The cumulative authorization remains **$110**, with $46.17349123025742 recorded
before R27. Charge the engineering pilot first. This stage reserves at most
**$24**, including setup, compute, disk, hosted Jev and cleanup; unused funds
remain available for other admitted tasks. Jev is separately capped at $0.25.
Use one L40S, measured current compute+80-GiB disk rate about $1.75458/hour before
tax/separate network. Require a conservative runtime ceiling plus an independent
VM shutdown earlier than the reserve could be exhausted. No unrelated resources.
Back up private results regularly, independently verify final file hashes, then
delete this stage's owned GPU, disk and network resources. Reconcile all attempts.

Full GPQA does not complete the ten-benchmark objective. IFBench/MuSR and the
remaining seven rows retain their own admission, exposure and budget requirements.
