# R13 method in relation to controlled decoding

Targeted method review, 2026-09-21, while the frozen R13 test was running. This
document changes no experiment setting, primary contrast or stopping rule. It
distinguishes the implemented heuristic from stronger claims about reward control.

## What prior methods establish

**FUDGE**, Section 3, learns a classifier on partial prefixes using the attribute
of the completed training sequence. Its conditional-generation argument depends
on predicting an attribute in the eventual continuation. The implementation
combines that prediction with the generator distribution, with practical candidate
truncation. A classifier judging whether an already completed local assertion is
true is a different object. Our inference from that distinction: Jev's local
support score cannot simply be interpreted as the probability that Granite's final
answer will be correct. [Yang and Klein, 2021](https://aclanthology.org/2021.naacl-main.276.pdf).

**Controlled Decoding**, Sections 2–3, formalizes a value function for the reward
of completing a prefix under the reference model. It learns a prefix scorer and
uses exponential reweighting for tokenwise control; it also describes blockwise
selection. The stated optimization result depends on that value formulation.
Our score is neither trained nor validated as this expected future reward, so
using an exponential multiplier does not transfer the paper's guarantee to R13.
[Mudgal et al., 2024](https://arxiv.org/html/2310.17022v3).

**DeAL**, Section 3.2.2, considers high-probability next-token candidates, extends
them with lookahead, and combines likelihood with an alignment heuristic. Its
reported implementation uses greedy lookahead and chooses the best scored root
among its candidate set. This is a close precedent for R13's rollout-and-score
placement. Our sparse, bounded stochastic reweighting retains unevaluated
syntax-permitted mass and runs at two selected boundaries; those implementation
differences do not make lookahead-guided decoding a new principle.
[Huang et al., 2025](https://arxiv.org/html/2402.06147v3).

These are method comparisons, not reproductions of their experiments. None of
their reported performance numbers is evidence for Jev or Granite. Other related
work remains in the [source ledger](related-work.md), with review depth stated.

## Exact R13 rule

The following describes our own frozen source, rather than a theorem imported
from those papers. Let `p` be Granite's next-token distribution **after the common
syntax mask**, and let `A` contain the four evaluated root actions. For each
assessable action `a`, Jev supplies local support `s(a)`. The reference `a₀` is
the most probable root. For assessed actions:

```text
d(a) = clip(2 · [s(a) − s(a₀)], −0.5, +0.5)
q(a) = p(a) · exp(c · d(a)) / Z
```

Unassessed/unevaluated actions receive zero bias. The code reduces `c` within
`[0,1]` as needed so that `KL(q || p) ≤ 0.02`, including the probability mass
outside `A`. If the reference is unassessed, the intervention is a no-op. The
zero control sets strength to zero. Jev chooses no final class in this rule.
The actual source is [logit_bias.py](../src/jev_guided_decoding/logit_bias.py),
[checkpoint selection](experiments/logit_controller.py), and
[R13 controller](experiments/structured_controller.py).

The KL limit controls this local change relative to the grammar-conditioned
distribution. It does not bound the change introduced by the grammar itself,
the addition of two reasoning steps relative to the direct arm, or a different
whole-step commitment policy. It is not a lower bound on accuracy improvement.

The evaluated greedy continuation and the subsequently sampled token-arm tail
may differ. Consequently the score estimates support for a particular lookahead,
not necessarily the assertion ultimately accepted. The soft-step ablation commits
that evaluated continuation when its root is selected, testing this placement
difference with the same rubric and first candidate pool. It still samples under
bounded root reweighting; it is not an argmax-Jev selector.

## Consequence for reporting

Report three different quantities: critic discrimination on proposed claims,
independently graded claims actually accepted, and Granite's final-answer accuracy.
High proposal-ranking accuracy alone establishes neither of the latter two.
Native/staged separates the common reasoning protocol; likelihood/Jev separates
two root policies; zero checks mechanical identity; shuffled tests score-to-action
assignment; soft-step tests commitment granularity. These comparisons isolate
specific parts of this controller, not an optimal hidden layer or universal
benefit of adding a second model.
