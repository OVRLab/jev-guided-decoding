# R16 mechanism and evaluation contracts

Execution is in progress; this page describes the frozen method, not results.
The [original plan](../../research/adaptive-attention-protocol.md),
[FP32 amendment](../../research/adaptive-attention-fp32-amendment.md),
[frozen manifest](../../research/protocols/adaptive-attention-fp32/manifest.json)
and [16,120-job schedule](../../research/protocols/adaptive-attention-fp32/schedule.json)
were committed before benchmark inference.

## What remains inside Granite

```text
Question + all source records -----------> Granite token embeddings
             |
             +---> Jev per-source relevance (one hosted request)
                            |
                    source-token weights
                            |
                per-head strength vector
                            v
Granite selected attention heads: QK scores + causal mask + source-key bias
                            |
                         softmax
                            |
                 value aggregation + remaining layers
                            |
                    Granite vocabulary logits
                            |
                  Granite-generated tokens
```

Twelve candidate query heads span nine of Granite's 40 attention layers, using
R15's fixed head identities. Development can set a head's strength to zero, disable
an entire selected layer group, or give heads different strengths. Bias is applied
at query positions after the evidence block, toward key tokens belonging to
relevant sources. The all-equal relevance convention remains no intervention.
Zero strength removes only the extra steering bias: the original attention head
continues operating. All of Granite's heads and layers remain present. References
to head/layer deletion in the policy search mean deletion from the steering set,
not removal or zeroing of the model's attention computation.
All original evidence stays in the prompt. This is source reweighting, not a new
attention layer, neural fusion, a trained adapter or a modified checkpoint.

## Dynamic guidance

```text
Initial Jev relevance --> Granite reasoning chunk 1 (up to 24 tokens)
                                      |
                Question + original sources + generated reasoning
                                      |
                              refresh Jev relevance
                                      |
                     Granite reasoning chunk 2 (up to 24 tokens)
                                      |
                              refresh Jev relevance
                                      |
                     Granite reasoning chunk 3 (up to 24 tokens)
                                      |
                       controller-supplied final-answer cue
                                      |
                       Granite final answer (up to 32 tokens)
```

Each source is judged in the same batched request. Generated reasoning is explicitly
fallible; the original sources remain authoritative. Jev supplies probabilities,
not a selected final answer. No branch rejection, candidate reranking or final
Jev classifier is used. Every semantic token is selected by Granite's logits.

Newline can end a reasoning chunk; EOS ends the reasoning phase early. Controller
framing tokens and exact generated token IDs have separate trace records. The final
phase has a reserved token budget even when reasoning ended early. No closing-frame
syntax is required. This still uses a bounded experimental generation protocol; it
is not an unrestricted chat deployment or evidence of accessing hidden thoughts.

The cache belongs to one request. New relevance changes subsequent computation,
including processing the last generated token when forming the next token's
logits. Previously computed higher-layer cached representations remain unchanged.
No HTTP call happens inside a layer. Static guidance, native generation and dynamic
controls all use the same cache semantics and framing within the staged panel.

## What was relaxed

| Contract | Vocabulary restriction | Uncertainty instruction | Generation |
| --- | --- | --- | --- |
| Constrained reference | Seven one-token answers including UNKNOWN | Explicit UNKNOWN | One token |
| Open explicit | None | State insufficient evidence in own words | Up to 32 tokens |
| Open neutral | None | No special uncertainty instruction | Up to 32 tokens |
| Staged open | None | State insufficient evidence in own words | Three reasoning chunks, then up to 32 final tokens |

The open panels contain no colour answer menu and no required UNKNOWN token.
Prompts, budgets, evidence and grading are matched **within** each panel. Across
panels, output instructions and computation intentionally differ; accuracy changes
cannot automatically be attributed solely to removing the vocabulary constraint.
Token limits remain necessary resource bounds. Selection has no subgroup harm gate;
all subgroup gains/regressions are reported rather than suppressing a candidate.

## Development and transfer

