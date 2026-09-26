# HotpotQA data notice

The HotpotQA portions of `hotpot.json`, `admission.json` and derived prompts/traces
are adapted from Yang, Qi, Zhang et al., *HotpotQA: A Dataset for Diverse, Explainable
Multi-hop Question Answering*, EMNLP 2018. They remain under
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), not the repository's MIT license.

[Dataset homepage](https://hotpotqa.github.io/) ·
[Authors’ Hugging Face distribution](https://huggingface.co/datasets/hotpotqa/hotpot_qa) ·
[Paper](https://arxiv.org/abs/1809.09600).

Source: distractor validation parquet, downloaded 2026-09-22. Its upstream SHA-256 is
`c20b638ca82b21d04fe12e14ff417ad05153d4d215a65de54497fca4e972f7c6`.
The university download timed out; the authors’ Hugging Face mirror supplied the data.
PyArrow was used only for local preparation, outside the runtime lockfile.

Changes: deterministic ID shuffle, complete-context length filtering, 12 reserved
mechanics examples plus 200 evaluation examples, paragraph titles joined to their
sentences, source IDs added, supporting-fact annotations excluded. `eligibility.json`
records every considered ID and decision. All ten paragraphs remain intact.
Original questions, answers and source sentence content are preserved; no answer
was used for selection. See the manifest for normalized-source and selected-data
hashes and the protocol for the exact length rule.
