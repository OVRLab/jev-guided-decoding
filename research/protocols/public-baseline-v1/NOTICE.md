# Source attribution and split use

These normalized excerpts are project development diagnostics; this repository's
MIT license does not replace upstream data terms. Exact source URLs, revisions
and file SHA256 values are in `manifest.json`. Selection code is `prepare.py`.

- MMLU-Pro, TIGER-Lab, Wang et al. (2024), https://github.com/TIGER-AI-Lab/MMLU-Pro,
  [pinned dataset card](https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro/blob/b189ec765aa7ed75c8acfea42df31fdae71f97be/README.md)
  labels the data MIT. The separate source-code repository carries Apache 2.0;
  these are distinct metadata observations. Only validation data are used;
  no chain-of-thought references appear in generation cases.
- GSM8K, OpenAI, Cobbe et al. (2021), https://github.com/openai/grade-school-math,
  MIT, Copyright (c) 2021 OpenAI; [original license text](GSM8K-LICENSE.txt).
  Main training split only; full worked solutions are not copied here.
- MuSR, TAUR Lab, Sprague et al. (2023), https://github.com/Zayne-sprague/MuSR,
  [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) dataset. Twelve selected public benchmark problems are consumed as
  project development; their IDs must be excluded from future untouched holdouts.
- IFBench, Allen Institute for AI, Pyatkin et al. (2025),
  https://github.com/allenai/IFBench, [ODC-BY-1.0](https://opendatacommons.org/licenses/by/1-0/)
  data for research/education under
  Ai2's Responsible Use Guidelines; third-party generated data may carry additional
  source terms. Twelve selected source-test prompts become project development.
  Evaluator code is Apache 2.0 and installed separately at the pinned revision.

Transformations: deterministic subset selection, explicit zero-shot final-answer
instructions for math/multiple choice, alphabetic option labels, separate oracle
metadata. IFBench prompts are unmodified. No claim of pristine pretraining data
or absence of contamination. The generation runner reads only `cases.json`.
