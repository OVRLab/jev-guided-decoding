# Generated-answer development pilot v1 — 2026-09-20

**The development gate failed; the main evaluation was not admitted.** All 48
jobs ran on one L40S, with no provider/backend errors or unknown usage. The
independent audit verified that Granite generated every final answer and Jev
only evaluated intermediate steps. Jev changed seven local candidate selections
relative to Granite's likelihood ranking. These are development results, not a
held-out quality claim.

Eight GSM8K training problems and eight fresh ProofWriter development theories
ran at seed 42 in all three modes. Correctness includes incomplete and malformed
outputs in the denominator:

| Task | Single candidate | Likelihood selection | Intermediate Jev |
| --- | ---: | ---: | ---: |
| GSM8K | 6/8 | 5/8 | 5/8 |
| ProofWriter | 3/8 | 4/8 | 3/8 |

Across both tasks, frame completion was 14/16, 16/16, and 15/16; requested answer
format was valid in 14/16, 14/16, and 15/16 respectively. The 90% per-arm format
gate therefore failed. Granite sometimes produced a label and then EOS without
the closing tag, sometimes misspelled ENTAILED, and once answered a numerical
problem with `undefined`. The first two expose an output-interface problem;
`undefined` also reflects a reasoning failure and remains incorrect.

Single, likelihood, and Jev arms retained 38, 50, and 16 intermediate steps.
They had 6, 6, and 10 zero-step runs. Jev made 24 calls consuming 26,671 input
tokens; no Jev call evaluated a final answer. Total per-arm times were 17.90,
25.91, and 23.36 seconds, excluding loading/warm-up. Hardware was CUDA BF16 on
NVIDIA L40S, with original frozen Granite revision
`6a7381ba1f54d684ff508d991aeb7dc580157103` and Jev `jev-1.13.0`.

Inference source: `ebff3e513815bdf710cf6a09e9ebd4642f3206ec`.
The unchanged [summary](summary.json), [audit](audit.json), and
[frozen metadata](metadata.json) preserve this run. Raw external text and traces
remain in private backups under the dataset rights policy. Do not regrade this
pilot using a changed prompt or parser.

The development correction accepts an explicit model EOS as termination of a
plain final answer, retains the actual generated tokens, and changes new logic
requests to the easier-to-spell TRUE/FALSE/UNKNOWN contract. No misspelled answer
is silently repaired. The contract is versioned so old records keep their original
grading. A relational worked example is added to the shared prompt. All arms get
the same changes. A fresh recorded pilot on the same development selection must
pass before any test freeze; no test outputs were used for these corrections.

See the [replacement protocol](../../docs/generated-answer-experiment.md).
