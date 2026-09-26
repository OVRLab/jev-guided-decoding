# Proposed next design: localized Jev feedback with learned preservation

Date: 2026-09-26. **Design proposal only: unimplemented, untrained and unrun.**
This records the recommendation after R28. It is not a frozen R29 protocol, a new
result, a novelty claim, or authorization to exceed the cumulative $125 ceiling.

Documentation plan: add this proposal and link it from the notebook, register and
feature roadmap; preserve completed protocols and reports. Validate source claims,
local links and the documentation diff. No model behavior or paid execution changes.

## Decision and evidence

The next hypothesis is a trained internal repair branch that receives **where and
what may be wrong**, with explicit training to preserve already correct answers.
The bottleneck indicated by the studies is converting criticism into beneficial
correction. A better intervention layer alone has not been established.

| Observation | Design implication, not a proven causal explanation |
| --- | --- |
| [R28](../reports/2026-09-25-routing-feedback/README.md): native 408/539, live repair 379/539; 11 native failures fixed and 40 native passes broken | Improve the repair capability and learn when to keep the native output. |
| R28 post-hoc inspection: Jev's 269 selected cases contain 116/131 native failures and 153 native passes | Jev can concentrate errors in this cohort; this does not establish calibrated repair benefit or a successful registered routing contrast. |
| R28 forces 269 repairs despite only 131 native failures | Use a development-calibrated benefit threshold in a future deployment policy; allow zero repairs. Preserve the fixed-quota experiment as an attribution study. |
| [R22](../reports/2026-09-23-learned-feedback/README.md): two local probabilities, but live/shuffled/oracle feedback produces identical final token sequences | More feedback dimensions alone are insufficient. Training and ablations must establish that the model uses the information productively. |
| [R25](../reports/2026-09-23-gated-repair/README.md): adapter trained on 384 math/science drafts; full repair regresses while selective science retention helps | Broaden development coverage and include correct-draft preservation targets. Transfer and rewrite training are possible failure sources, not established causes. |
| [R27](../reports/2026-09-25-completed-granite/README.md): GPQA/IFBench gains, nearby fixed/shuffled controls, no AIME gain | Formatting recovery and extra trained computation must be separated from new reasoning capability. |

An additional **post-hoc calculation**, using R28's already reported transitions,
is `(408 + 11) / 539 = 77.74%`: perfect selection between each saved native answer
and its saved live-policy answer would achieve this score. This is an oracle bound
for those saved pairs, not an executable policy, new inference, a statistical
confirmation, or a ceiling on future correction models. Rejection alone cannot
create better candidates than those pairs contain.

## Proposed information flow

```text
Prompt -> frozen Granite -> native draft, saved exactly
                              |
                  bounded, identified draft spans
                              |
                Jev: focused typed judgments
              (target span/requirement, probabilities)
                              |
                 learned feedback representation
                              |
              trained repair branch after block 19
                              |
               Granite generates a repair candidate
                              |
            calibrated retain/repair decision -> answer
```

1. Preserve a native answer as an explicit alternative. Start with one draft
   checkpoint and at most one repair; more frequent reasoning checkpoints are a
   later hypothesis, not part of the first test.
2. Bind focused Jev questions to actual draft spans and explicit user requirements
   or supplied evidence. Example judgments concern a contradiction, unsupported
   claim, or unmet instruction. Jev returns typed probabilities over supplied
   questions/options; it does not generate a correction or read Granite's hidden
   states. Retain uncertain/unassessed cases. Span construction uses input text
   and actual drafts, never benchmark reference answers or hidden checker metadata.
3. Encode the judgment type, target span representation and returned probabilities
   into a small feedback memory. A new trainable branch conditions Granite's
   hidden states on that memory during repair. Start after zero-indexed block 19
   to isolate the change from R25/R28; this is not evidence that block 19 is optimal.
   One candidate implementation is low-rank cross-attention to the feedback memory
   followed by a residual update. Freeze the exact implementation and parameter
   budget in the execution protocol, with equally sized controls.
4. Build that memory only from draft/prompt spans already present in the repair
   prefill, using their frozen representations and position bindings. Apply
   feedback at the repair-answer boundary and subsequent generated positions.
   Earlier cached states are not retroactively changed. Keep branch caches
   separate, original accepted token IDs intact, and no cross-request hook state.
5. Train only the new branch and small decision components initially. Original
   Granite and Jev remain frozen; all answer tokens come from Granite. Jev stays
   active at inference, rather than only producing training labels.

The internal path is more specific than a scalar controlling residual strength:
the branch can condition *which transformation* it applies on the diagnosed span
and error type. Whether it learns a useful transformation is the central unknown.
There is no proposed HTTP call on every token or layer.

## Training changes that must accompany the interface

