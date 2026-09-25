# R28 focused prior-art review

Primary sources checked on 2026-09-25. This is a targeted comparison, not an
exhaustive novelty search or a reproduction of the cited methods. Claims about
our method depend on our own controlled results.

| Prior work | Relevant overlap | Difference and implication for this study |
| --- | --- | --- |
| [SCORE: Small Language Models Need Strong Verifiers to Self-Correct Reasoning](https://arxiv.org/abs/2404.17140), Zhang et al., Findings of ACL 2024 | Explicitly separates verification from refinement and studies external versus self-verification for small models. Its method trains a refiner using filtered critique/correction data. | Separation of deciding when to revise from performing revision is established prior art. R28 isolates an additional scalar feedback channel into a fixed internal adapter, at matched repair counts. We must not claim invention of verifier-triggered correction. Method section 2 inspected in full. |
| [Self-Refine](https://arxiv.org/abs/2303.17651), Madaan et al., 2023 | Uses generated textual feedback and iterative refinement without additional task training. | Our no-feedback second pass is a simpler control, not a reproduction of Self-Refine. The studied feedback is a probability scaling an internal residual, not a generated critique. Abstract-level comparison. |
| [ReFT](https://arxiv.org/abs/2404.03592), Wu et al., 2024 | Learns interventions on hidden representations of a frozen language-model backbone. | A learned internal intervention or low parameter count alone does not establish novelty. Our question is whether the external judgment usefully controls such an intervention. Abstract/method overview comparison. |
| [SCoRe: Training Language Models to Self-Correct via Reinforcement Learning](https://arxiv.org/abs/2409.12917), Kumar et al., 2024 | Studies limitations of supervised correction and learns correction behavior with reinforcement learning. | Our adapter was supervised on a small fixed dataset; this study neither implements RL nor determines whether another training procedure would solve the observed limitations. Abstract-level comparison. Do not confuse SCoRe with Zhang et al.'s SCORE. |
| [RouteLLM](https://arxiv.org/abs/2406.18665), Ong et al., 2024/2025 | Learns routing between language models to balance response quality and cost. | Our selectors allocate a fixed number of second passes through one generator. Equal repair counts isolate an allocation question but do not establish equal realized compute or a production latency advantage. Abstract-level comparison. |
| [IFEval](https://arxiv.org/abs/2311.07911), Zhou et al., 2023, and [IFBench](https://arxiv.org/abs/2507.02833), Pyatkin et al., 2025 | Evaluate verifiable instruction constraints; IFBench specifically examines generalization to additional constraint types. | Rule compliance is independently measurable but is not comprehensive semantic answer quality. R28 transfers from the previously inspected IFBench results to an eligible IFEval cohort; it cannot claim pretraining decontamination. Dataset code and metadata inspected. |

The candidate contribution is an empirical comparison of repair selection and
case-specific scalar control within this particular Granite–Jev system, together
with explicit measurement limits. A new general architectural principle, an
optimal insertion layer, and superiority over larger models remain unestablished.

Related historical reviews cover [activation steering and decoding](related-work.md),
[R22 representation bridges](learned-feedback-related-work.md) and
[R25 correction training](gated-repair-related-work.md). These references also
limit novelty claims; they are not independent confirmation of our results.
