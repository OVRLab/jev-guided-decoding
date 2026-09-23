# R25 mechanism and attribution

This describes the registered design, not a positive result. The BF16 v1 attempt
failed numerical admission; v2/v3/v4 use float32 throughout. V3/v4 explicitly record
unavailable feedback as null with neutral effective 0.5, never as a Jev judgment.

```text
Original question
      |
      v
Frozen Granite 4.0-1B: native full-vocabulary draft
      |
      +-------------------> Jev: probability draft answer is correct
      |                                |
      | exact original token IDs       | g = 1 - probability
      v                                |
New repair pass and fresh cache        |
  original prompt + exact draft +      |
  common request to check/correct      |
      |                                |
  frozen blocks 0..19                  |
      |                                |
      +--> trained rank-64 branch -----+
      |       bounded residual x g
      +<-------------+
      |
  frozen blocks 20..39
      |
  frozen final normalization + vocabulary head
      |
  Granite-generated repair token
      |
      +--> repeat with same g and its own cache until EOS/cap
```

Blocks are zero indexed. Only the final prompt position and subsequent repair
positions receive the residual. Draft positions are never retroactively changed;
each arm prefills the exact original token sequence into a fresh cache. Jev is
provides one judgment for each available case, not one per layer or token. V4
may make up to four charged attempts after explicit service overload; unavailable
feedback is null with a separately labeled neutral effective probability. Its judgment enters
internal hidden states without becoming an answer token or vocabulary mask.
The text-feedback control alone receives the probability in its user instruction,
rounded to four decimal places. All learned arms share the identical blind prompt.

The branch has 262,144 parameters: two bias-free matrices of dimensions 2048x64
and 64x2048. The original 1,631,750,144 parameters stay frozen; Jev's hosted
parameters and compute are unknown and are not included in these counts. The
branch starts at exactly zero output, with a fixed error-probability multiplier.
That explicit multiplier can affect hidden states without improving answers.

Training uses real native drafts, never authored errors or test answers. GSM8K
provides worked solutions; ARC supplies an answer label but no explanation. The
latter targets encourage terse answers, so malformed output and final-token
length are reported along with accuracy. Reference targets train only the new
branch. They never enter inference prefixes or Jev requests.

Both live and constant adapters use identical initialization, data, order and
optimizer schedule for each seed. Development accuracy selects an epoch before
any test draft is produced. The primary test remains untouched by that selection.
Shuffled and inverted feedback use the already selected live weights without
retraining; feedback sensitivity must be measured on final tokens and correctness,
not assumed from the explicit gate. A training benefit is distinct from a Jev
benefit, and a one-task gain is distinct from transfer or broad superiority.

The experimental run shares native drafts and one feedback receipt among its
paired arms. Actual experiment spending counts every generation/training step/API
attempt. Deployment accounting for an arm must include its own draft, repeat
prefill, repair generation and API call if used. The constant/blind arms need no
Jev call in deployment. Equal token ceilings do not imply equal actual work.

This is a serial Transformers research prototype. Multi-request isolation,
production throughput, colocated Jev weights and vLLM serving integration are not
implemented or benchmarked by this study.

The read-only `research/iterations/gated_repair_retry/details.py` summarizes the
registered recovery/damage, format, cutoff and work measures after the primary
tokenizer audit passes. Its tests were run red before implementation. It averages
seeds inside each problem, retains unavailable-feedback cases and distinguishes
all actually executed repair work from the retention replay's selected outputs.
It changes no generation, checkpoint selection, threshold or grading rule.

A read-only clock check at local 20:22:20–20:22:22 UTC found the worker reporting
20:21:41 UTC, approximately 40 seconds behind the workstation. Cross-machine
wall-clock ordering is therefore approximate. Within-worker selection/test order
and recorded monotonic generation durations remain the timing evidence; backup
timestamps are not model durations. No clock or scientific setting was changed.

Primary bootstrap intervals resample problems, pairing the two adapter seeds
inside each problem and stratifying by task. They describe uncertainty over
problems conditional on these two fitted seeds; they do not estimate a population
of training seeds. The registered 95% intervals are individual intervals, not a
simultaneous family guarantee across all contrasts and domains. An isolated
positive contrast remains visible even when the separate spending gate for a
larger-model follow-up is unmet. The gate does not redefine every endpoint as a
failure or erase partial gains.

## Independent source-data audit

[The source audit](data-audit.json) independently checked all 640 questions and
references, all 384 training targets, ARC choice relabeling, source splits and
exact normalized question overlap against five pinned upstream Parquet files.
All checks passed. The 24 GSM8K questions exposed in R23 are excluded. This does
not establish freedom from pretraining contamination or near-duplicate questions,
or certify the factual correctness of the upstream labels.

The helper was added while v4 was collecting training drafts, before inspection
of held-out performance. It neither changes the frozen worker nor recomputes
targets through the original preparation routine. Its two tests failed first
because the new module was absent; the resulting local suite passes 538 tests.
Reproduce with Python and PyArrow 21.0.0, using the manifest's upstream files
named `gsm8k-train.parquet`, `gsm8k-test.parquet`, `arc-train.parquet`,
`arc-validation.parquet` and `arc-test.parquet` in `<upstream>`:

```sh
python research/diagnostics/gated_repair_data_audit.py \
  --freeze research/protocols/gated-repair-retry-v4 \
  --upstream <upstream> \
  --exposed research/protocols/public-baseline-v1/cases.json \
  --save <new-audit.json>
```
