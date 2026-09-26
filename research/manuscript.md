# Separating Repair Selection from Internal Feedback in a Small Language Model

Working research manuscript, updated 26 September 2026. Authors, affiliations and
contribution statements await owner/coauthor decisions. Not submitted or peer
reviewed. The earlier [chronological manuscript notebook](paper-draft.md) and
[study register](study-register.md) preserve the complete exploration, including
negative results and corrections. This manuscript narrows the research question;
it does not replace the project's broader, unachieved objective.

## Abstract

External verification can select answers for revision or supply information that
changes the revision itself. We study these roles in frozen IBM Granite 4.0-1B
with TypeSafe Jev, which returns typed judgments while Granite generates every
answer token. A 262,144-parameter branch acts after decoder block 19 during repair.
An initial complete evaluation improves strict IFBench from 55/300 to 71/300 and
GPQA Diamond from 37/198 to 54/198, but shuffled feedback recovers most gains.
A separate 539-case eligible IFEval study instead falls from 75.70% to 70.32%.
Two authored tracking studies show narrower native improvements with preservation,
without establishing the value of precise field-score localization.

A subsequent matched-memory study trains twelve adapters on 512 worlds and selects
epochs on 64 development worlds before evaluating 256 fresh same-template worlds.
Scalar Jev repair improves all-three-answer accuracy from 30.08% to 46.29%
(+16.21 points; registered 98.75% interval [10.94,21.68]) and exceeds its donor
feedback control by 8.40 points [3.71,13.48]. Contextual and embedding scalar repair
have identical complete-world correctness; structured contextual feedback performs
worse. A separately constant-trained, Jev-free recipe reaches 47.85%, while
repairing more native failures and damaging 7/4 native passes across the two seeds;
live scalar repair damages none. These findings distinguish feedback dependence
within a trained model from superiority over an independently trained alternative.
They motivate public transfer and preservation analysis, without establishing
broad reasoning gains, a novel general architecture or larger-model superiority.

## 1. Research question

A verifier can recognize an error without enabling a generator to correct it.
Conversely, a trained second pass may improve an answer even if the external
judgment contributes little useful information. These possibilities require
separate comparisons: improvement over the original generator establishes a
system-level difference; improvement over equally equipped controls is needed
to attribute that difference to a particular verifier input.

Our question is whether Jev contributes useful inference-time information to a
small generator through (a) selecting which answers receive repair or (b)
modulating the repair computation. We study one fixed checkpoint and insertion
point. The contribution sought is a controlled empirical account of these roles,
not the invention of verification, refinement, low-rank intervention or routing.
The ambitious goal of outperforming named larger models across a broad benchmark
suite motivates the project but is not supported by the present evidence.

## 2. Relation to previous work

