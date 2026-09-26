# R18: attention observations, conditional assistance and prior methods

Method-focused primary-source review on 2026-09-22 during the frozen GPU study.
This adds no implementation, tuning, live comparator or statistical claim. It
extends the [R16 steering review](adaptive-attention-related-work.md) and
[R17 routing review](selective-attention-related-work.md). Reported results in
other papers are not measurements of Granite/Jev.

| Prior method | Signal and intervention described by its authors | Relationship to R18 |
| --- | --- | --- |
| [Lookback Lens, EMNLP 2024](https://aclanthology.org/2024.emnlp-main.84.pdf), §§2–3 | A linear detector uses per-head context-versus-generated-token attention ratios. Guided decoding samples several chunks and selects the detector's preferred continuation. | Attention-based detectors and generation control already exist. R18 observes source distributions before the first output, then optionally changes selected attention logits; it neither samples nor ranks output chunks. A pre-output ratio with no generated-token history cannot simply reuse Lookback Lens's decoding feature contract. |
| [RAUQ, arXiv v1 2025](https://arxiv.org/html/2505.20045v1), §§3–4 and Algorithm 1 | Selects heads using average attention to preceding generated tokens, then combines recurrent attention and token probabilities into sequence uncertainty. It needs no task labels. | Cheap native attention signals are prior art. R18 uses a development-supervised benefit threshold on one prompt query, not RAUQ's sequence uncertainty. Algorithm 1 chooses heads over the generated sequence, so using that exact rule before any output would require a different, prospectively validated adaptation. |
| [SeaKR, ACL 2025](https://aclanthology.org/2025.acl-long.1312.pdf), §§3.1–3.4 | Uses multiple sampled generations and a regularized Gram determinant of EOS hidden states to decide retrieval, rerank snippets and choose a reasoning strategy. | Internal-state conditional assistance and utility-sensitive retrieval already exist. R18 has supplied evidence, an external relevance scorer and one retained prefill. It does not implement SeaKR's sampling, retrieval or representation-consistency estimator. |
| [CtrlA, Findings ACL 2025](https://aclanthology.org/2025.findings-acl.652.pdf), §§3.2–3.3 | Derives honesty/confidence directions from contrastive representations using PCA. It steers representations and monitors token confidence to trigger retrieval, including refusal handling and segment regeneration. | Monitoring model internals while steering inference is established work. R18 uses source-attention statistics and fixed source-key logit biases; it learns no honesty vector, changes no evidence and does not regenerate an output segment. |
| [DSSP-RAG, EMNLP 2025](https://aclanthology.org/2025.emnlp-main.549.pdf), §§3.2–3.5 | Compares semantically equivalent query representations for retrieval decisions, filters evidence using cross-layer attention differences, and combines internal/external streams through mixed attention at a selected layer with a training objective. | Conditional, layer-specific external-knowledge integration is also prior art. R18 preserves a single native layer loop and unchanged weights; Jev returns text-conditioned source judgments, not a second stream of latent vectors. These architectures and their training requirements are distinct. |

Review depth: the linked primary method sections, algorithms/equations and relevant
limitations were read. This is not a full code reproduction, comprehensive survey,
or a controlled performance comparison. R18 has no implemented Lookback Lens,
RAUQ, SeaKR, CtrlA or DSSP-RAG arm, so it cannot claim to beat them.

## What the present experiment can establish

The concrete contribution being tested is a bounded Jev callback inside a
single Granite prefill, with development-frozen dispatch, unchanged weights,
branch parity, exact work accounting and three-domain held-out controls. An
implementation of that combination is not evidence that its individual principles
are new, nor that it is the first such combination in the literature.

Our design inference from this review is that predicting **whether the existing
treatment helps** is different from predicting whether the native answer is wrong.
An uncertain model may need evidence that is absent, or may be unable to use
relevant evidence. Conversely, a confident wrong answer may benefit from guidance.
R18 therefore fits guided-minus-native development quality, and tests routing
against expected random calls at the same request count. Attention entropy and
head disagreement remain fallible proxies; their names do not establish calibrated
uncertainty, truthfulness or a readable reasoning state.

Source count and granularity also matter. A single source has zero normalized
source entropy/disagreement, and R18's fixed uniform-score convention makes its
relevance treatment a no-op. That follows from the published implementation, not
from test-set tuning. The descriptive supplement records such calls explicitly.
Any future source-count gate, different source segmentation, learned readout,
honesty intervention or later-token callback would need a new development freeze
and fresh evaluation; none is silently added to R18.
