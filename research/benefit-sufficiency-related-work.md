# R19: benefit routing and sufficiency are distinct claims

Targeted primary-source comparison on 2026-09-22 while the frozen study runs.
This is a literature check, not a protocol amendment, benchmark reproduction or
systematic novelty search. No held-out outcomes informed it.

| Prior source | Relevant method | Boundary for R19 |
| --- | --- | --- |
| [RouteLLM, arXiv v4](https://arxiv.org/html/2406.18665v4), §§3.1–4.2 | Predicts which model will win from comparison data, then applies a cost threshold to route between two generators; evaluates quality and strong-model call fraction. | Learning relative usefulness and trading calls for quality already have precedents. R19 predicts a numerical guided-minus-native gain from one generator's native attention and structural features, then optionally asks an external typed judge inside the same prefill. It neither implements RouteLLM nor compares against it. |
| [AutoPASTA](https://arxiv.org/abs/2409.10790), primary abstract rechecked; detailed method review in the [R16 comparison](adaptive-attention-related-work.md) | Automatically selects contextual information and steers attention during inference with unchanged model parameters. | Automatic source selection and frozen-weight attention steering are established. R19 additionally tests a separate sufficiency-dependent choice between source and existing-instruction attention. That combination is a candidate contribution, not proof of historical priority. |
| [Lookback Lens, EMNLP 2024](https://aclanthology.org/2024.emnlp-main.84/), primary abstract rechecked; detailed method review in the [R18 comparison](boundary-attention-related-work.md) | Uses context-versus-generated-token attention ratios in a detector and classifier-guided decoding. | Reading native attention to guide generation is established. R19 observes before any generated token, predicts treatment gain rather than hallucination, and retains one prefill. |
| TypeSafe [semantic-find cookbook](https://docs.typesafe.ai/cookbooks/semantic_find), API source inspected during R19 preparation | Separates relevance from whether a source contains an answer. | The semantic distinction itself is not new. R19 tests whether a joint sufficiency judgment usefully controls Granite's internal attention and its own generated abstention. |

There are three separate empirical claims: dual guidance improves generated
answers; the benefit gate allocates calls usefully; and question-specific Jev
judgments add value beyond fixed or shuffled control signals. They can have
different answers. A gain over native alone cannot establish all three, and a
positive benchmark does not by itself establish novelty. Conversely, failing a
stronger control does not erase an observed native-relative gain; it narrows its
attribution.

The candidate contribution is the tested combination and its measured limits:
typed relevance/sufficiency, benefit-conditioned dispatch at an internal boundary,
source/instruction attention steering, preserved final-token ownership and explicit
call/work accounting. Whether this combination merits a methods contribution
requires broader literature review, independent scientific review and replication.
No cited paper's published performance is treated as a Granite/Jev result.
