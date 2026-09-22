# R19: two decisions at one internal boundary

This is a prospective method description. See the
[registered protocol](../../research/benefit-sufficiency-plan.md) for the evaluation.
No quality result is implied by the architecture diagram.

```text
Question + original evidence + unchanged system instruction
                           |
                Granite layers 0 through 18
                           |
                 Native attention observation
                           |
            Local expected-benefit predictor (Python)
                   /                       \
                 skip                     call
                  |                         |
                  |             Hosted Jev, one joint request
                  |             + source relevance probabilities
                  |             + evidence-sufficiency probability
                  |                         |
                  |               Fixed intervention policy
                  |           /             |             \
                  |      sufficient      uncertain     insufficient
                  |      source bias      no bias     instruction bias
                  |           \             |             /
                  +-------------------------+
                                            |
                      Continue the SAME prefill before layer 19
                                            |
                   Selected heads in layers 19 through 38
                                            |
                     Granite chooses every final output token
```

Layer numbers are zero based. The exact eleven heads are inherited from R18:
(19,6), (19,11), (19,15), (20,11), (21,14), (23,8), (29,10), (30,4), (34,4),
(37,14), (38,11). Layer 19 is the first existing treatment layer, not a newly
established optimal insertion point. No bias is applied to earlier layers.

The local controller observes one last-prompt-query attention row before any
intervention. Its six inputs are evidence mass, source entropy, head disagreement,
log(1 + source count), log(1 + prompt tokens), and maximum question/source lexical
Jaccard. A ridge model with degree-two feature products predicts the change in
quality from applying dual guidance. Fit targets are paired guided-minus-native
scores; fit-only normalization and coefficients remain frozen during calibration
and test. No family label, expected answer, missing-evidence label, generated pilot
or Jev output is available to the pre-call decision.

Jev receives only the question and source records. Independent relevance and
sufficiency questions are batched; neither question sees another question's answer.
This uses the existing typed API, not a Jev hidden-vector interface. The service
is hosted; a model colocated with Granite is not measured.

When sufficient probability is at least 0.65, source relevance above 0.65 receives
additive attention-logit bias 5 under the inherited rule. Uniform source choices
are a no-op. When sufficient probability is at most 0.35, the existing system
clause about explaining missing evidence receives bias 2 or 5, selected using
calibration only. Otherwise attention remains native. Instruction and evidence
keys are disjoint, bound to the unchanged original tokenized prompt; affected
queries begin at the question and continue through generated tokens. Bias is added
at the same selected heads and continues through cached decoding. There is no
special UNKNOWN token, output substitution or restricted vocabulary.

A failed request is counted and leaves native computation unchanged. An unasked
judgment is `None`, never a fabricated probability. The serial runtime owns its
hooks/cache until its model thread drains, including repeated cancellation. Lower
layer cache signatures cannot change while waiting for the hosted callback.

## Controls and attribution

All seven test arms share prompts, model revision, precision, greedy decoding,
32-token ceiling and graders. Relevance-only consumes the relevance part of the
same joint receipt. Sufficiency-only emphasizes the abstention instruction only
when evidence is judged insufficient. Dual-always combines both branches. Three
conditional arms apply that same frozen dual treatment: expected benefit, random,
and the unchanged R18 threshold. Native makes no provider request.

The learned gate executes first per question; these calls are actual physical
attempts. Other controls reuse exact receipts, so their standalone call counts
are logical usage and uncached elapsed times are reconstructed estimates. Every
arm uses one retained prefill. Comparisons of different answers also have different
decode lengths; equal token ceilings are not equal computation.

## Relationship to prior work

Separating relevance from whether a document contains an answer is already shown
in TypeSafe's [semantic-find cookbook](https://docs.typesafe.ai/cookbooks/semantic_find).
Frozen-weight attention steering is established by
[AutoPASTA](https://arxiv.org/abs/2409.10790), while
[Lookback Lens](https://aclanthology.org/2024.emnlp-main.84/) uses attention features
to guide decoding. Our experiment investigates the particular combination of
benefit prediction, external sufficiency, and internal instruction/source steering
within one prefill. It does not establish historical priority or superiority over
those methods; they are not reproduced comparison arms here.
