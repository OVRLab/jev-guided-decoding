# A conditional Jev boundary inside one Granite prefill

Design note, 2026-09-22, written while R17 held-out inference was running. This is
an **unimplemented hypothesis**, not R18 registration, a tested speedup or a new
model release. Finish and interpret R17 before selecting the next quality study.

## Why investigate this boundary

R17 buffers up to eight native tokens before deciding to call Jev. A call discards
that pilot and starts a fresh guided prefill. Even a gate that avoids API requests
can add substantial model work. A useful architecture should also avoid doing the
same lower-layer work twice.

The current selected attention intervention begins at zero-indexed layer 19. All
layers below it remain native. Inspection of the pinned Transformers 4.57.1
`GraniteMoeHybridModel.forward` confirms an ordered layer loop using shared rotary
positions and a request cache. This suggests placing the decision **immediately
before layer 19 during the first prefill**, carrying the already-computed native
state into either branch:

```text
Question + complete original evidence
                 |
        Granite layers 0–18
                 |
      Cheap features of current state
                 |
        Development-fitted benefit gate
             /                 \
          skip                 call
           |                    |
           |              Jev source relevance
           |                    |
           +----------+---------+
                      |
        Continue layers 19–39 in the same prefill
        Native heads, or selected guided heads
                      |
          First Granite token and later decoding
```

The gate would finish before the first output token is chosen. If it calls, a
bounded request supplies the same source-relevance judgments as today; it does
not generate the answer. If it skips or the request fails, continue native
computation. No native pilot tokens need to be generated or discarded. This is a
possible reduction in repeated computation, not a proven reduction in wall time.
The network request can still stall the forward pass.

## What should decide whether to call

Start with a small, frozen feature set from the final prompt position at layer 18:
source attention mass, entropy across source documents, and disagreement among
head-level source distributions. These measure a model state, not semantic
correctness or an explanation of reasoning. Compute only the needed query row;
do not retain a full prompt-by-prompt attention tensor solely for the gate.

Fit a small rule to **guided-minus-native final-answer benefit** on development
pairs, with an explicit request budget. Compare it with always, never, random
at the same call count, and R17's output-confidence gate. Confidence can be high
on an incorrect copied answer, and uncertainty can be high where steering cannot
help. The target should therefore be incremental benefit, not an assumption that
low confidence always needs an intervention. A trained small router would use
new labeled development pairs; it would not require Granite's original training
corpus or update Granite's weights.

The proposed features differ from R17's first-eight-token features, so R17's fitted
thresholds cannot be transferred unchanged. Its exposed test set also cannot
become a fresh confirmation set. A new prospective study would need separate
feature development, selection and evaluation, including answerable and missing
cases and an external task beyond the existing Hotpot sample.

## Engineering and scientific admission

Before any quality claim, verify one-pass always-guided output equals the existing
always-guided runtime, and one-pass no-call output equals native, at full-logit,
accepted-token and cache levels on the real checkpoint. Preserve first-token
scaling, rotary positions, masks, cache length and EOS. Record actual layer work,
request time, peak memory and time to first token, not just model forward counts.
The new gate must be evaluated before the first controlled layer; changing earlier
layers would invalidate the reusable-prefix argument.

A synchronous layer callback could demonstrate the mechanism in a serial research
runner; a resumable forward can expose the pause explicitly. Neither should be
promoted to concurrent serving without request-local intervention state and
cancellation cleanup. The current global SDPA dispatcher is deliberately serial.
Provider failure must retain the native continuation and the paid-attempt receipt;
no ambiguous timeout should be replayed automatically.

This architecture changes where a decision is made and can eliminate duplicate
lower-layer work. It does not itself promise better answer quality. If R17 shows
that the relevance intervention has little useful effect on a task, moving the
gate will not create that missing effect.

## Relevant existing ideas

A broad comparison of adaptive retrieval methods evaluates both uncertainty and
efficiency, supporting their inclusion as controls; it does not evaluate Jev or
this intervention. [Moskvoretskii et al., ACL 2025](https://aclanthology.org/2025.acl-long.319/).

Dey et al. propose single-pass hidden-state probes for missing versus conflicting
knowledge. Their proposed probe targets depend on pretraining occurrence counts;
the preliminary results use semantic entropy and WEPR. We should not describe
those results as validation of our source-attention features or assume access to
Granite's pretraining corpus. [Primary workshop text, 2026](https://arxiv.org/html/2607.07380v1).

V-Steer edits cached value vectors after prefill, using attribution and span
roles, for instruction-hierarchy tasks. It is a relevant alternative to repeatedly
altering attention masks, not a tested Jev/Granite QA baseline. Its GQA treatment
acts at shared KV-head scope, which differs from our selected query-head scope.
Our mass-conserving mask operation is not equivalent to scaling V. A future value
intervention must be credited and compared rather than renamed as a new invention.
[Zeng et al., COLM 2026](https://arxiv.org/html/2607.26228v1).

This targeted reading was added after R17 development, independently of its frozen
protocol. [Source hashes](../reports/2026-09-22-selective-attention/followup-source-manifest.json)
retain retrieval/version evidence. No existing paper's reported result is evidence
that this proposed Granite/Jev boundary works, and no historical novelty claim is made.
