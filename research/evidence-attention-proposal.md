# R14 proposal: Jev-guided attention to source evidence

Date: 2026-09-21. Status: **design proposal only; no hook implemented, no new
inference, no measured gain**. This follows the owner's request to reconsider
placement after the two negative studies. It is not a frozen execution protocol.

Execution update: the owner subsequently authorized implementation and testing.
The [prospective execution plan](evidence-attention-protocol.md) and
[dated report](../reports/2026-09-21-evidence-attention/README.md) record current
status. The original proposal below is preserved; it is not a result claim.

## Documentation plan

Record the hypothesis, actual tensor location, competing explanations, controls,
and decision gates here; link the notebook, register, related-work ledger, earlier
architecture review, and manuscript. Preserve historical reports and scores.
Validate the documentation links and diff. This change has no runtime behavior,
new paid requests, cloud resources, or model-weight changes.

## What the evidence motivates

R10 selected whole intermediate steps; R13 applied bounded preferences to next-token
probabilities. Neither demonstrated a useful final-answer improvement. They used
different tasks and generation contracts, so their scores do not rank insertion
points against each other. See the [R10 report](../reports/2026-09-20-generated-answer-study/README.md)
and [R13 report](../reports/2026-09-21-structured-study/README.md).

R13's highest Jev support score identified a supported claim in all 1,179 mixed
candidate sets. Supported accepted claims increased from 58.83% to 61.89%, while
final accuracy changed from 37% staged to 36% Jev. Direct Granite scored 42.67%.
The intervals do not establish a general harmful effect, and the larger change
occurred when staging was introduced. These observations motivate separating
evidence use from claim truth; they do not diagnose an attention defect.

Our hypothesis is that **query-specific emphasis on source evidence inside selected
attention heads may help Granite use relevant information while generating**.
The first target is grounded question answering with distractors, followed by
tests requiring several linked facts. Arithmetic and universal reasoning gains
are not assumed. Relevance judgment is a new Jev task requiring its own evaluation;
R13's claim-support scores do not validate it.

## Mechanism and ownership

The proposed Python runtime divides the existing evidence into complete spans,
retains every span in Granite's context, and maps each span to its exact token
positions. Jev receives the public question and source spans, and returns a
focused relevance judgment for each span. It receives no reference answer,
oracle dependency path, candidate final labels, or hidden tensor. The rubric must
allow both supporting and contradicting evidence and relevant bridge facts.

```text
Question + complete source evidence
       |                         |
       |                         v
       |                 Jev: relevance per span
       |                         |
       v                         v
Granite embeddings       controller maps span IDs
       |                 to bounded token biases
       v                         |
Selected Transformer attention head
  QK scores + causal mask <------+   <-- new intervention
       |
  softmax -> weighted sum of V -> output projection
       |
  residual path + remaining model computation
       |
Granite output head -> Granite-generated tokens
```

This is an internal attention intervention controlled by an external text model,
not neural fusion or an exchange of Jev/Granite hidden representations. Jev stays
outside the GPU forward call; its validated judgments become a local tensor.
Neither an HTTP request nor a fresh Jev evaluation is needed at every layer/token.

For a selected layer/head, a candidate control law is:

```text
S = the implementation's scaled QK scores + existing causal/padding mask
b[j] = bounded emphasis assigned to the source span containing key token j
A = softmax(S + b)
head_output = A @ V
```

The mapping from a span judgment to `b` is an explicit heuristic to calibrate on
development data, not a claim that Jev probabilities are attention probabilities.
A bounded positive emphasis can leave other tokens at zero additive bias; no
source is deleted or assigned a new hard mask. Softmax still reduces other tokens'
relative attention, so preserving their text does not guarantee they remain used.
No relevance contrast means zero intervention, not uniform evidence amplification.

This differs from R13's vocabulary bias: the affected coordinates are **source-token
positions**, before value aggregation inside a block, rather than candidate output
tokens after the model head. A scalar broadcast across every hidden dimension or
every attention head would have no such span alignment and is not proposed.

Layer/head IDs, strength, span granularity and intervention schedule are unknown.
Select them by causal output tests on development cases, not by attractive attention
plots or copying another model's heads. Granite's audited implementation has 40
attention layers, 16 query heads and four KV heads; shared KV heads must not be
mistaken for independent query heads. Preserve RoPE positions and causal masks.

First isolate a fixed question/evidence map, computed once and reused during
generation. Dynamic refresh from Granite's accepted textual prefix is a separate
ablation if that simpler mechanism works; generated text remains tentative, never
new source evidence. If biases change, existing deeper-layer KV states can reflect
the old policy. Recompute the exact prefix as the initial correctness reference,
and specify cache semantics before optimizing incremental serving.

The final answer still consists of Granite-generated tokens. A policy applying
attention steering during final generation must be named explicitly: that final
is generator-owned but **attention-guided**, not the unassisted final policy of
R13. A reasoning-only treatment would disable steering before final generation
and rebuild state under its declared policy. These are separate experimental arms,
not interchangeable descriptions. No Jev final classifier is used in either.

