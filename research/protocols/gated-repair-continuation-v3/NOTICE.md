# R25 data attribution and changes

This directory freezes an experimental subset; it is not an official benchmark
release or score. IDs, question formatting, option-label normalization, targets,
and train/development/test allocation were produced by `gated_repair/prepare.py`.
The manifest preserves immutable upstream revisions and original file digests.

- GSM8K: OpenAI, [dataset](https://huggingface.co/datasets/openai/gsm8k),
  [original repository](https://github.com/openai/grade-school-math), MIT license;
  the original license is retained in `GSM8K-LICENSE.txt`. Training solution
  calculator markup is removed; question text and numeric answers are retained.
- ARC-Challenge: Allen Institute for AI,
  [dataset and attribution](https://huggingface.co/datasets/allenai/ai2_arc),
  Clark et al., *Think you have Solved Question Answering? Try ARC, the AI2 Reasoning
  Challenge* (2018), [paper](https://arxiv.org/abs/1803.05457).
  ARC-derived content and our normalized adaptations are provided under
  [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
  Choice labels are mapped to consecutive letters while preserving option order;
  question/option content and answer identity are otherwise retained.

These dataset terms apply to the respective data portions, separately from the
repository's code license. Public prompts and draft answers are sent to TypeSafe
for the registered one-question judgment; references are never sent. Original
weights and Jev weights are not included here. Source-test cases consumed in R25
are exposed pilot evaluation data for all future research, not a reusable untouched
final benchmark sample. No claim of absence of pretraining contamination is made.