Collect real native drafts on fresh development tasks, including correct drafts,
natural errors and independently checked corrections. Use licensed training data
and independent checkers or reviewed targets; Jev must not be the sole source of
training truth or the final evaluator. Authored error examples can supplement but
must not replace natural failures.

Train wrong drafts toward validated repairs and correct drafts toward exact native
retention. Teach an explicit no-change decision; separately measure preservation
and correction, since maximizing preservation alone permits the useless policy
of never repairing. Refresh development drafts as the repair model changes to
measure distribution shift. Begin with supervised targets; reinforcement learning
is a possible later method, not a necessary first expense.

Calibrate repair decisions against expected net correctness improvement and actual
cost on development data. Probability that the draft is wrong is not probability
that the available repair will help. Do not force a fixed repair percentage.
The deployment decision must use only available inputs, outputs and judgments.
Ground-truth acceptance is an oracle diagnostic, never the deployed result.

Calling Jev conditionally is a subsequent efficiency study once live feedback
improves quality. The initial attribution pilot should collect judgments across
eligible development cases to avoid hiding routing errors. A later pre-call gate
must predict the value of obtaining feedback, and record genuine avoided requests
and generation work. No latency savings are inferred from offline replay.

## First experiment before another broad benchmark run

Freeze fresh train/development/test splits, evaluator admission, seeds, source and
data hashes, budgets, effect thresholds and stopping rules before execution. The
completed benchmark cohorts are now exposed; do not tune on their cases and call
a repeat fresh validation. Exact sample sizes and power remain to be planned.

1. **Check correction capacity:** use independently validated error locations and
   diagnoses on development data as a labeled oracle diagnostic, alongside live
   Jev diagnoses. Establish whether specific feedback enables correct candidates
   at all. Oracle improvement is not a Jev result; failure motivates better repair
   training or greater model capacity, rather than a layer sweep.
2. **Separate training from feedback:** use the same preservation/correction
   training recipe, data, seeds and capacity for scalar, structured and constant
   feedback arms. Include test-time shuffled feedback with valid target bindings,
   preserving question types and marginal probabilities while breaking alignment.
   Inspect whether final outputs and independently graded correctness depend on
   meaningful feedback, not just whether hidden activations change.
3. **Test the internal placement:** compare the same diagnosis conveyed as text,
   a Jev-free trained repairer, and Jev-free additional sampling/reranking under
   disclosed actual work. Compare adapter-disabled native generation as well.
   Internal conditioning must earn its complexity beyond access to more information
   or additional computation.
4. **Separate candidate quality from acceptance:** score raw candidates and the
   frozen retain/repair policy separately. Report fixed errors, damaged correct
   answers, unresolved cases, net correctness, formatting, truncation, all attempts,
   tokens, API costs and latency. Include a fixed common selection policy for
   attribution before comparing separately calibrated deployment policies.
5. **Advance on evidence:** require held-out net benefit over native and informative
   comparisons against the relevant matched controls, replicated across seeds and
   task types. If the internal channel adds no reliable benefit, prefer the simpler
   successful control. Only then expand the frozen architecture to the broad suite
   and larger models with fair generation budgets and admitted graders.

This is a staged experiment, not a demand that every exploratory comparison pass
one undifferentiated success rule. Each comparison answers a distinct question:
does the system help, does live Jev help, and does internal placement help?

## Prior work and the possible contribution

- [TypeSafe primitives](https://docs.typesafe.ai/primitives) provide typed focused
  judgments and probabilities; our proposed adapter supplies their learned
  connection to Granite's internal computation.
- [SCORE](https://arxiv.org/abs/2404.17140) already studies strong verification with
  trained small-model refinement. Separating detection from correction is not new.
- [SCoRe](https://arxiv.org/abs/2409.12917) studies training self-correction on the
  model's own trajectories and limitations of offline correction training. It
  motivates investigating the training distribution, not a prediction of our gain.
- [ReFT](https://arxiv.org/abs/2404.03592) already learns interventions in frozen
  model representations. A learned residual insertion alone is not novel.
- [Thought-ICS](https://arxiv.org/abs/2602.02416) studies structured error localization,
  backtracking and regeneration, including the damage caused by fallible
  verification. Localization or prefix retention alone is not a novelty claim.

The possible research contribution is evidence that **localized typed external
judgments, coupled to a trained internal correction branch and explicit
preservation, improve a small generator beyond matched alternatives**. That
combination still needs a fuller novelty review and positive independent results.
It cannot currently be called a breakthrough or a model that beats larger systems.

No paid run accompanies this proposal. The latest conservative cumulative estimate
remains about $114 of $125, not an invoice; roughly $11 before unresolved tax/network
costs does not establish that the proposed training program fits the remaining
budget. Freeze a costed execution protocol before allocating infrastructure.
