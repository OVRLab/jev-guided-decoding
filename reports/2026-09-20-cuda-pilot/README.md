# Single-L40S CUDA integration pilot

All twelve planned development jobs completed without provider/backend errors or
unknown usage. Each of the four executed arms matched 2/3 independent verdicts.
This establishes CUDA integration; it does not demonstrate added accuracy from
intermediate guidance. The 200-problem held-out study was then frozen and started.

| Executed arm | Correct / planned | Completed | Total seconds | HTTP attempts |
| --- | --- | --- | --- | --- |
| Step guidance + fixed choice | 2/3 | 2/3 | 7.15 | 9 |
| Unguided reasoning + same choice | 2/3 | 2/3 | 33.31 | 3 |
| Final-only filtering + same choice | 2/3 | 3/3 | 37.18 | 8 |
| Direct Jev choice | 2/3 | 2/3 | 0.78 | 3 |

Uncertain decisions count incorrect, separately from semantic UNKNOWN. The
Granite-alone path completed twice but produced no exact canonical label; one
answer began with the correct label, which is recorded only as a secondary
formatting diagnostic. Neither guided nor final-filtered search completed a
generated final answer. Their subsequent code-defined Jev choices remain separate
outcomes, not repaired proofs. See the [aggregate results](summary.json).

Guided generation used 379 tokens, 438 padded decode slots, and 16,170 prefill tokens;
unguided used 2,798 / 3,342 / 101,490; final-only used 3,012 / 3,606 / 110,559.
Direct Jev used no Granite generation. The leading-claim audit checks only
recognized atomic consequences, not complete reasoning or cited justifications.
Equal ceilings did not mean equal work. The [MPS pilot](../2026-09-20-proofwriter-pilot/README.md)
remains a separate historical record; sampling and paths differ across devices,
so these timings are not a controlled hardware speedup measurement.

## Provenance

- Source: `62f6bedd992afb522421b4fbf73a5fcfd02f8011`, clean at freeze.
- Same three distinct development theories as the MPS pilot; seed 42; unchanged
  prompts, probability thresholds, and 90-second per-job ceiling.
- Original `ibm-granite/granite-4.0-1b`, revision
  `6a7381ba1f54d684ff508d991aeb7dc580157103`; zero trainable parameters.
- One NVIDIA L40S, 46,068 MiB reported memory; driver 580.173.02; CUDA BF16;
  Torch 2.8.0+cu128, Transformers 4.57.1, Python 3.12.13; pinned Jev `jev-1.13.0`.
- Model loading (1.17 seconds) and two-token batch-one/batch-three warm-ups excluded.
- Raw runs SHA-256:
  `289ac8b9eeb8aad5f88731c334a982f56f15a6f627cb864953944555f7986157`.
- All 174 offline tests also passed on the server before the live pilot.

Raw external examples and traces remain in private study storage; this report
publishes aggregates. The [study protocol](../../docs/proofwriter-experiment.md)
explains dataset rights, independent grading, statistical controls, and limits.
The full evaluation and synthetic stress test remain in progress; there is no
held-out accuracy conclusion yet. No package or model release has been published.
