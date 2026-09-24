# R27 task preparation: IFBench, MuSR and AIME 2026

Recorded before inference on their previously untouched cases, 2026-09-24. These
are candidate next tasks under the [R27 plan](benchmark-execution-v2-plan.md),
subject to its remaining budget and separate final manifests. Preparing their
inputs does not mean they have run or all fit the remaining authorization.

[The adapter](evaluation/full_short_tasks_v1.py) creates prompt-only cases and
separate local references, with immutable source revisions from the
[ten-task contract](benchmark-suite-contract-v1.md). It passes synthetic
prompt/exposure/reference tests. Existing R26 data and code are unchanged.

## IFBench

Use all 300 prompts byte-for-byte as stored in the upstream JSON strings, from
AllenAI commit `1c40f0c10d9b5c5c2f10a175a28007ebb64f7f4d`, data SHA-256
`d2ada7da94a38cfe406351614c4e686846ed2da6d1b339db95fa5ead19554a4a`.
No answer-format suffix or terminal-line stop applies to instruction tasks.
Native EOS/token ceilings remain in effect; thinking content is excluded from
the larger model's final response. R23's twelve development IDs are marked exposed;
report 300 full-source and 288 untouched prompts separately.

Use upstream evaluator SHA-256
`e681a4b03a6a9dfb540fbd9ef6b963de503a5ffac557ed611c326ee385850cf6`:
strict prompt-level pass is primary, loose prompt-level pass also reported.
Both receive the same null-padding removal, matching upstream strict input
handling and the already tested R23 correction. Empty-response validation covers
all 300 source rows, with all 300 correctly failing strict and loose and no errors.
This structural check does not itself validate semantic usefulness; instruction
compliance and useful reasoning remain distinct measurements.

## MuSR

Use all 756 rows at revision `7c365b439a222150f317764d4f16ae6c96d7d94a`:
250 murder, 256 object-placement, 250 team-allocation cases. Preserve each
narrative, question and choice string; confirm answer index agrees with answer
text only during private preparation. Use the shared R27 lettered zero-shot
prompt/readout; this differs from upstream numbered-answer/random-fallback
evaluation, so report the exact OVRLab contract instead of claiming leaderboard
protocol parity. Unparseable output receives no random credit.

Cluster stories without using answer labels. Join identical narratives, identical
normalized first 150 characters (for long narratives), or five-word shingle
Jaccard >=0.65, then take connected components within family. This yields
116/64/250 clusters. Known murder variants 212/213 join correctly even though
most of their evidence text differs. Propagate R23 exposure to every member of
its story component: 6/16/4 cases exposed, **26 total**, leaving **730 untouched**.
Report both 756 full-source and 730 untouched cases and paired cluster-resampled
intervals. This conservative text heuristic is not proof that all remaining
stories are semantically independent or absent from pretraining.

## AIME 2026

Candidate full coverage is 30 problems at revision
`79037aebdb6580008fb960d17cb21fd3099083e3`, source SHA-256
`52822957957a3f577d1e9706c36a66a8108a3f99b6aff424cfb72dff0094a9ee`.
Preserve problem text and request the shared `#### NUMBER` answer ending; accept
the frozen numeric readout's explicit forms and compare numeric value, so leading
zeroes do not change correctness. References must be integers from 0 to 999.
One native generation per case/profile is pass@1 under the R27 resource contract,
not a multi-sample mathematical-reasoning estimate. A 30-problem result has wide
uncertainty. Final source attribution and official-protocol review still precede
any dispatch; preparing these cases is not a quality claim or paid run.

Every actual stage keeps the same original/checkpoint/Jev versions and controls,
records real token work and cost, and remains inside the cumulative $110 cap.
Select affordable task order from engineering cost/evaluator readiness, never
from favorable test grades; do not replace missing benchmark rows or manufacture
a ten-task mean from a partial suite.
