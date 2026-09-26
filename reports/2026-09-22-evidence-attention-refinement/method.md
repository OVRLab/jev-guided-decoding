# R15 mechanism and development selection

The original [prospective protocol](../../research/evidence-attention-v2-protocol.md)
was frozen before inference. Operational changes are separately registered in the
[transport recovery](../../research/evidence-attention-v2-recovery.md) and
[checkpoint repair](../../research/evidence-attention-v2-checkpoint-repair.md).
The later [service continuation](../../research/evidence-attention-v2-service-continuation.md)
and [freeze-comparison repair](../../research/evidence-attention-v2-freeze-repair.md)
were registered after testing began; that operational deviation is disclosed.
All model weights, scientific candidate configurations and test cohorts remained
unchanged. The selected configuration was frozen before held-out inference.

## Exact placement

```text
Question + ALL source records
        |                              |
        |                              v
        |                   Jev source relevance (one API call)
        |                              |
        |                     probability for each source
        |                              |
        |                   threshold > 0.5 -> source-token map
        v                              |
Granite embeddings                    |
        |                              |
40-layer Granite forward              |
        |                              |
12 selected query heads <-------------+
across 9 attention layers:
  (QK scores + causal mask + source-key bias)
        |
     softmax -> weighted values -> projection
        |
Remaining Granite computation -> output head
        |
Granite chooses ONE of: red blue green white black yellow UNKNOWN
```

Layer/head indices are zero based:

```text
(34,4), (38,11), (37,14), (30,4), (23,8), (19,6),
(21,13), (19,11), (19,15), (21,14), (29,10), (20,11)
```

At query positions after the complete evidence block, add ln(16) to evidence-key
positions belonging to sources with Jev relevance strictly greater than 0.5, in
those heads only. Other source keys receive zero extra bias. All-equal mapped scores
produce no intervention, following the unchanged hook convention. The requested
strength is 2.772588722239781; applied masks have ordinary BF16 quantization.

The previous R14 policy used the first eight heads, ln(8), and a continuous
`max(0, 2r-1)` multiplier. The new policy changes head count, strength and score
mapping; it retains R14's query scope. Its `scope_only` ablation therefore equals
R14 by design and remains in the schedule as an identity control.

Jev receives text questions/source records, with no reference answer, oracle
annotations, proposed final label, logits or hidden tensors. It is not asked to
choose UNKNOWN. Granite owns that semantic decision. One hosted call supplies
static relevance before the forward pass; no network request happens inside an
attention layer and there is no refresh during intermediate reasoning. The model
checkpoint remains unchanged; this is inference code, not a new trained checkpoint.

## Finite development search

Ninety configurations cross top-head count 1/2/4/8/12, strength ln(4)/ln(8)/ln(16),
soft/hard50/hard80 relevance mapping, and all post-evidence queries versus only the
last input position. Head ranking is inherited from the exposed R14 profiling
cohort. R15 calibrates the deployed Jev mapping directly on fresh development
worlds, using one shared receipt per context. All facts remain visible to Granite.

On 96 development worlds, each with light and heavy distraction, the selected
`h12-ln16-hard50-question` policy scores **127/192 (66.15%)**, versus native
**74/192 (38.54%)** and the frozen R14 policy **86/192 (44.79%)**. One provider-failed
context counts incorrect for every guided policy, including R14; native still ran.
The log-probability tie break uses the same 191 successful guided contexts. These
are optimistic selection results, not independent evidence of improvement.

The chosen configuration satisfies all three development harm floors: answerable,
missing-link and light-context accuracy cannot fall more than three percentage
points relative to R14. Selection ranks eligible policies by accuracy, reference
log probability, fewer heads, lower strength, mapping and scope. No test output
informed the choice. Selecting the largest head count/strength in this finite grid
does not establish that the optimum has been found beyond its boundaries.

## Evaluation contract

The primary test contains 600 new worlds (depths 1/2/3); the separate challenge has
120 new worlds (depths 4/5/6), each with two context variants. Half lack the final
link and require UNKNOWN, so a constant-UNKNOWN reference scores 50%. All seven
labels are always available to Granite. This is constrained one-token containment
QA, not unrestricted chat or general reasoning.

Twelve arms compare native, frozen R14, selected R15, shuffled scores, lexical
relevance, Jev prompt highlighting, privileged oracle, zero intervention and four
single-factor ablations. All attention arms share identical model inputs; prompt
highlighting changes markers/tokenization but preserves every source. Deterministic
arm-order rotation, source permutations and exact prompts are recorded.

The two primary contrasts are R15 minus native and R15 minus R14, with 10,000 paired
world-bootstrap draws and individual 97.5% intervals (nominal 95% family coverage).
The world averages its two contexts. Advancement requires at least +2 percentage
points over R14 and both interval lower bounds above zero. Other controls,
ablations and the challenge are exploratory; their displayed 95% intervals are
unadjusted. The original R14 all-controls criterion and results stay unchanged.
