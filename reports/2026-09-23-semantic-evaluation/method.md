# R20 method and interpretation

R20 measures the existing R19 intervention on fresh questions with a separately
validated semantic judge. Its [prospective plan](../../research/semantic-evaluation-plan.md)
and [63-file source freeze](../../research/protocols/semantic-evaluation-v1/manifest.json)
precede live evaluation. Architecture settings are inherited; no new gate, prompt,
head selection, instruction strength or model weight is fitted in this study.

## Where Jev participates

```text
Question + supplied evidence + unchanged answer instructions
                          |
                Original Granite 4.0 1B
                    native prefill
                          |
              observe attention at layer 18
                          |
        boundary immediately before layer 19
                          |
     +--------------------+-----------------------+
     |                    |                       |
   native               static                   dual
 no callback       fixed local scores       one hosted Jev request
 no new bias       no Jev request            evidence relevance
                   instruction steering     + evidence sufficiency
     |                    |                       |
     +--------------------+-----------------------+
                          |
       finish the SAME prefill, retain its KV cache
      selected eleven heads use the registered biases
                          |
             Granite generates the final tokens
              greedy, full vocabulary, cap 32
                          |
       anonymous question/evidence/reference/answer packet
                          |
       Qwen3-14B judges correctness in a separate process
                 AFTER Granite generation
```

Qwen is an evaluation instrument outside Granite + Jev inference. Its reference
answers never enter Granite or Jev inputs. Jev also does not produce or replace
the final answer. No arm forces the literal word UNKNOWN: Granite can express
abstention naturally. Static steering is an important causal control because it
tests whether applying the instruction bias explains a gain without Jev judgments.
See the inherited [runtime](../../research/iterations/benefit_sufficiency/runtime.py)
and [R19 method](../2026-09-22-benefit-sufficiency/method.md) for exact bias equations.
Layer numbers are zero based. The eleven affected `(layer, head)` pairs are
`(19,6), (19,11), (19,15), (20,11), (21,14), (23,8), (29,10), (30,4), (34,4),
(37,14), (38,11)`. Earlier layers receive no bias. The dual rule steers source
attention when sufficiency is at least 0.65, the existing abstention instruction
when sufficiency is at most 0.35, and neither in between. Its selected head biases
continue through cached decoding; Jev is called once per input, not once per layer
or token. A failed request is charged and preserves native computation.

Granite is `ibm-granite/granite-4.0-1b` at
`6a7381ba1f54d684ff508d991aeb7dc580157103`, FP32. Jev requests retain `jev-1.13.0`.
The dual arm inherits instruction strength 5 and the R19 selected attention policy.
The static arm sets relevance to 0.5 for every source and sufficiency to zero;
its callback is local and cannot be counted as a hosted request. All arms have
the same prompt, model revision, token ceiling and full-vocabulary output contract.
Actual token counts and elapsed work may differ.
R20 changes both the evaluation cohort and the primary metric relative to R19.
Compare interventions within R20; a change in absolute score across studies is
not a measured improvement over time or an estimate of R19's artifact share.

## Fresh cases and comparison units

| Domain | Inputs | Sampling and dependence |
| --- | ---: | --- |
| Authored containment | 288 | 144 worlds, each light/heavy context; balanced answerable/missing; cluster by world |
| HotpotQA | 120 | Fresh project question IDs, all ten original paragraphs; cluster by question |
| SQuAD2 | 120 | 60 answerable + 60 impossible, one question per paragraph, no previously used project articles; cluster by article |

The schedule contains three outputs per input: 1,584 generations. It randomizes
arm order within each case. Prior project aliases, upstream IDs and used SQuAD
articles are excluded. This is project-held-out data; public benchmark pretraining
exposure is unknown. Original evidence fits the inherited 3,072-token/32-source
limits. References and answerability are reserved for evaluation.

## Judge admission and blinding

The independent automated judge is `Qwen/Qwen3-14B` at
`40c069824f4251a91eefaf281ebe4c544efd3e18`, BF16, non-thinking chat template,
greedy decoding and a 128-token output ceiling. GPU memory is released between
Granite and Qwen processes. The rubric accepts equivalent wording, complete
correct answers and natural abstention, while rejecting incorrect partial overlap,
contradiction, unsupported guesses, incomplete answers and false refusal.

Before Granite test generation, Qwen receives 24 diagnostic development packets,
96 separate validation packets and twelve repeated validation packets. These span
twelve categories, with eight validation cases per category and balanced Boolean
gold labels. The coding assistant constructed the gold from explicit fictional
facts; these are not independent human annotations. Admission requires all
validation outputs to parse, at least 95% overall and each-class agreement,
at least 7/8 agreement in each category and all repeat labels to agree. There is
no registered tuning cycle on these validation cases.

The main judge sees only question, evidence, reference alternatives, answerability
and candidate answer. It does not see treatment/model identity, old grades, Jev
scores, timing or token traces. Random opaque IDs are metadata and are not rendered
into prompts. Exact duplicate case/answer pairs share one grade. Packet order is
randomized, and the judge process does not read the separate treatment mapping.
After all judgments are saved, hashes freeze packets, mapping, answers and grades
before joining arms or calculating scores. This is evaluator blinding; the operator
can access the wider repository.

The [registered supplementary inspection](../../research/semantic-evaluation-blind-review.md)
reviews the first 24 unique anonymous packets after that freeze and before aggregate
analysis. The coding assistant records its own labels before reading Qwen labels
or treatment identities. This small descriptive sample is not a human review,
an independent operator, or a replacement for the primary grades.

## Analysis and claim boundaries

Primary scores are Boolean semantic correctness according to the admitted judge,
reported separately by domain. Six fixed comparisons estimate dual minus native
and dual minus static in each domain using 10,000 paired cluster bootstraps and
individual 99.1667% intervals, for nominal 95% family coverage within R20.
There is no pooled score or requirement that every comparison be positive.

Malformed, schema-invalid or output-capped judgments are unresolved, with no silent
retry or removal. The primary lower-bound score counts them as incorrect; score
upper bounds and worst/best-for-dual contrast sensitivities remain visible. More
than 5% unresolved unique packets disallows a semantic-advantage claim. Answerable
and missing-evidence groups and the old lexical metrics are descriptive. A whole
answer may be judged incorrect for false refusal, an unsupported assertion or
an incomplete answer; Boolean labels alone do not separate those error types.

An advantage would be evidence for this fixed intervention under this judge and
these tasks. It would not establish historical novelty, general reasoning gains,
a superior checkpoint, human-validated accuracy or efficient serving. Negative
results likewise distinguish limitations of this particular intervention from
the broader possibility of useful Granite + Jev architectures.

The [reconstruction instructions](reproduce.md) replay source, prompt, token, weight,
attention, provider, budget and grading integrity from saved records without new
inference. They do not turn mechanical replay into independent semantic validation.

## Editorial example rule

Fixed while main anonymous grading is running, before treatment-level score
inspection: in each domain, select the first case by case ID where valid dual and
native grades differ, once for a repair and once for a regression; show all three
arms and retain the full evidence. Report no example if the direction is absent.
This is descriptive illustration, not an additional endpoint or a representative
sample. It does not replace the separately registered 24-packet blind inspection.
