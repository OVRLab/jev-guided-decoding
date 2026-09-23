# R22: related work and limits on novelty

Checked against primary sources on 2026-09-23 while R22 test generation was
running. This is a focused prior-art check, not an exhaustive novelty review.
It did not change the frozen architecture, training, selection, or endpoints.

| Prior work | Relevant overlap | Distinction in this pilot |
| --- | --- | --- |
| [ReFT: Representation Finetuning for Language Models](https://arxiv.org/abs/2404.03592) | Trains interventions on representations while retaining a frozen language-model backbone. | Our bounded residual at one block is conditioned on two external local-claim probabilities. A small learned hidden-state intervention is already an established approach. |
| [FiLM: Visual Reasoning with a General Conditioning Layer](https://arxiv.org/abs/1709.07871) | Conditions neural computation on another input through feature-wise modulation. | Our formula is a bounded low-rank residual, not FiLM's affine feature modulation; conditioning internal computation is not itself a new principle. |
| [EchoTrust: Evidence-Based Actor–Verifier Reasoning for Echocardiographic Agents](https://arxiv.org/html/2604.06347v1) | Sections 3.1–3.2 describe verification-guided second-pass inference and distinct trained adapters for initial actor, verifier, and retry actor on a frozen multimodal backbone. | R22 uses a separately hosted, unchanged Jev verifier, a two-number non-text feedback channel and one internal residual module. It does not train a verifier or separate initial actor, and does not implement EchoTrust's posterior acceptance loop. The broad idea of learning to revise under verifier feedback already has close prior art. |
| [Tiny Inference-Time Scaling with Latent Verifiers](https://arxiv.org/abs/2603.22492) | Verifies intermediate hidden representations of diffusion-transformer image generators to reduce verification overhead. | Its verifier reads generator features for candidate evaluation. Our Jev reads a textual claim; its probabilities condition Granite's subsequent hidden states. We neither expose Granite's activations to Jev nor implement a latent verifier. |

No empirical comparison with these methods was run. Their reported gains do not
support claims about Granite+Jev. The defensible contribution, if supported by
R22's results, is the particular integration and its controlled evidence: exact
draft-token retention, reference-free local feedback, a bounded trained internal
bridge, and matched constant/permuted/oracle feedback comparisons. Even a positive
test would require replication and broader transfer evidence before claiming a
generally better architecture. A negative test remains evidence about this
specific design and training setup, not a proof that all verifier-conditioned
architectures fail.

See the [frozen protocol](learned-feedback-bridge-plan.md) and
[architecture and controls](../reports/2026-09-23-learned-feedback/method.md).
