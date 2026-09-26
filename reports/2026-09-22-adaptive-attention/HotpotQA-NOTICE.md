# HotpotQA attribution and data rights

HotpotQA questions, answers, source paragraphs and their derived prompts/traces
in this report come from Yang, Qi, Zhang et al., *HotpotQA: A Dataset for Diverse,
Explainable Multi-hop Question Answering*, EMNLP 2018. That content remains under
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), including when
stored alongside authored examples in a mixed JSONL artifact. The repository's
MIT software license does not relicense these portions.

[Dataset homepage](https://hotpotqa.github.io/) ·
[Authors' distribution](https://huggingface.co/datasets/hotpotqa/hotpot_qa) ·
[Paper](https://arxiv.org/abs/1809.09600).

The distractor validation parquet was retrieved on 2026-09-22 from the authors'
Hugging Face distribution, with upstream SHA-256
`c20b638ca82b21d04fe12e14ff417ad05153d4d215a65de54497fca4e972f7c6`.
The [full preparation notice](../../research/protocols/adaptive-attention-v1/HotpotQA-NOTICE.md)
describes deterministic shuffling, complete-context length filtering, reserved
mechanics examples, paragraph-title concatenation, source identifiers and exclusion
of supporting-fact annotations. Original question, answer and sentence content is
preserved. The report adds Granite outputs, Jev relevance judgments and evaluation
metadata; those additions do not replace the original data's attribution or terms.
