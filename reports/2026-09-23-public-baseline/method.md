# R23 method and limits

The [registered plan](../../research/benchmark-baseline-plan.md) and
[manifest](../../research/protocols/public-baseline-v1/manifest.json) govern this
run. Source implementation is commit `36d55ce`, after the pre-inference IFBench
null-argument amendment; initial registration was `36ebac9`. Eight source files,
two data files and exact model revisions are hashed. Prior R20/R21/R22 source
and data freezes remain intact.

The new [ten-task contract](../../research/benchmark-suite-contract-v1.md) fixes
reporting and admission requirements; it is not a completed ten-task evaluator.
R23 is a 76-problem **development diagnostic** in four domains:

| Development data | Number | Selection |
| --- | ---: | --- |
| MMLU-Pro validation | 28 | Two per each of 14 subjects |
| GSM8K main training | 24 | Deterministic hash-ranked problems; auxiliary to the ten-task suite |
| MuSR | 12 | Four per each of three narrative task families |
| IFBench | 12 | Deterministic hash-ranked prompts |

All selected MuSR and IFBench IDs become project development; exclude them and
content duplicates from a future untouched holdout. A later score on the full
source dataset includes exposed cases and must be labeled accordingly. The
source notices and normalization details are in the protocol directory. These
are public tasks and may have been in model pretraining; this run establishes
no contamination-free claim.

## Generator ownership and profiles

Each model receives the same question in its own native chat template. No answer
reference, worked solution, IFBench verifier kwargs, Jev call, retrieval tool,
forced choice grammar or intervention enters generation. There is no adapter or
training in this stage. Model weights are unquantized BF16, immutable, with
SDPA/PyTorch 2.8.0/Transformers 4.57.1 on one NVIDIA L40S. Each request owns its
cache; all generated IDs, prompt IDs and EOS outcomes are retained.

- Granite 4.0-1B: greedy, 2,048 new-token ceiling.
- Granite 4.2-3B: native thinking, temperature 1.0, top-p 0.95, top-k disabled,
  8,192 new-token ceiling, seed 2301 reset per question.

These are **different native-oriented profiles**, not equal compute, multiple-seed
best-quality comparisons or a causal estimate of parameter count. Version,
training and reasoning capability differ alongside size. The 3B runtime accepts
its default thinking template; only text after `</think>` becomes its final
answer. Unfinished thinking, empty responses and length stops remain explicit.
No input may be silently truncated; 16,384 is the admitted input ceiling.
The `load_and_hash_seconds` field in the original hardware record is evaluated
before its subsequent file-hashing expression; interpret it as loading time,
not the total hashing duration. Total study/cloud time includes that work.

No separate warm-up is excluded. Requests run serially in the frozen task order,
first 1B then 3B. CUDA-synchronized generation time includes each request
prefill/decode; cloud lifetime additionally includes installation, tests, downloads,
loading, backup and cleanup. These timings are not a serving-throughput test.

## Scoring and audit

Multiple choice and math use prospectively fixed explicit-final extraction, not
an LLM judge. The diagnostic's zero-shot instructions differ from official
MMLU-Pro five-shot evaluation. Report extraction failures separately from wrong
parsed answers. A wrong answer alone cannot distinguish a knowledge gap from
faulty reasoning. For IFBench, run upstream strict and loose verifiers; strict
is this diagnostic's primary and loose is also shown because the paper reports
that metric. Neither checker establishes the usefulness of the underlying prose.

Admission exposed a stateful upstream detail: strict removes null kwargs in place,
so loose can fail if given a fresh unnormalized dataset object. Before inference,
our wrapper was corrected to remove only null entries for both calls. All 12
selected verifier families then passed strict/loose invocation admission (24
calls on a fixed synthetic response). Simple keyword pass/fail fixtures also
passed. This validates invocation, not every verifier's semantic quality.

The offline audit binds question ID and prompt hash, reconstructs native prompt
IDs, verifies exact output decoding/EOS boundaries, final readout, model settings,
source/data hashes and planned coverage. Independent grading sees references
only after generation. Missing attempts stay in planned task denominators.
Paired 95% bootstrap intervals use 10,000 problem resamples with seed 2301 and
are exploratory; 12-example tasks cannot support a robust broad-superiority
claim. No ten-task aggregate is computed from these four diagnostic rows.

A subsequent [post-hoc choice readout](../../research/public-baseline-readout-amendment.md)
was specified after native-output inspection and before completing the 3B arm.
It preserves primary scores and adds reference-independent whole-option matching;
its results are a separately labeled development diagnostic.