Ninety-six new heavy-context worlds cover depths 1–6, half missing a required link.
We first measure individual head/layer deletion and uniform strength changes, then
perform one deterministic coordinate pass over the twelve head strengths, then
select a relevance mapping. Ties use reference log probability, total strength and
policy ID. The finite search is neither a global optimum nor exhaustive exploration.
Policy selection uses the constrained development contract only. Transfer to free
text and HotpotQA therefore tests that policy without task-specific retuning.

Three hundred new worlds each supply light and heavy distraction. Their first 120
worlds also receive staged evaluation and two relation renderings: paraphrased
containment and dependencies ending at a colour-coded terminal. References are
reconstructed from visible source statements. Changed wording and dependencies
are authored transfer tests, not independent real-world benchmarks.

Two hundred [HotpotQA](https://hotpotqa.github.io/) distractor questions provide
external document QA. Complete ten-paragraph contexts are selected by a seeded ID
shuffle and a maximum 2,048-token staged prompt, independently of answers or
supporting-fact annotations. Twelve other eligible questions are reserved for
mechanics. This length-filtered subset is not the full official benchmark and
may be easier than longer questions. Potential pretraining exposure is unknown.
See the [data notice](../../research/protocols/adaptive-attention-v1/HotpotQA-NOTICE.md).

## Controls, scoring and uncertainty

Constrained answers compare native, R15, tuned, shuffled tuned, lexical tuned and
zero intervention. Open direct panels omit the redundant zero arm. Staged panels
compare native, R15-static, tuned-static, dynamic Jev, shuffled dynamic Jev and
lexical dynamic attention. The latter controls separate relevance quality from
extra reasoning or a change in the attention mask. Different arm trajectories can
use different actual token counts; equal ceilings are not equal computation.

A conservative preregistered parser recognizes a single asserted colour or natural
abstention in synthetic final text. Negated/ambiguous colours, mixed answers and
unrecognized wording fail. Parser coverage and strict normalized EM are reported
separately. The parser is not a semantic judge and may undercount valid paraphrases.
HotpotQA uses the authors' answer normalization, exact match and token F1 on the
complete final text. No gold-assisted substring extraction or Jev self-grading is
used. F1 is a lexical answer metric, not proof of grounded reasoning.

Ten thousand bootstrap resamples use the world/question as the unit. The three
primary contrasts use individual 98.333% intervals: tuned minus R15 constrained
accuracy; dynamic minus tuned-static staged accuracy on original worlds; tuned
minus native direct HotpotQA F1. All other intervals are exploratory 95% intervals.
Each question receives its own conclusion; there is no all-controls success gate.

The separately [registered factorial supplement](../../research/adaptive-attention-factorial.md)
isolates the three changes in the selected policy: uniform active-head strength,
disabling head (21,13), and relevance threshold. It runs the six missing corners
of a 2×2×2 combination on the same 600 constrained contexts, replaying existing
receipts without API calls. R15 and tuned corners reuse the original outputs.
Registration occurred after the main test began and before consulting aggregate
held-out quality, so all factorial comparisons remain explicitly exploratory.
They are not a new independent test set. Their deterministic execution order is
acceptable for these greedy quality comparisons but does not establish randomized
timing comparisons between the six new arms.

## Precision, accounting and failures

All benchmark arms use FP32. The initial BF16 admission failed before any benchmark
or Jev call; the [registered diagnostic](../../research/adaptive-attention-cache-diagnostic.md)
and prospective precision amendment are retained. R15 is rerun in FP32 for fair
within-study comparisons. Historical BF16 aggregate scores are not direct controls.

Actual model forwards, prompt/processed/generated tokens, model seconds and paid
request receipts are retained. Receipts are reused only for identical payloads.
Deployment latency estimates must charge each arm for its needed hosted calls even
when experimental receipt sharing avoids duplicate billing. Timing is serial
reference execution, not concurrent serving throughput. Colocation is unmeasured.

Unknown paid usage remains charged at the full reservation; failed payloads are
memoized and never replayed. Failed outcomes remain in denominators. The journal
will not rerun a started unfinished model job. Source, data, policy and schedule
freezes are checked before resumption. No quality-driven exclusion or retry is
permitted. Independent auditing reconstructs prompt spans, exact tokens, dynamic
state binding, masks, receipts, grades, development selection and statistics.
