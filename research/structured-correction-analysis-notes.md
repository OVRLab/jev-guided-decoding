# R29-A interpretation and supplemental analysis notes

Recorded during training on 2026-09-26, before any held-out generation or quality
inspection. The [registered primary protocol](structured-correction-plan-v1.md)
is unchanged. These supplemental analyses cannot replace its primary outcomes.

## Readout and task interpretation

The primary checker measures whether all three requested room names match the
independent reference after case, whitespace and terminal-punctuation normalization.
It accepts either `1.` or `1)` numbering for the answer readout; the separate format
flag checks three `1.`/`2.`/`3.` lines. Missing, contradictory/duplicate or additional
numbered answer fields fail the relevant primary readout. This is a constrained
answer contract in the prompt, not a constrained decoder. Do not describe it as a
general semantic evaluator for arbitrary prose.

Inspect all non-room or unparsed output fields after audit and list their forms.
If a semantically equivalent expression falls outside the frozen readout, disclose
it and keep the registered score unchanged. Any separate adjudication must retain
its own name, rule and denominator; it must not silently rewrite the primary score.

Report reference-room frequencies and all eight retrospective constant-room
policies (the same room on all three answer lines). Those are class-balance
diagnostics, not model runs or prospectively selected deployment policies. The
deterministic state-replay program can solve every authored world by construction;
it is the grading oracle, not an LLM comparison. These facts limit practical
claims from this diagnostic even if a neural branch improves accuracy.

Controlled question-answering tasks are longstanding prior art, including
[Weston et al.'s prerequisite toy tasks](https://arxiv.org/abs/1502.05698).
Our newly authored instances are not the bAbI dataset or a replication of its
published scores. Their role is to isolate repair and preservation with an
independent answer oracle before investing in public-domain transfer.

## Training-only representation diagnostic

A post-launch descriptive probe examined the **128 training drafts only**, with
no test access or configuration changes. It reconstructed the exact R29 memory
construction from the frozen original embedding matrix: mean embeddings of each
question and its actual draft answer span. Across 384 within-world slot pairs,
cosine similarity was:

| Statistic | Similarity |
| --- | ---: |
| Minimum | 0.881653 |
| Median | 0.913105 |
| Mean | 0.918573 |
| Maximum | 0.963016 |

This establishes representation overlap, not that the learned branch cannot
distinguish slots, nor a causal explanation of its quality. It motivates a possible
future comparison with contextual representations at the same model boundary.
Keep that comparison separate from R29-A's currently frozen experiment.

One candidate would capture each question and answer span's contextual hidden
states during repair prefill, before modifying the answer-generation positions,
and retain them in the repair scope's private memory. It would preserve the same
adapter capacity, data, supervision and feedback controls so that memory construction
is the changed factor. It must reject spans reaching training target positions,
retain causal cache behavior, and pass fresh mechanical/held-out tests. It is not
implemented or admitted by this note.

## Work and cost interpretation

R29 waits two seconds before each provider request to keep the serial research
runner conservative. API receipt timing excludes that deliberate delay; total
worker time includes it, plus training and development. None is an optimized
serving-latency benchmark. The retention policy is replayed over generated candidates;
do not claim that its skipped selections saved actual GPU work or Jev calls.

[Current TypeSafe model documentation](https://docs.typesafe.ai/models), checked
2026-09-26, prices Jev 1.13 at $0.042 per million input tokens, with free output
tokens. The reservation ledger deliberately uses $0.05 per million. Report the
documented-price estimate and the conservative spending reserve separately;
neither is an invoice. Jev's undisclosed model resources prevent treating the
whole system as having only Granite's parameter count.
