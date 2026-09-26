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

## Expanded search while R31 runs, 26 September 2026

The following primary sources were located after R31 was frozen and launched.
They extend the literature record without changing that experiment or interpreting
partial results. This is a targeted search, not an exhaustive novelty review.

| Primary source and inspected scope | Relation and limit |
| --- | --- |
| [PoPE, İşcan, v1](https://arxiv.org/html/2607.12962v1), abstract and methods §2.1–2.2 | Tests small code generators with scaffold-matched and mismatched feedback controls through prompts and trained adapters. Its screening results do not establish content-attributable superiority or equivalence. Our attribution controls and separation of audit validity from quality have clear methodological precedent; its code-execution endpoint and small resistant cohort differ from ours. |
| [CRN v2, Kishore, v1](https://arxiv.org/html/2609.16145v1), abstract and method §3 | Adds a trained logit correction module to frozen Gemma, with supervised/preference training and a KL preservation term. The reported correction/capability tradeoff is measured on limited cohorts. Frozen weights and preservation goals are established design ideas; our hosted inference-time judgments and internal context-memory branch differ. The paper itself avoids an architectural novelty claim. |
| [Latent Reward Steering, Li et al., v3](https://arxiv.org/html/2606.00726v3), method §3.2–3.5 and limitations | A learned reward model supplies gradients in sparse-autoencoder latent space, with a reward/confidence gate deciding when to intervene. This is a close precedent for adaptive internal correction, though our branch consumes hosted probabilities rather than differentiating through Jev. The authors acknowledge added computation and a training/inference mismatch. |
| [Memory Inception, Liu et al., v2](https://arxiv.org/abs/2605.06225v2), abstract | Inserts text-derived KV banks at selected layers without training. This overlaps with internal memory-based steering; our current memory is read by a trained residual branch and does not append KV entries. No method or performance reproduction was attempted. |
| [Readout Feedback, Kamiya et al., v1](https://arxiv.org/abs/2608.24136v1), abstract | Uses intermediate prediction probabilities to steer recurrent latent dynamics on Sudoku/maze tasks. Closed-loop probability feedback is therefore not a new general concept; the studied recurrent models and tasks differ from Granite autoregressive repair. |

These sources strengthen the need for a specific, demonstrated contribution. A
defensible claim could concern the measured usefulness or failure of typed hosted
feedback under matched contextual-memory controls and public transfer. It cannot
be merely “a verifier inside an LLM,” a low-rank branch, preservation training,
or an on-demand gate. Direct comparisons remain future work; cited performance
numbers are not treated as scores on our data or proof about our implementation.
