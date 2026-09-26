# R16 targeted comparison with automatic and dynamic attention steering

Reviewed 2026-09-22 while the frozen R16 evaluation was running. This review does
not change its source, schedule, selection or claims. It is a targeted method
comparison, not a systematic literature review or a reproduced benchmark.
[Retrieval hashes](../reports/2026-09-22-adaptive-attention/related-source-manifest.json)
identify the retrieved sources; source downloads remain private.

## AutoPASTA

Zhang et al., *Model Tells Itself Where to Attend: Faithfulness Meets Automatic
Attention Steering*, arXiv 2409.10790v1. Reviewed Sections 2, 3 and 4.1.
The generator first proposes key evidence, an encoder maps it to original context
sentences, and selected heads emphasize those sentences. Layer-first profiling
reduces the head search. This establishes automatic evidence selection plus
frozen-weight attention steering as prior art. R16 substitutes typed Jev judgments
and tests refreshes against generated prefixes; it does not reproduce AutoPASTA's
sentence matching, profiling or benchmark results. [Primary text](https://arxiv.org/html/2409.10790v1).

## Spotlight

Venkateswaran and Contractor, *Spotlight Your Instructions: Instruction-following
with Dynamic Attention Steering*, EACL 2026; arXiv 2505.12025v2. Reviewed Section 2.1
and the experimental-model list. Spotlight measures current attention mass on
user-selected spans and applies a proportional log-ratio correction only below a
target, across all heads/layers. Its reported correction approaches a bounded
proportion; it is not an exact assignment to the target. Experiments include
Granite 3.1 8B, which is a different checkpoint from R16's Granite 4.0 1B.
R16 instead keeps selected-head strengths fixed and refreshes external relevance.
Dynamic source selection and dynamic intervention strength are distinct controls.
[Primary text](https://arxiv.org/html/2505.12025v2),
[venue record](https://aclanthology.org/2026.eacl-long.174/).

## CAFE

*CAFE: Retrieval Head-based Coarse-to-Fine Information Seeking to Enhance
Multi-Document QA Capability*, EMNLP 2025. Reviewed Sections 3, 4 and 5.1.
CAFE uses calibrated retrieval heads to filter and reorder documents, then boosts
candidate evidence in attention rather than deleting every remaining distractor.
The published steering condition targets question-to-evidence attention across
heads. R16 retains the complete original context and uses external Jev relevance
on a selected head set, including later generation positions. CAFE reports SubEM;
R16's whole-answer EM is not interchangeable with substring matching. Their
different models, contexts and graders prevent direct score comparisons.
[Primary paper](https://aclanthology.org/2025.emnlp-main.655.pdf).

## Consequences for the research claim

The project can contribute evidence about hosted typed judgments, final-token
ownership, failure accounting, free-text transfer and insertion-policy trade-offs.
It cannot claim to invent automatic evidence highlighting, attention steering or
dynamic inference-time intervention. A positive R16 result would establish a
measured effect for the tested system, not novelty or superiority over these papers.

Attention-mass-dependent strength and generator-only evidence selection are useful
future comparators. They require a new prospective study and matched implementation;
neither is represented by the current lexical or shuffled control. No such extra
inference is silently added to R16 in response to this review.