## Why this is worth testing, and what could defeat it

Evidence spans offer a concrete connection between Jev's text judgments and
Granite's internal computation without learning a shared hidden representation.
The proposal removes the need to invent and approve a short claim before useful
information can influence generation. It does not assume that deeper placement
automatically improves reasoning or that attention maps explain reasoning.

Relevant spans may be missed, especially when an apparently unrelated premise is
needed several hops later. Negation, conflicting facts, lexical distractors, long
spans and answer position can all bias selection. Jev and Granite might both lack
the necessary inference capability. Even perfect evidence identification may not
help, and attention intervention can impair syntax or suppress required context.
The selected task distribution could also favor this design without generalizing.

No original Granite training corpus or full retraining is required for this
proposal. Independently labeled development examples are still needed for span
assessment and causal head/strength selection. Frozen weights do not mean no
calibration data or no experimental tuning.

## Decision gates before another full study

1. **Mechanical equivalence:** a zero-bias implementation must match the original
   attention path within a declared numerical tolerance and reproduce deterministic
   token choices on the fixtures. Test causal masking, exact span offsets including
   Unicode/repeated text, GQA indexing, request isolation, cancellation, and stale
   scores. A successful hook is not an accuracy result.
2. **Evidence-use diagnostic:** on fresh development problems with independently
   annotated relevant spans, compare unmodified Granite with oracle-span attention
   steering over a bounded, recorded head/strength search. The oracle condition
   contains privileged information and is never reported as Jev performance or a
   guaranteed upper bound. If the proposed intervention cannot help even with
   correct spans within this search, stop this design before adding paid Jev.
3. **Jev relevance assessment:** on separate annotated cases, measure necessary-span
   recall, distractor preference, contradictions and missing-evidence behavior.
   Score bridge-fact coverage separately. Do not use Jev as its own grader.
4. **Controlled development comparison:** use the same complete context, prompts,
   generator, decoding settings and final contract for baseline, zero bias,
   Jev-span bias, shuffled span scores, and a simple lexical relevance baseline.
   Include static span emphasis and random-head controls to separate semantics
   from generic perturbation. Compare against prompt highlighting using the same
   Jev judgments as a separately disclosed prompt-changing arm; an internal hook
   must justify itself against a simpler way to communicate the same information.
5. **Freeze a new test:** predeclare sample size, selected heads/strength/schedule,
   primary contrasts, useful-effect criterion, multiple-comparison adjustment,
   independent grader, data/source hashes and remaining budget before live test
   inference. Keep all failures and exposed prior tests out of the new test set.
   Measure final accuracy, clean-context regressions, necessary-evidence use,
   latency, tokens, repeated prefill and every API cost. A positive result is not
   required for reporting; it is required for claiming an improvement.

These gates are a design plan, not an executable preregistration. No new sample
size, tuned parameters, cost forecast or experiment result has been established.
First answer whether this intervention has useful causal headroom, then whether
Jev supplies the necessary signal. A negative first diagnostic only rejects the
tested mechanism/range, not every possible attention intervention.

## Alternatives and sources

Prompt highlighting is a necessary simpler control. Jev-triggered residual/head
direction steering is another internal approach, but requires a separately
validated activation direction; a Jev scalar does not supply that direction.
Cross-attention to Jev representations would require an interface and alignment
that the inspected public API does not provide.

Primary sources checked on 2026-09-21:

- Zhang et al., [PASTA, ICLR 2024](https://proceedings.iclr.cc/paper_files/paper/2024/file/b99d6cc40b05809c3d84b57a165448cd-Paper-Conference.pdf),
  Sections 3.1, 3.2 and 5.3: reweights attention to highlighted spans with frozen
  weights and profiles heads on development examples. Its all-head ablation
  illustrates why more intervention need not help. Those experiments do not
  validate Jev scores or Granite heads. This proposal adapts an established
  mechanism family; it is not an invention of attention steering.
- [TypeSafe System One](https://docs.typesafe.ai/concepts/system-one) and
  [HTTP API](https://docs.typesafe.ai/api): text/structured state and typed
  judgments, with no documented hidden-tensor or gradient interface on these pages.
- [TypeSafe reranking cookbook](https://docs.typesafe.ai/cookbooks/rerank_typesafe):
  per-candidate judgments can drive relevance ranking; its task-specific example
  is not validation of this evidence-attention proposal.
- [Jev 1.13 limitations](https://docs.typesafe.ai/model-jaggedness/jev-1.13):
  indirect reasoning and irrelevant context are documented difficulties. They
  motivate bridge-fact and distractor checks, not an assumed solution.

Markdown/index retrieval failed through the browser tool; the corresponding
official HTML pages and the primary conference PDF were accessible. This was a
targeted method review, not an exhaustive novelty search. All earlier results and
the [prior architecture decision](architecture-reassessment.md) remain preserved.
