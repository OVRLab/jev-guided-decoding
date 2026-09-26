# Prior-art check for contextual Granite–Jev repair

Checked 2026-09-26 while R30 runs; this changes the literature record, not its
frozen protocol. No external method has been reproduced or benchmarked here.

| Primary source and review depth | Relevant overlap | Consequence for this project |
| --- | --- | --- |
| [ITI, Li et al.](https://arxiv.org/abs/2306.03341), abstract | Inference-time changes to selected activations seek more truthful outputs. | Internal intervention itself predates this work. |
| [ReFT, Wu et al.](https://arxiv.org/abs/2404.03592), abstract | Learned representation interventions adapt a frozen language model. | Frozen original weights plus a small learned branch is not sufficient novelty. |
| [ATLAS, Nguyen and Le, v4](https://arxiv.org/html/2601.03093v4), method §3 and comparison §A.7 | A trained latent verifier selects among no-op and reasoning-mode activation shifts at thought boundaries; its ATLAS-T comparison uses a text verifier. | Verifier-guided adaptive internal steering also predates our candidate. |
| [SCoRe, Kumar et al.](https://arxiv.org/abs/2409.12917), abstract | Studies why supervised correction can fail and trains correction through online reinforcement learning. | Our supervised branch should not be presented as reproducing that result. |

ATLAS's main runtime uses a local latent verifier distilled from process-reward
supervision, while its text-verifier variant explicitly compares another feedback
route. Our current study instead asks hosted Jev about actual answer fields and
feeds its probabilities into a learned residual branch reading bound question/draft
memory during a second generation pass. That is a specific implementation
difference, not proof of an original general concept or better performance.

## What could become a defensible contribution

The prospective question is whether **case-specific contextual memory plus typed
external feedback** produces useful, preserved corrections on new tasks, and which
part of the feedback is necessary. R30's score rotations, mean and answer-type
control help distinguish interpretations that a donor shuffle alone cannot.
The proposed matched-memory training comparison would isolate contextualization
from changing adapter capacity or token positions. Neither experiment yet supports
broad superiority, and the memory proposal has engineering evidence only.

A positive public transfer result would justify stronger comparison with relevant
published controllers. A null result can still explain when verification fails to
become correction, but novelty must be argued against prior methods and measured
mechanisms. Renaming a known feedback loop or using Jev's brand cannot establish it.

Sparse Jev dispatch remains a later efficiency question: first show that the
repair candidate is useful, then compare a prospectively calibrated call policy
against the same model at matched budgets. Distilling Jev away entirely would
change the owner's requested inference-time Granite–Jev system and must be labeled
as a different system, not silently substituted.