Zhang et al.'s [SCORE](https://arxiv.org/abs/2404.17140) already separates verification
from refinement and evaluates external and intrinsic verifiers for smaller language
models. We extend the experimental question to a scalar signal entering a fixed
internal adapter. The conceptual separation itself is not new.
[Self-Refine](https://arxiv.org/abs/2303.17651) studies iterative textual feedback;
our second-pass control does not reproduce its full procedure.
[ReFT](https://arxiv.org/abs/2404.03592) establishes learned representation
interventions with frozen backbones. [SCoRe](https://arxiv.org/abs/2409.12917)
studies correction training with reinforcement learning; our small supervised
adapter does not test that approach.

A subsequent [targeted literature update](contextual-memory-related-work.md#expanded-search-while-r31-runs-26-september-2026),
made while R31 was running, identifies closer precedents. [PoPE](https://arxiv.org/html/2607.12962v1)
compares feedback content with matched placebos in frozen small code models.
[Latent Reward Steering](https://arxiv.org/html/2606.00726v3) applies selective
reward-gradient corrections to latent states, while [CRN v2](https://arxiv.org/html/2609.16145v1)
studies a frozen backbone with a trained logit correction and preservation loss.
These works further restrict our contribution to the particular mechanism and
controlled empirical findings. We have not reproduced their methods, and their
results are not directly comparable with our task scores.

[RouteLLM](https://arxiv.org/abs/2406.18665) addresses model routing under quality
and cost trade-offs. Our allocation is between retaining an answer and running
a second pass through the same generator. [IFEval](https://arxiv.org/abs/2311.07911)
and [IFBench](https://arxiv.org/abs/2507.02833) provide independently verifiable
instruction constraints, which measure compliance rather than comprehensive
semantic quality. The [prior-art comparison](routing-feedback-related-work.md)
records the review depth and relevant differences. No direct empirical comparison
with these published methods has been performed.

A later literature check also identifies [ATLAS](https://arxiv.org/html/2601.03093v4),
which adaptively selects internal steering using latent verification and includes
a text-verifier variant. Verifier-guided internal steering is therefore not a
novelty claim for this project. The [contextual-memory comparison](contextual-memory-related-work.md)
records the narrower implementation differences and review depth; no empirical
ATLAS comparison has been performed.

## 3. Method

### 3.1 Generator, verifier and token ownership

The generator is dense, all-attention IBM Granite 4.0-1B, pinned to revision
`6a7381ba1f54d684ff508d991aeb7dc580157103`. Its model family implementation has
hybrid support, but the selected checkpoint is not a mixed attention/Mamba model.
The checkpoint contains 1,631,750,144 original parameters; the product name is
not an exact parameter count. Those original weights remain frozen.

Granite first produces an ordinary full-vocabulary response. Jev 1.13.0 receives
only the user problem and this response and returns the probability that the
response satisfies the requested judgment. For instruction tasks the question
asks whether all content and explicit formatting requirements are fulfilled.
The benchmark checker, constraint metadata and reference answers are absent
from that request. A probability is a fallible judgment, not a correctness label.

If repair is selected, the next input preserves the exact original prompt and
generated token IDs and appends a request to check and correct the answer. Every
repair uses a new cache. There is no forced UNKNOWN option, restricted answer
vocabulary, or Jev-generated final label in the scored system.

```text
User prompt --> Frozen Granite --> Original generated answer
                                      |             |
                                      |             +--> Native log-probability
                                      v                  or random control
                                Jev judgment p                |
                                      |                       |
                             Select answers to repair <-------+
                                      |
             +------------------------+------------------------+
             | retain                                          | repair
             v                                                 v
     Exact original answer                   Prompt + exact original answer
                                              + common repair instruction
                                                           |
                                               Frozen blocks 0 through 19
                                                           |
                                            h' = h + g * trained residual(h)
                                                           |
                                              Frozen blocks 20 through 39
                                                           |
                                              Granite vocabulary head
                                                           |
                                              Generated repair answer
```

The experiment varies selection and the scalar g. Jev is called after the native
answer, not once per layer or token. Its scalar is held fixed while the repair is
generated; it does not provide hidden states, gradients, a textual correction or
missing factual knowledge.

### 3.2 Internal intervention and earlier training

For hidden vector h, define s as its root-mean-square magnitude with a small
positive floor. The intervention is:

    residual(h) = 0.5 s tanh(U tanh(D(h / s)))
    h' = h + g residual(h)

D and U are rank-64, bias-free matrices with 262,144 total parameters. Live
feedback uses g = 1 - p. A zero gate is exactly the identity. The branch acts
after zero-indexed block 19 at the last prompt position predicting the first
repair token and subsequent generated positions. Earlier draft positions are
not retroactively modified.

The [completed R25 study](../reports/2026-09-23-gated-repair/README.md) trained
live- and constant-gated adapters using 384 examples from GSM8K and ARC-Challenge,
64 development examples and two training seeds. Only the new matrices were
trained; source solutions supplied training targets. Final completed training
and evaluation used FP32 after a preserved BF16 admission failure. R27 and R28
reuse the live seed-2501 epoch-2 checkpoint selected on that development set.
They do not train on IFBench or IFEval.

Controls using that checkpoint with fixed feedback are **Jev-free at inference**
when their selector also avoids Jev. They are not Jev-free training controls,
because the shared adapter was originally trained with Jev judgments. The older,
separately trained constant adapter answers a different training comparison.

## 4. Completed benchmark evidence: R27

The following are complete denominators under the registered OVRLab generation
profiles, not claims to reproduce every official leaderboard recipe. Original,
guided and all listed 1B controls are complete. The larger Granite profile also
finished every scheduled case, although many responses reached its token limit
without finishing the thinking segment.

| System | GPQA Diamond /198 | IFBench strict /300 | AIME 2026 /30 |
| --- | ---: | ---: | ---: |
| Original Granite 4.0-1B | 37 (18.69%) | 55 (18.33%) | 0 |
| Granite–Jev | 54 (27.27%) | 71 (23.67%) | 0 |
| Jev-free self-refinement of every case | 33 (16.67%) | 59 (19.67%) | 0 |
| Jev-routed blind repair | 36 (18.18%) | 59 (19.67%) | 0 |
| Jev-routed constant-trained adapter | 53 (26.77%) | 59 (19.67%) | 0 |
| Jev-routed live adapter, constant signal | 52 (26.26%) | 60 (20.00%) | 0 |
| Jev-routed inverted signal | 36 (18.18%) | 57 (19.00%) | 0 |
| Jev-routed shuffled signal | 51 (25.76%) | 68 (22.67%) | 0 |
| Granite 4.2-3B, thinking profile | 42 (21.21%) | 178 (59.33%) | 8 (26.67%) |

![R27 IFBench scores and paired differences](figures/routing-paper/r27-instruction-evidence.svg)

Figure 1. Completed R27 instruction-following evidence. Constant and shuffled
signal controls keep Jev routing; the intervals are descriptive.

The guided-minus-original IFBench difference is +5.33 percentage points, with
22 wins, six losses and a descriptive paired 95% interval [2.00, 8.67]. All wins
start from nonempty native answers. Guided-minus-shuffled is only +1.00 point,
with six wins, three losses and interval [-1.00, 3.00]. These unadjusted intervals
are descriptive; they are not a confirmatory multi-benchmark superiority test.

On GPQA the guided gain is +8.59 points, with 32 wins and 15 losses. Unparseable
finals fall from 67 to 16. A post-hoc partition finds 16 wins originating from
unparseable native answers and 16 from parseable wrong answers; all 15 losses end
in parseable wrong answers. Thus the net gain partitions into +16 and +1. This
describes transitions between readout categories, not the correctness of hidden
reasoning. The reference labels are imbalanced: a retrospective always-B output
would score 70/198, above guided 54/198. It was not a preregistered policy or a
separate model run and does not alter the saved grades.

The larger Granite is substantially stronger on IFBench and AIME. Its 140/198
unfinished GPQA thinking responses make the lower GPQA score unsuitable as
evidence of a smaller-model capability victory. Qwen output coverage is incomplete
and prompt-length ordered, so no representative Qwen accuracy is reported.
Seven other planned full benchmark tasks remain incomplete.

The six routed 1B arms all use the same Jev repair decision. Their signal controls
therefore do not establish whether Jev contributes through selection. The
Jev-free self-refinement control repairs every case and has a different repair
budget. This is the attribution gap motivating R28.

Full evidence, token/receipt audits, frozen readouts and uncertainty are in the
[R27 report](../reports/2026-09-25-completed-granite/README.md). The post-hoc
completed-Granite analysis was specified before fresh scoring, after generation
closed with the larger cross-family comparison incomplete; it is not an external
preregistration or completion of the originally planned full suite.

## 5. Prospective attribution study: R28

### 5.1 Cohort and independent scoring

IFEval is pinned to Google Research commit
`e6890f85757dd84e27ca6df2dd30651dafad28e0`. Before generation, its 541 input
prompts were screened against 2,040 unique earlier project prompts: no normalized
exact or five-word-shingle near overlap at Jaccard 0.65 was found. This limited
check does not establish absence of semantic overlap or pretraining exposure.

Metadata admission found that upstream keys 1122 and 1129 use punctuation in the
letter-frequency checker, which substitutes a random alphabetic character.
These two cases are excluded prospectively without changing the upstream grader,
leaving 539 eligible cases. We report the eligible cohort, not an official full
541-case score. All other admitted constraint parameters are fully specified.
The original grader passes 48 upstream tests and 12 constructed strict
pass/fail/empty checks. Language detection is seeded for repeatability.

The primary outcome is original strict prompt-level compliance. Loose prompt-level
and instruction-level compliance are secondary. These checks do not determine
whether an otherwise compliant answer is factually correct or useful.

### 5.2 Equal-count allocation and feedback controls

The fixed checkpoint, prompt contract and 2,048-token ceiling are shared across
conditions. Two deterministic disjoint blocks contain 270 and 269 cases. Each
selector repairs floor(n/2) per block, totaling 269 repairs. Jev chooses the lowest
probabilities of compliance; native confidence chooses the lowest mean log
probability of generated non-EOS tokens; random selection uses a fixed hash seed.
Empty native answers have lowest confidence. Stable hash ordering breaks ties.

A constant-strength repair is collected for every case. Jev-selected cases also
receive live and shuffled-signal repairs. Shuffling is a deterministic cyclic
derangement within each block's selected cases, preserving exactly their signal
distribution and avoiding self-donors. This permits seven policy comparisons:
native, always-constant repair, Jev/constant, confidence/constant, random/constant,
Jev/live and Jev/shuffled. A 100-seed random allocation sensitivity is secondary.

These are policies evaluated from freshly collected deterministic potential
outcomes. Shared responses do not inflate the number of evaluated problems.
The study queries Jev on every native answer and generates counterfactual repairs;
it is not a measurement of skipped API requests or separately deployed latency.
Equal repair counts and ceilings do not imply equal realized token counts or FLOPs.

### 5.3 Analysis and decision criteria

Four primary paired comparisons test Jev/constant versus random/constant and
confidence/constant, then Jev/live versus Jev/constant and Jev/shuffled. We use
20,000 paired bootstrap draws stratified by block, with 98.75% intervals to
account for this family of four. A component meets the registered practical
criterion only if both relevant lower bounds exceed zero, each point estimate
is at least two percentage points, and both blocks agree in direction. The
blocks are consistency checks, not independent trained-model replications. The
bootstrap conditions on the frozen selection and donor assignment; it does not
measure uncertainty from refitting or re-ranking a policy in another cohort.

Unadjusted 95% intervals for native comparisons remain descriptive. Failure to
meet the criterion is not proof of equivalence; this sample may miss small
benefits. We do not tune thresholds or stop early based on correctness scores.
Generation, source, checkpoint, prefix, hook, donor, selection, workload and API
receipt admission precede grading. Missing planned outcomes leave the study
incomplete instead of silently reducing its denominator.

### 5.4 Results

| Policy | Strict prompt success | Loose prompt success | Repairs |
| --- | ---: | ---: | ---: |
| Original Granite | 408/539 (75.70%) | 417/539 (77.37%) | 0 |
| Always repair, constant signal | 360/539 (66.79%) | 369/539 (68.46%) | 539 |
| Jev selection, constant signal | 392/539 (72.73%) | 402/539 (74.58%) | 269 |
| Native confidence, constant signal | 381/539 (70.69%) | 391/539 (72.54%) | 269 |
| Random selection, constant signal | 389/539 (72.17%) | 396/539 (73.47%) | 269 |
| Jev selection, live signal | 379/539 (70.32%) | 387/539 (71.80%) | 269 |
| Jev selection, shuffled signal | 375/539 (69.57%) | 383/539 (71.06%) | 269 |

| Primary contrast | Difference (pp) | 98.75% interval | Wins / losses | Blocks (pp) |
| --- | ---: | ---: | ---: | ---: |
| Selection: Jev − random | +0.56 | [-2.23, +3.71] | 22 / 19 | +0.00, +1.12 |
| Selection: Jev − native confidence | +2.04 | [-0.56, +4.64] | 21 / 10 | +1.85, +2.23 |
| Feedback: live − constant | -2.41 | [-5.01, +0.19] | 10 / 23 | -2.22, -2.60 |
| Feedback: live − shuffled | +0.74 | [-1.11, +2.60] | 10 / 6 | +1.48, +0.00 |

Selection criterion: **not met**. Internal-feedback criterion: **not met**.
Each component requires both relevant adjusted lower bounds above zero, both
point estimates at least +2 pp, and a positive difference in each block.
Failure to meet that criterion does not establish equivalence or rule out
smaller benefits. All planned comparisons are retained.

![R28 attribution contrasts](figures/routing-paper/r28-attribution.svg)

Figure 2. Registered primary comparisons on the 539 eligible cases. All 1,616
generated answers and 539 Jev receipts passed independent integrity admission
before scoring. The [complete R28 report](../reports/2026-09-25-routing-feedback/README.md)
contains token/work accounting, secondary readouts, numerical replay and costs.

## 6. Interpretation and limitations

The fresh IFEval cohort reverses the earlier IFBench direction: all tested repair
policies score below original Granite. Live repair loses 5.38 percentage points
relative to native, with 11 wins, 40 losses and a descriptive 95% interval
[-7.98, -2.78]. None of the four primary attribution intervals excludes zero at
the registered 98.75% level. A positive point estimate for selection versus native
confidence therefore does not establish an effective repair system.

Post-result selection inspection finds 116 of the 131 native failures among Jev's
269 selected cases, compared with 53 for native confidence and 67 for fixed random
selection. Jev identifies many problematic drafts, but live repair fixes only 11
of those 116 and damages 40 of 153 selected native passes. The fixed quota would
require at least 138 native passes even under perfect error ranking. Correction
ability and preservation are therefore central limitations under this allocation;
we have not tested a policy that can choose very few repairs. These descriptive
counts are not a newly substituted primary outcome or a validated threshold.

The original checker also emitted one handled language-detection exception during
a loose-check candidate evaluation. The pinned upstream fallback accepts that
language constraint. Post-result rechecking reproduces all original booleans and
finds no such exception during strict evaluation. This limits the secondary loose
metric without changing the primary scores; details and hashes are in the
[R28 diagnostic record](../reports/2026-09-25-routing-feedback/review-diagnostics.json).

The earlier IFBench result supports improved constraint compliance in that tested
system. It does not establish that correct scalar pairing is essential, nor that
the generator has acquired broad reasoning ability. A scalar assessment also
specifies neither which requirement failed nor how to repair it. Whether richer
structured feedback would help is a separate hypothesis requiring another study.

The R27/R28 evidence concerns one backbone, one adapter selected from a small
supervised training study, one fixed layer and specific generation profiles.
Greedy decoding and pinned software improve traceability but do not guarantee identical behavior
on other hardware. Hosted Jev's internal compute and parameters are unknown;
reporting only Granite's size would understate the whole system. Colocation,
production serving and end-to-end latency are not measured.

R27's repeated exploration, descriptive analyses, readout artifacts and incomplete
larger-model comparison limit generalization. R28 avoids tuning on its answers
but uses a long-public benchmark, and its rule-based grader does not provide
comprehensive semantic evaluation. Numerous earlier attempts are retained rather
than selectively presenting the most favorable stage. Their lexical, classifier,
judge-based and independently checked scores are not interchangeable metrics.

## 7. Reproducibility and publication status

The repository preserves source revisions, protocols, manifests, original and
adapter weight hashes, exact generated IDs, stopping decisions, API receipts,
negative attempts and resource accounting. Original model parameters are compared
before and after inference. Dataset-specific licenses remain separate from the
code license. Gated GPQA material and private operational credentials are not
redistributed as public raw artifacts. Public aggregate scores alone cannot
reproduce every historical token audit.

The [reproduction guide](routing-feedback-reproduction.md) documents the R28
acquisition, inference, integrity and grading paths and separates offline replay
from a new paid run. Hosted API availability and version retention remain external
dependencies. A broader replication on another backbone and appropriately
validated larger-model generation profiles would be needed for broader claims.

Implementation, orchestration, analysis and drafting received AI assistance.
Human authors must verify the evidence, review the text and take responsibility
for the final submission; authorship has not been assigned to an AI system.

This is a working manuscript for author review, not a published paper or released
model. Final authorship, affiliations, venue formatting and publication approval
remain editorial decisions. Nothing here asserts completion of the ten-benchmark
or larger-model objective.

## Appendix A. R29-A: localized correction with preservation training

The R28 result motivated a [separate prospective study](structured-correction-plan-v1.md)
registered before new inference. It changes both training and conditioning, so
cross-study score differences cannot isolate either factor. This appendix reports
its scoped evidence rather than treating authored tasks as another public benchmark.

We authored 128 training, 32 development and 96 test worlds, balanced between
temporal object movement and compositional object/container/room movement. Each
world asks three final-room questions; all three normalized room names must match
for primary success. Worlds are fresh but share templates. An independent graph
replayer reconstructs the reference from the supplied text. This resembles the
purpose of earlier prerequisite toy question-answering tasks
([Weston et al.](https://arxiv.org/abs/1502.05698)); neither this task principle nor
an executable state oracle is a novelty claim.

The same frozen Granite checkpoint generates native drafts. Jev 1.13.0 receives
the problem and actual draft, returning three correctness probabilities without
reference answers. A new 262,144-parameter branch after block 19 attends over
three question/draft memory slots, each the mean frozen input embedding of that
question and its generated answer field. The slot weights and correctness scores
condition a bounded residual update only at the repair-generation boundary and
subsequent generated positions. Original parameters and accepted token IDs remain
unchanged; every final token is generated by Granite.

Five equally sized branches use matched initialization, order, data and optimizer
under two seeds: structured, scalar, constant, text and oracle diagnosis. Correct
training drafts have exact-original-token preservation targets; wrong drafts have
independently constructed corrected targets. Two-epoch training and development
selection precede held-out generation. The scalar condition receives the mean
probability repeated in all slots. Test-time donor shuffling preserves recipient
memory but replaces its probability vector with another world's vector from the
same task family. Oracle flags deliberately use reference correctness and cannot
support a deployable claim. All details and initial verifier mistakes remain in
the [admission record](structured-correction-admission-v1.md).

| Condition | All 96 worlds | Temporal | Compositional |
| --- | ---: | ---: | ---: |
| Original Granite | 25.00% | 50.00% | 0.00% |
| Blind repair | 26.04% | 52.08% | 0.00% |
| Constant feedback | 16.15% | 27.08% | 5.21% |
| Scalar Jev feedback | 28.65% | 54.17% | 3.12% |
| Structured Jev feedback | 29.69% | 55.21% | 4.17% |
| Shuffled feedback | 22.92% | 41.67% | 4.17% |
| Text Jev feedback | 21.88% | 41.67% | 2.08% |
| Oracle diagnosis, nondeployable | 30.73% | 54.17% | 7.29% |

Trained rows are means across two seeds. Structured-minus-native is +4.69 pp
(exploratory paired 95% interval [+1.04, +8.85]); structured-minus-shuffled is
+6.77 pp [+1.56, +12.50]. Structured-minus-scalar is +1.04 pp [−1.04, +3.65].
These intervals use 10,000 within-family paired bootstrap samples; they are not
adjusted confirmatory or multi-benchmark tests. Structured repair fixes 5 and 4
native failing worlds in the two seeds while preserving all 24 native passes.
Shuffling changes 41/96 and 39/96 final token sequences. Thus feedback alignment
has useful effects in this cohort, but precise slot localization has not shown
an advantage beyond aggregate reliability. Donor shuffling changes both.

Development-selected retention thresholds are zero for both seeds, meaning no
repairs; this secondary policy consequently remains at native accuracy. We do not
change it after seeing the test results. All held-out outputs follow the requested
three-line format. Non-room fields are crate names/colors rather than alternative
expressions of the requested room, so the observed compositional weakness is not
resolved by a formatting readout change. A post-result verifier inspection flags
125/157 wrong native fields and 1/131 correct fields at p < 0.5. This describes
diagnosis on the original draft, not final-answer quality.

All 2,144 outputs, 256 provider judgments and 2,560 training steps pass integrity
reconstruction, and a separate copied-artifact replay reproduces the complete
analysis byte-for-byte. Original backbone digests match. Authored inputs, raw
records, all research adapters, per-case grades, negative admission findings and
costs are included in the [completed report](../reports/2026-09-26-structured-correction/README.md).
Owned cloud resources are deleted. The conservative cumulative estimate is
$118.12/$125, including operating allowances, not a final invoice.

R30 below subsequently separates score placement from overall reliability using
frozen checkpoints and fresh worlds. Its result motivates the registered R31
memory comparison; neither registration nor a working hook is quality evidence.

## Appendix B. R30: fresh feedback-pairing replication

The [prospective protocol](feedback-pairing-plan-v1.md) froze four R29 structured/
scalar checkpoints on 384 new worlds, 192 per family, without new training or
threshold selection. Each world contributes original native and blind repair plus
nine feedback/checkpoint conditions under two fixed training seeds: 7,680 outputs
and one three-question Jev request per world. All final answers are Granite-generated.

| Condition | All-three accuracy | Temporal | Compositional |
| --- | ---: | ---: | ---: |
| Original Granite | 28.65% | 55.21% | 2.08% |
| Blind repair | 29.17% | 56.25% | 2.08% |
| Structured Jev | 32.16% | 57.81% | 6.51% |
| Repeated mean, same checkpoint | 34.11% | 61.46% | 6.77% |
| Mean of two within-draft rotations | 32.03% | 58.20% | 5.86% |
| Same-family donor feedback | 27.21% | 50.52% | 3.91% |
| Constant 0.5, same checkpoint | 25.00% | 43.49% | 6.51% |
| Known-room answer-type rule | 31.12% | 56.25% | 5.99% |
| Oracle flags, same checkpoint | 32.16% | 57.81% | 6.51% |
| Separately trained scalar | 34.77% | 62.24% | 7.29% |

| Registered primary contrast | Difference (pp) | 98.3333% interval |
| --- | ---: | --- |
| Structured − native | +3.52 | [+1.69,+5.73] |
| Structured − repeated mean | −1.95 | [−4.17,+0.13] |
| Structured − within-draft rotation mean | +0.13 | [−1.50,+1.82] |

The native advantage replicates within the authored task family. Structured repair
fixes 15/12 failing worlds across the two seeds and damages none of the 110 native
passes. The registered ±2 pp mean-equivalence criterion is not met. Correct field
pairing shows no supported advantage over permutations, and donor feedback changes
overall reliability as well as locality. The separately trained scalar advantage
and live-minus-donor advantage are secondary/descriptive comparisons.

The nondeployable oracle substitutes perfect flags into an adapter trained on Jev
probabilities; its unchanged average score motivates, but does not establish, a
memory/correction-capacity explanation. Absolute compositional accuracy remains
low. R29 and R30 share templates/vocabulary and are not pooled as one prespecified
sample. They do not reverse the earlier public-task transfer failure.

![R30 scores and paired effects](../reports/2026-09-26-feedback-pairing/figures/r30-feedback-pairing.svg)

The [complete report](../reports/2026-09-26-feedback-pairing/README.md) publishes raw
records, inherited adapters, hashes and exact independent replay. It accounts for
93,207 generated tokens, 328,283 Jev input tokens and verified cloud cleanup.
The secondary half-threshold policy replays saved outputs and makes no deployment
work-saving claim. The cumulative conservative estimate is $122.90 under the
owner's $175 cap; it is not an invoice.

The prospectively registered R31 study selects scalar as lead from completed R30
evidence and tests the memory representation hypothesis. Its completed results
follow in Appendix C. Prior art already includes verifier-guided latent steering;
any contribution needs a narrower mechanism and measured transfer.


## Appendix C. R31: matched contextual memory and feedback

The [frozen protocol](contextual-memory-plan-v1.md) fixes 512 training, 64 development
and 256 test worlds, disjoint from the preceding studies but retaining their
vocabulary and templates. Twelve rank-32 adapters cross embedding/contextual memory,
structured/scalar/constant conditioning and seeds 3101/3102. Initialization, targets,
training order, optimizer, capacity and selected token positions are matched.
Earliest best development accuracy selects each checkpoint before test generation.

Three detached vectors pool each question and its unique actual draft field, using
original token positions. Contextual memory uses a frozen prefill through block 19;
the control pools original input embeddings at the same positions. This matched
embedding construction differs from R29's standalone retokenized text. Correct
native outputs supply preservation targets; failed natives use the three reference
room names. References enter training targets and independent grading, never memory
extraction or provider inputs. Original weights remain frozen.

| Trained condition | All-three accuracy | Temporal | Compositional |
| --- | ---: | ---: | ---: |
| Original Granite | 30.08% | 59.38% | 0.78% |
| Blind repair | 31.25% | 60.94% | 1.56% |
| Embedding structured | 40.23% | 65.62% | 14.84% |
| Embedding scalar | 46.29% | 73.05% | 19.53% |
| Embedding constant | 47.46% | 73.83% | 21.09% |
| Contextual structured | 39.84% | 67.58% | 12.11% |
| Contextual scalar | 46.29% | 73.05% | 19.53% |
| Contextual constant | 47.85% | 73.83% | 21.88% |

| Registered primary contrast | Difference (pp) | 98.75% interval |
| --- | ---: | --- |
| Contextual scalar − native | +16.21 | [+10.94,+21.68] |
| Contextual scalar − embedding scalar | 0.00 | [0.00,0.00] |
| Contextual structured − contextual scalar | −6.45 | [−10.55,−2.54] |
| Contextual scalar − its donor feedback | +8.40 | [+3.71,+13.48] |

All main arms pass formatting on all cases and have no length stops. Intervals
resample worlds within task, averaging the fixed seeds within each world; they do
not treat 512 seed outputs as independent or represent arbitrary training-seed
uncertainty. Correctness matches exactly across memory types for both scalar seeds,
although seven of 512 token sequences differ. A post-hoc integrity diagnostic
confirms distinct tensors and checkpoints. The degenerate bootstrap interval does
not prove identical unseen-input behavior. No memory-by-feedback interaction is
established: −0.39 points, descriptive 95% interval [−2.93,+2.15].

Scalar repair fixes 44/39 failed worlds without damaging any of 77 native passes;
constant-trained contextual repair fixes 55/47 but damages 7/4. Live scalar minus
constant-trained contextual repair is −1.56 points, descriptive 95% interval
[−5.08,+2.15]; this establishes neither superiority nor equivalence. Same-checkpoint
constant substitution scores only 31.64%, unlike the independently constant-trained
47.85% condition. Informative feedback can therefore matter to a checkpoint trained
with that signal without making the resulting recipe better than a Jev-free one.
The observed preservation trade-off is exploratory evidence for a follow-up, not
proof of a successful selective-repair policy.

![R31 accuracy and registered effects](../reports/2026-09-26-contextual-memory/figures/r31-contextual-memory.svg)

The stronger absolute results cannot be attributed to increased training data
alone: sample size, selected memory positions, worlds and checkpoints also differ
from prior studies. The within-R31 matched comparisons support no added contextual
memory accuracy. They do not measure out-of-template reasoning, general knowledge
transfer, colocation or larger-model superiority. Structured versus scalar compares
separately trained checkpoints and is not a same-checkpoint permutation test.

The [complete report](../reports/2026-09-26-contextual-memory/README.md) publishes
all 11,840 outputs, 832 receipts, 832 paired memories, 36 initial/epoch checkpoint
files and the full independent reconstruction of 12,288 training-example passes
and 1,536 optimizer updates. Exact public-archive replay reproduces the analysis.
The recorded run generated 143,167 tokens and used 711,344 Jev input tokens.
Component sums are approximately 0.56 seconds for native, 1.78 for scalar repair
and 1.29 for constant-trained repair per case; these are post-hoc sums excluding
loading, queues and other overhead, not an interactive latency benchmark.

Owned cloud resources are verified deleted. Conservative cumulative cost is
$129.42/$175, including an operating allowance, not an invoice. The result-informed
next MuSR admission retains both scalar memory conditions and adds independently
constant-trained controls; it is separately registered before execution. No new
public-task or model-release result is claimed here.
