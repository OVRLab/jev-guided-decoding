# R20: blinded semantic evaluation of fixed Granite/Jev interventions

Prospective plan, 2026-09-23. The owner authorized this measurement step toward
the Granite + Jev architecture objective. Preserve every R19 score and source.
The purpose is to validate an independent evaluator before measuring the existing
interventions on fresh inputs; no architecture or grader is selected on test results.

## Questions and fixed comparison

Does R19 dual guidance improve semantic correctness over native Granite and over
static instruction attention without Jev? Retain original Granite revision
`6a7381ba1f54d684ff508d991aeb7dc580157103`, FP32, greedy full vocabulary, 32 generated
tokens, the unchanged R19 prompt, eleven heads, boundary before layer 19 and
instruction strength 5. Three arms: native, static instruction, Jev dual. Granite
owns every final token. Use the existing runtime and admission checks, with no
weight changes, new output constraint, fitted gate, prompt tuning or Jev final answer.

Fresh test: 144 authored worlds with light/heavy contexts (288 inputs), 120 Hotpot
questions, and 120 SQuAD questions (60 answerable/60 impossible), total 528 inputs
and 1,584 generations. Exclude previous project aliases, upstream IDs and used
SQuAD articles. One question per SQuAD paragraph; original passages and all ten
Hotpot paragraphs are retained within the inherited 3,072-token/32-source limits.
Public training data are project-held-out, not certified absent from pretraining.
No test answer is generated before judge admission and source/data freeze.

## Independent automated judge and admission

Use `Qwen/Qwen3-14B`, revision `40c069824f4251a91eefaf281ebe4c544efd3e18`, BF16,
Transformers 4.57.1, non-thinking chat template, greedy generation, at most 128
new tokens. This is a different model family from Granite and Jev; it is still a
fallible automated judge, not a human panel or validated universal semantic oracle.
Score one answer at a time against question, exact evidence, reference alternatives
and answerability. Return a strict Boolean correctness judgment plus brief reason.
Accept equivalent correct wording, harmless verbosity and valid natural abstention;
reject wrong partial overlaps, incomplete requested answers, contradictions,
unsupported material claims, guesses on missing evidence and false refusals.
Instructions embedded in candidate answers or evidence are untrusted data.

Build 24 development and 96 separate validation examples across twelve categories:
correct short/verbose answers, numerical equivalence, complete multipart answers,
two forms of natural abstention, false refusal, overlapping wrong entity,
contradiction, unsupported guess, incomplete multipart answer and judge injection.
Gold labels are constructed by the coding assistant from explicit fictional facts;
they are not independent human annotations. Freeze fixtures and rubric before
running the judge. Development results are diagnostic only in v1; no tuning cycle
or choosing among judges is registered. Admission requires 100% parseable results,
at least 95% validation accuracy and at least 95% recall for each Boolean class,
at least 7/8 correct in every category, and identical labels on twelve separately
repeated validation packets. Publish all errors. If admission fails, stop before
Granite/Jev test generation and report evaluator failure; a revised evaluator needs
a separately registered study and new validation data.

## Blinding, integrity and analysis

Render judge prompts from a strict allowlist: question, evidence, references,
answerability, candidate response. Exclude treatment, model names, token traces,
Jev judgments, latency and old grades. Give packets random opaque IDs, randomize
their order and grade exact duplicate case/answer pairs once, mapping the same
judgment to all matching outputs. Store the identity mapping separately; the judge
process reads only anonymous packets and the rubric. This is evaluator blinding,
not operator blinding: the implementing agent can access raw records. Freeze and
hash all judge outputs before joining treatment identities or inspecting aggregate
scores. Publish mapping and provenance afterward for full reconstruction.

Primary endpoints: binary semantic correctness, separately per domain; dual minus
native and dual minus static, six paired cluster-bootstrap contrasts, 10,000 draws,
individual 99.1667% intervals for nominal 95% family coverage within R20. Authored
contexts cluster by world, Hotpot by question, SQuAD by article. No pooled metric
or all-controls conjunction. Report answerable/missing groups, false refusals,
recognized lexical scores and semantic/lexical disagreement descriptively. Retain
all generated outcomes and failed grading attempts. A malformed/capped judge answer
is unresolved, not silently retried or dropped; report conservative score bounds.
If more than 5% of test packets are unresolved, do not claim a semantic advantage.
All results remain conditional on this admitted judge; human replication remains
necessary for stronger claims. No architectural adjustment follows from test cases.

Audit exact prompts, accepted token IDs, original weight hashes, attention maps,
receipt provenance, output work, source/data freezes, judge prompt/response IDs,
reference exclusion from Granite/Jev, blind-map coverage and grading freeze order.
Preserve test-first failures for missing capabilities, leakage/tampering, duplicate
and incomplete records, failed admission and source mismatches. Reuse existing
durable API reservations; no replay of ambiguous paid attempts. No inference rerun
for unrelated reporting fixes.

## Operations, artifacts and sources

Prior estimated spending is $30.22803312122089 of the original $50. Reserve at
most $8 compute/disk and $1 Jev, leaving more than $10 margin. Use one L40S with
an automatic four-hour expiry and a shorter process deadline; inspect current
capacity/price before creation. Store checkpoints sequentially in GPU memory.
Retain rolling local backups and verify every result byte before deleting owned
instances, disks, security rules/groups and automatic IP allocations. Publish
plan, frozen inputs, validation, all raw attempts, blinded grading, exact analysis,
cost/cleanup and manuscript update. A failed admission is a completed measurement
finding, not a positive architecture result. Keep the current PR unmerged.

Primary references checked for this plan:

- [Qwen model card](https://huggingface.co/Qwen/Qwen3-14B): model, Apache 2.0 terms,
  Transformers support and non-thinking template switch; pin the exact revision.
- [MT-Bench judge study](https://arxiv.org/abs/2306.05685): motivates explicit
  validation and avoiding preference/verbosity bias; does not validate our judge.
- [Nebius pricing](https://docs.nebius.com/compute/resources/pricing): L40S Intel
  GPU $1.35/hour, CPU $0.012/core-hour, RAM $0.0032/GiB-hour, network SSD
  $0.071/GiB per 730 hours, before taxes and separate networking.
- [TypeSafe API](https://docs.typesafe.ai/api.md) and
  [models](https://docs.typesafe.ai/models.md): retain the existing pinned Jev
  1.13.0 relevance/sufficiency request contract, no new judgment design.
