# Related work and source ledger

Reviewed 2026-09-21. These are primary papers and vendor/implementation sources.
This is a targeted architecture review, not a systematic literature review or a
claim to have exhaustively found every Jev integration. Abstract-level reviews
are identified; reported gains in other work are not independently reproduced here.

## Closest decoding precedents

| Source | Relevant contribution | Boundary for our design |
| --- | --- | --- |
| Yang and Klein, **FUDGE: Controlled Text Generation With Future Discriminators**, NAACL 2021 ([paper](https://aclanthology.org/2021.naacl-main.276/)) | Learns a predictor on partial sequences and uses it to adjust a frozen generator's probabilities | Supports the output-logit insertion family; its learned future-attribute predictor is not interchangeable with an arbitrary Jev support judgment. Reviewed the primary abstract/method description. |
| Mudgal et al., **Controlled Decoding from Language Models**, ICML 2024, arXiv v3 ([full text](https://arxiv.org/html/2310.17022v3)) | Learns a prefix value function for tokenwise control; also considers blockwise control | Its mathematical guarantees depend on the value-function formulation. A short local Jev judgment is not established as the required value. Reviewed method/value definition and inference discussion. |
| Huang et al., **DeAL: Decoding-time Alignment for Large Language Models**, ACL 2025; arXiv v3 ([full text](https://arxiv.org/html/2402.06147v3)) | Treats decoding as heuristic search with customizable rewards and lookahead | Particularly close to the proposed training-free rollout/scoring integration. General lookahead reward-guided decoding is established prior art. Reviewed the abstract and method text. |
| Liu et al., **DExperts: Decoding-Time Controlled Text Generation with Experts and Anti-Experts**, ACL 2021 ([paper](https://arxiv.org/abs/2105.03023)) | Combines generator and expert/anti-expert language-model output distributions | Jev's typed answers are not a language model distribution over Granite's vocabulary. We cannot directly add “Jev logits” by analogy. Reviewed abstract. |
| Zhao et al., **Probabilistic Inference in Language Models via Twisted Sequential Monte Carlo**, 2024 ([paper](https://arxiv.org/abs/2404.17546)) | Uses learned twisting functions and sequential Monte Carlo to guide generation | Relevant for future-value estimation and maintaining several paths; more complex than the proposed bounded first prototype. Our local-score policy is not an implementation of its exact inference target. Reviewed abstract. |

A subsequent [targeted method comparison](decoding-method-comparison.md) reads FUDGE Section 3, Controlled Decoding Sections 2–3, and DeAL Section 3.2.2 against the frozen R13 implementation. It separates local claim support from future-answer value and records the exact KL reference distribution.

## Actual hidden-state intervention and critic quality

| Source | Relevant contribution | Boundary for our design |
| --- | --- | --- |
| Dathathri et al., **Plug and Play Language Models: A Simple Approach to Controlled Text Generation**, ICLR 2020, arXiv v4 ([paper](https://arxiv.org/abs/1912.02164)) | Backpropagates a differentiable attribute signal to steer hidden activations during generation | Frozen generator weights do not imply no differentiability requirement. The hosted Jev API supplies no such gradient. Reviewed abstract. |
| Li et al., **Inference-Time Intervention: Eliciting Truthful Answers from a Language Model**, NeurIPS 2023, arXiv v6 ([paper](https://arxiv.org/abs/2306.03341)) | Finds selected attention-head directions using labeled examples and shifts activations at inference | Evidence for calibrated interventions in other models; neither a known Granite layer nor a generic Jev-to-vector mapping. Reviewed abstract and authors' method description. |
| Lightman et al., **Let's Verify Step by Step**, 2023 ([paper](https://arxiv.org/abs/2305.20050)) | Compares trained process and outcome supervision for mathematical reasoning; introduces step-level data | Validating mathematical steps is a trained, evaluated critic capability. A general semantic scorer is not a process reward model merely because we ask a step question. Reviewed abstract. |

## Recent work relevant to a publication claim

| Source | Why retain it | Review status |
| --- | --- | --- |
| Markovic-Voronov et al., **Sampling for Quality: Training-Free Reward-Guided LLM Decoding via Sequential Monte Carlo**, 2026, arXiv v1 ([paper](https://arxiv.org/abs/2604.16453)) | Studies reward-augmented sampling with prefix-only and lookahead variants while preserving model weights | Abstract-level screening of a preprint. Do not claim novelty for training-free reward-guided sampling; full-method comparison is required before submission. |
| **Look Before You Leap: A Lookahead Reasoning Quality Gate for Speculative Decoding**, EACL 2026 ([paper](https://aclanthology.org/2026.eacl-long.367/)) | Uses base-model hidden-state geometry to gate lookahead prefixes without an auxiliary reward model | Abstract-level screening. This is a relevant critic-free alternative, not evidence that a hosted Jev judgment can read hidden representations. |
| Agrawal et al., **The Hidden Bias of Process Reward Models: PRISM for Rewarding the Right Reasoning**, 2026, arXiv v1 ([paper](https://arxiv.org/abs/2606.09078)) | Investigates false-positive step rewards and relative-comparison training | Abstract-level screening of a preprint. Supports examining discrimination and ranking; its findings do not independently diagnose Jev or our traces. |

## Exact implementation and provider contracts

- [Pinned Granite configuration](https://huggingface.co/ibm-granite/granite-4.0-1b/blob/6a7381ba1f54d684ff508d991aeb7dc580157103/config.json)
  and [Transformers v4.57.1 implementation](https://github.com/huggingface/transformers/blob/v4.57.1/src/transformers/models/granitemoehybrid/modeling_granitemoehybrid.py):
  all-attention, zero-expert configuration despite the hybrid-family class name;
  final norm/head/scaling path inspected directly.
- [TypeSafe HTTP API](https://docs.typesafe.ai/api.md) and
  [models](https://docs.typesafe.ai/models.md): text/structured state, typed judgments,
  current model/usage contract. No documented tensor or gradient interface was
  found in these pages. A colocated deployment has not been obtained or measured.
- [Noul](https://docs.typesafe.ai/primitives/noul.md),
  [Score](https://docs.typesafe.ai/primitives/score.md), and
  [confidence](https://docs.typesafe.ai/confidence.md): use the primitive matching
  the question, and distinguish its probability/level distribution from
  independently measured accuracy. Scores for different questions are not
  automatically comparable calibrated utilities.
- [Jev 1.13 limitations](https://docs.typesafe.ai/model-jaggedness/jev-1.13.md):
  the vendor identifies numerical precision, indirect reasoning and irrelevant
  state as weaknesses. This motivates testing local semantic judgments; it is
  not a substitute for measuring their accuracy on Granite proposals.
- [TypeSafe reranking cookbook](https://docs.typesafe.ai/cookbooks/rerank_typesafe.md):
  an example of per-candidate judgments and independent ranking evaluation.
  Retrieval relevance differs from reasoning correctness; its thresholds/results
  must not be transplanted to this task.

Public retrieval metadata and content hashes for the inspected implementation and
TypeSafe pages are preserved in the [source manifest](../reports/2026-09-21-architecture-reassessment/source-manifest.json).
Downloaded vendor pages stay in ignored local storage; they are not redistributed
as our research. Online pages can change, so an access date alone is not a version
pin. The scholarly links above give the version/venue reviewed where applicable.

## Plausible contribution, still to be established

A transparent negative result and a carefully controlled study of a hosted typed
critic steering a small frozen generator could be useful. The candidate contribution
is the measured boundary between judge capability, candidate availability,
control policy, insertion point and cost, with explicit final-token ownership.
It is not the invention of reward-guided decoding, process verification, or
activation steering. A positive Jev/Granite result and a novel method are separate
claims, and neither is established by this review.
