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
These heads were inherited from source-attention studies, not independently
selected as instruction-following heads. A positive or negative instruction
result applies to this finite mechanism and strength search.

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

The bias changes attention probabilities, not the meaning of a value vector. For
one affected query/head with original attention mass `m` on the selected keys,
adding bias `b` changes that mass to `exp(b) * m / (1 - m + exp(b) * m)`, holding
the incoming logits fixed. Thus strengths 2 and 5 multiply selected-versus-other
attention odds by about 7.39 and 148.41. Downstream layers still combine their
value vectors with the residual stream. More attention to an abstention clause
does not guarantee following it, and an erroneous sufficiency judgment can steer
an answerable input toward abstention.

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
Native uses the same instrumented serial runtime and prompt contract; its timings
are not a benchmark of optimized default Granite serving.

The learned gate executes first per question; these calls are actual physical
attempts. Other controls reuse exact receipts, so their standalone call counts
are logical usage and uncached elapsed times are reconstructed estimates. Every
arm uses one retained prefill. Comparisons of different answers also have different
decode lengths; equal token ceilings are not equal computation.

Two [supplemental controls](../../research/benefit-sufficiency-controls.md) were
registered during fitting, before calibration selection, held-out generation or
quality inspection. Each adds 608 generations on the same test inputs. The static
control always emphasizes the existing abstention clause, using the selected
instruction strength and no Jev. Its canned callback is local computation, not a
provider request. The shuffled control keeps each input's relevance scores but
uses another input's sufficiency probability, through one deterministic within-domain
permutation. It reuses receipts and makes no additional paid requests. Dual minus
each control is reported separately with exploratory 95% intervals; the six main
primary comparisons are unchanged. A single permutation and the dual-selected
strength do not constitute a search for the strongest static control.

The main and supplemental schedules contain 6,096 and 1,216 outcomes respectively.
Both finish before held-out quality inspection. The scientific audit reconstructs
the frozen prompts, source and instruction token maps, decisions, receipt bindings,
token provenance, cache lengths, work and grades; public replay repeats that audit
without generating new answers or contacting Jev. Reconstruction is a mechanical
consistency check, not independent human assessment of answer meaning.

## What the comparisons establish

For each domain, let `N_i` be native quality, `D_i` dual-guided quality, and `g_i`
the frozen benefit gate's call decision. Conditional generation is checked to
match the exact dual token sequence when `g_i = 1` and native sequence otherwise.
The primary routing statistic is

```text
mean(g_i * (D_i - N_i)) - mean(g_i) * mean(D_i - N_i)
```

This measures whether calls select larger gains than an expected random allocation
with that domain's actual call fraction. Saving calls alone does not make this
statistic positive. The separately executed random arm uses the calibration call
fraction and is a different, descriptive comparator. The 50% ceiling applies to
calibration selection, not a guaranteed runtime quota on unseen data.

The other primary comparison is dual minus relevance. This tests the complete
sufficiency-dependent policy, including withholding relevance steering at middle
or low probabilities; it does not isolate only the instruction-bias mechanism.
The sufficiency-only and static/shuffled controls help interpret that distinction.

Ten thousand paired cluster-bootstrap resamples preserve authored light/heavy
world pairs, Hotpot questions and SQuAD article membership. Each of six main
intervals has 99.1667% nominal coverage, giving a Bonferroni-adjusted nominal 95%
family level. Finite-sample percentile bootstrap coverage is approximate. Ordinary
95% secondary and supplemental intervals remain exploratory, and descriptive
answerability groups do not introduce new significance tests. Different domain
metrics are not pooled into a headline accuracy score.
The main adjustment covers R19's six registered comparisons, not all questions
asked across the project's successive experiments. Earlier positive, negative and
interrupted studies remain part of the published record.

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

The [R19 source comparison](../../research/benefit-sufficiency-related-work.md)
also covers RouteLLM's learned quality/cost routing. Predicting comparative
usefulness is an established idea; the question here is the effectiveness of
this particular internal intervention and dispatch mechanism.
