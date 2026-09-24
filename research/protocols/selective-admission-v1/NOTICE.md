# R26-A exposed development data and checkpoint attribution

These 50 cases are drawn only from the already-exposed R23 development and R25
development cohorts. This is not a fresh benchmark evaluation. Source bindings
and upstream origins remain in the linked immutable manifests:

- [R23 sources, authors and data terms](../public-baseline-v1/NOTICE.md), covering
  14 MMLU-Pro validation questions, six MuSR problems and ten IFBench prompts.
- [R25 sources, authors and data terms](../gated-repair-retry-v4/NOTICE.md), covering
  ten GSM8K development questions and ten ARC-Challenge development questions.

GSM8K's MIT notice is retained in [GSM8K-LICENSE.txt](GSM8K-LICENSE.txt).
ARC-derived content and adaptations remain CC BY-SA 4.0; MuSR remains CC BY 4.0;
IFBench remains ODC-BY-1.0 with its source conditions. Repository software licensing
does not replace these dataset terms. R26 changes only output instructions for
choice/math cases; IFBench prompts remain unmodified. References stay separate
and are never supplied to the generator or Jev.

The two safetensors files are the R25 seed-2501 development-selected live epoch 2
and constant epoch 1 residual adapters, copied byte-for-byte. They contain only
262,144 new parameters apiece, not the original Granite weights. Their exact
hashes and selection provenance bind to the [R25 report](../../../reports/2026-09-23-gated-repair/README.md).
Use requires the separately obtained pinned IBM Granite checkpoint and its
[Apache 2.0 model terms](https://huggingface.co/ibm-granite/granite-4.0-1b).
No Jev weights or credentials are included.
