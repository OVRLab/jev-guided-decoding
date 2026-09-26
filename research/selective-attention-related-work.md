# R17 prior art and contribution boundaries

Targeted review on 2026-09-22 before R17 live inference; not a systematic novelty
search or a reproduced comparison. The retrieved primary pages and TypeSafe
documentation are identified by [source hashes](../reports/2026-09-22-selective-attention/related-source-manifest.json).

**Conditional calls already have precedents.** FLARE generates tentative text,
uses low token confidence to trigger retrieval, and regenerates with retrieved
evidence. R17's pilot/uncertainty gate follows that broad idea; it is not a claim
to invent on-demand assistance. Our gate calls an external relevance judge over
already supplied evidence, then changes internal attention rather than retrieving
new documents. A separately fitted benefit rule asks whether the intervention
helps, not merely whether the generator is uncertain.
[Jiang et al., EMNLP 2023](https://aclanthology.org/2023.emnlp-main.495/).

DRAGIN similarly investigates when and what to retrieve using the generator's
information needs. Its retrieval and query construction are different from R17's
fixed source inventory, typed external judgments and single bounded call. We have
not implemented DRAGIN, and cannot claim a benchmark advantage over it.
[Su et al., ACL 2024](https://aclanthology.org/2024.acl-long.702/).

**Attention steering also has precedents.** PASTA/AutoPASTA and CAFE motivate
selected evidence/head steering; Spotlight adapts intervention using observed
attention mass. See the earlier [method comparison](adaptive-attention-related-work.md).
R17 tests a different operation: keep the *entire evidence group's* unnormalized
partition unchanged while changing its internal allocation using Jev relevance.
This preserves that group's softmax mass in each controlled head/query and leaves
attention probabilities outside the group unchanged for the same Q/K. Subsequent
layers and generated tokens may still change. It is not a claim that all model
representations or all later attention remain unchanged.
[Spotlight primary text](https://arxiv.org/html/2505.12025v2).

The proposed contribution is the measured combination of selective typed judgment,
phase-dependent internal attention, mass-preserving evidence allocation, exact
generator-token attribution and explicit compute/API accounting on Granite. A
positive benchmark would establish this combination's tested benefit; it would
not by itself establish historical novelty or a generally superior LLM architecture.
No access to Jev hidden states, fused neural weights or colocated serving is implied.

TypeSafe's current [API](https://docs.typesafe.ai/api) and
[Noul contract](https://docs.typesafe.ai/primitives/noul) support the existing
batched per-source yes/no relevance questions. The
[citation cookbook](https://docs.typesafe.ai/cookbooks/citation_check) illustrates
performing ordinary checks before requesting a semantic judgment. R17 retains the
existing endpoint, typed validation, one-attempt transport and receipt accounting;
it changes dispatch policy and how successful judgments influence Granite.
