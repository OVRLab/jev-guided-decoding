# HotpotQA data notice

HotpotQA questions, answers, source paragraphs and derived prompts/traces are
adapted from Yang, Qi, Zhang et al., *HotpotQA: A Dataset for Diverse, Explainable
Multi-hop Question Answering*, EMNLP 2018. They remain under
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), including within
mixed JSONL artifacts. The repository's MIT software license does not relicense
these portions.

[Dataset homepage](https://hotpotqa.github.io/) ·
[Authors' distribution](https://huggingface.co/datasets/hotpotqa/hotpot_qa) ·
[Paper](https://arxiv.org/abs/1809.09600).

Source: the authors' distractor-validation parquet, retrieved 2026-09-22, SHA-256
`c20b638ca82b21d04fe12e14ff417ad05153d4d215a65de54497fca4e972f7c6`.
R19 excludes all 466 R16/R17 questions and applies a new deterministic shuffle and a
3,072-token complete-prompt limit. It reserves three mechanical examples, 72
development questions and 240 test questions. Titles are joined to their sentences,
source IDs are added and supporting-fact annotations are excluded. All ten complete
paragraphs remain. Questions, answers and sentence content are preserved; answers
do not determine eligibility. The frozen manifest/eligibility log records hashes
and considered IDs. Added outputs, relevance judgments and metrics retain this
attribution for the incorporated data.
