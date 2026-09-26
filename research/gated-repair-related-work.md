# R25 prior art and interpretive limits

Primary sources checked on 2026-09-23 after the protocol/data freeze. This note
changes no settings or endpoints and makes no exhaustive novelty claim.

- [ReFT](https://arxiv.org/abs/2404.03592) already trains hidden-representation
  interventions with a frozen backbone. A low-rank internal branch is established
  prior art; R25 studies its explicit gating by a separate hosted critic.
- [Self-Refine](https://arxiv.org/abs/2303.17651) studies iterative feedback and
  refinement without additional training. R25's blind/text controls test a simpler
  second-pass explanation of gains, without claiming to reproduce that method.
- [SCoRe](https://arxiv.org/abs/2409.12917) finds that offline supervised correction
  can suffer from behavior collapse and policy-distribution mismatch, and proposes
  multi-turn reinforcement learning. R25 uses supervised targets and no RL. Its
  draft generator stays fixed in both data collection and evaluation, which removes
  one source of policy drift but does not establish robust repair learning.
- [R22's prior-art discussion](learned-feedback-related-work.md) also records
  FiLM, actor/verifier retry adapters and latent-verifier work. R25 does not claim
  that conditional computation or learning to revise is a new principle.

A single correctness probability supplies an assessment, not the missing fact or
location of an error. Direct gating guarantees that the scalar controls the
branch's magnitude; it cannot guarantee that the learned direction repairs the
mistake, that a token changes, or that changed tokens improve correctness. The
fresh tests and matched controls distinguish these claims. Fine-grained feedback
or on-policy reward training remain separate prospective hypotheses.

Even a positive R25 result would establish only a bounded math/science pilot:
384 training examples, two seeds, one fixed layer and the stated token caps.
No current result proves architectural novelty, broad superiority, total-parameter
advantage, local Jev latency, or performance against a larger model. Hosted Jev's
internal parameter/computation budget remains unknown.
