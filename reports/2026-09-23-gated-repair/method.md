# R25 mechanism and attribution

This describes the registered design, not a positive result. The BF16 v1 attempt
failed numerical admission; v2/v3 use float32 throughout. V3 explicitly records
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
queried once for each case, not once per layer or token. Its judgment enters
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

The read-only `research/diagnostics/gated_repair_report.py` summarizes the
registered recovery/damage, format, cutoff and work measures after the primary
tokenizer audit passes. Its tests were run red before implementation. It averages
seeds inside each problem, retains unavailable-feedback cases and distinguishes
all actually executed repair work from the retention replay's selected outputs.
It changes no generation, checkpoint selection, threshold or grading rule.
