# Granite-generated answer study — 2026-09-20 UTC

**This configuration did not demonstrate an accuracy improvement from Jev.**
Granite generated the final answer in every arm. Math accuracy was lower with Jev;
logic accuracy was nearly unchanged. Against three-candidate likelihood selection,
the math decrease remained below zero across the adjusted confidence interval.
The comparison with single-candidate Granite was inconclusive about a population
math difference. No model weights were trained or changed.

## Final-answer accuracy

| Task | Granite single candidate | Granite likelihood selection | Granite + intermediate Jev |
| --- | ---: | ---: | ---: |
| GSM8K math | 61.5% (369/600) | 67.8% (407/600) | 56.5% (339/600) |
| ProofWriter logic | 52.7% (316/600) | 52.8% (317/600) | 52.5% (315/600) |

Each cell covers 200 distinct problems × three seeds. Seeds are repeated
measurements of the same problem, not 600 independent problems. All 3,600 planned
jobs were recorded. Two incomplete single-candidate math answers and every invalid
format count as incorrect. Completed/valid-format totals across both tasks were
1,198/1,194 for single, 1,200/1,196 for likelihood, and 1,200/1,196 for Jev, out of
1,200 jobs per arm. There were no provider/backend failures or unknown usage.

## Prespecified paired comparisons

Differences and intervals are percentage points. Each interval is 98.75%, using
5,000 paired problem-cluster bootstrap draws for four prespecified contrasts
(Bonferroni nominal familywise 95%). Wins/losses/ties compare each problem's mean
accuracy across three seeds. The broad positive criterion required all four lower
bounds above zero; it was not met.

| Comparison | Jev accuracy difference | Adjusted interval | Problem wins / losses / ties |
| --- | ---: | ---: | ---: |
| GSM8K: Jev − single | -5.00 | [-12.00, +1.83] | 43 / 52 / 105 |
| GSM8K: Jev − likelihood | -11.33 | [-18.17, -4.50] | 25 / 54 / 121 |
| ProofWriter: Jev − single | -0.17 | [-4.83, +4.17] | 19 / 19 / 162 |
| ProofWriter: Jev − likelihood | -0.33 | [-5.33, +4.17] | 22 / 20 / 158 |

This is evidence about the complete selection-and-rejection policy under this
staged prompt. It does not isolate ranking from early stopping, and it does not
establish that Jev cannot help another configuration. Settings were not retuned
on these test outcomes, and no failed or unfavorable run was removed.

## What ran and what the audit established

The [frozen protocol](../../docs/generated-answer-experiment.md) compares one
sampled intermediate candidate, three candidates selected by mean model log
probability, and three candidates selected by Jev support/progress judgments.
Every arm ends with the same greedy Granite final generation, including when no
intermediate step survives. Jev never scores or supplies that final answer.
This is a staged-generation baseline, not an unrestricted default-chat benchmark.

The source was `966fdb7518f67b751a17834dc3e92d329997fe65`, frozen before test
inference, using original `ibm-granite/granite-4.0-1b` revision
`6a7381ba1f54d684ff508d991aeb7dc580157103`, CUDA BF16, and returned Jev version
`jev-1.13.0`. Runtime metadata records 1,631,750,144 parameters and zero trainable
parameters. One L40S 48 GB served all arms in rotated order. Torch was 2.8.0+cu128,
Transformers 4.57.1, and Python 3.12.13. No retained-prefix serving cache or vLLM
extension was used.

Development used separate GSM8K train and ProofWriter dev problems. The
[first pilot](../2026-09-20-generated-answer-pilot-v1/README.md) failed its format
gate and remains preserved. A development-only EOS/output-contract correction
was admitted by the [second pilot](../2026-09-20-generated-answer-pilot-v2/README.md).
The main test then froze 200 fresh GSM8K test problems and 200 distinct ProofWriter
OWA D5 test theories. The logic sample has 67 TRUE, 67 FALSE, and 66 UNKNOWN
references, with derivable questions stratified across depths 0–5. Previously used
logic theories/evidence and the new development selection were excluded. References
were kept out of model inputs; the independent grader used exact numeric matching
or exact TRUE/FALSE/UNKNOWN labels.

The token audit passed remotely and reproduced exactly from the local backup.
All 3,600 final generations were reconstructed from recorded Granite tokens;
controller tokens contained framing delimiters only. Accepted prefixes excluded
rejected branches, and every scored candidate was an intermediate step. Recorded
sampling seeds/counts and final-generation policy matched the protocol. All 1,200
paired initial three-candidate batches matched exactly between likelihood and Jev.
Identical retained final prefixes never produced different greedy final tokens.
Source, dataset and exclusion hashes matched; all 400 problem evidence hashes
were distinct, with no excluded-theory/evidence overlap.

## Guidance behavior and performance

Jev changed **484 intermediate selections** from the local likelihood winner on
its own visited prefixes. It retained 1,421 steps overall, versus 4,058 for single
and 4,637 for likelihood. The Jev arm ended reasoning with `all_rejected` in 833
runs and `no_valid_step` in 367; the reserved Granite final generation still ran.

The task breakdown matters: Jev retained **no step in 572/600 logic runs** and
150/600 math runs. It accepted just 48 logic steps and 1,373 math steps. Thus the
logic condition mostly ended with a direct Granite final after rejected/invalid
proposals. These observations identify a bottleneck; they do not establish whether
individual rejected steps were correct or whether rejection caused the math loss.
An independent audit of step correctness/usefulness would be needed to distinguish
weak proposals from over-rejection. No such semantic audit is claimed here.

UNKNOWN remained difficult despite being an explicit answer option: single,
likelihood, and Jev matched 15/198, 19/198, and 18/198 UNKNOWN reference outcomes.
These are descriptive counts across 66 problems and three seeds, without a new
subgroup significance claim.

| Mean controller latency | Single | Likelihood | Jev |
| --- | ---: | ---: | ---: |
| GSM8K | 1.97 s | 2.47 s | 2.87 s |
| ProofWriter | 0.86 s | 1.28 s | 0.62 s |
| Both tasks | 1.42 s | 1.87 s | 1.75 s |

Latency includes generation and remote Jev calls, excluding loading, warm-up and
runner bookkeeping. Jev was slower on math but faster on logic, where it usually
retained no steps. Its lower aggregate latency than likelihood is not a matched-work
speedup or evidence of colocated performance. Actual work differed substantially:

| Whole-study resource | Single | Likelihood | Jev |
| --- | ---: | ---: | ---: |
| Generated tokens, all proposals | 66,762 | 203,798 | 113,122 |
| Padded decode slots | 66,762 | 234,985 | 130,883 |
| Repeated prefill tokens | 3,784,507 | 10,871,148 | 5,164,814 |
| Accepted reasoning steps | 4,058 | 4,637 | 1,421 |
| Runs retaining no reasoning step | 325 | 295 | 722 |
| Jev API calls | 0 | 0 | 2,254 |

The main Jev arm used 2,505,412 input and 183,474 output tokens. Its accumulated
provider-call time was 806.97 seconds. See [resources](resources.json) for per-task
latencies, medians/p95, stop reasons and peak allocated CUDA tensor memory;
[summary](summary.json) includes seed/depth results without new subgroup claims.
Equal configured ceilings do not imply equal computation or production throughput.

## Cost, cleanup and reproducibility

Estimated compute and disk cost was **$3.18**,
and Jev cost was **$0.108**, including both
48-job pilots and the 3,600-job main study: **$3.29**
total against the authorized $50 budget. This is a rate estimate before tax and
any separately billed network charges, not a provider invoice. It conservatively
uses creation-to-confirmed-deletion wall time (2.042 hours).
The shared ledger reconciled all 2,306 calls and 2,563,893 input tokens, with no
unsettled reservations. Its conservative $0.05/million accounting was $0.1282.

All 41 remote result files matched local SHA-256 backups before cleanup. The
instance, managed boot disk, task security rules and security group were deleted,
and their absence was verified. No temporary study resources remain running.
[Cost assumptions](cost.json) use the checked [Nebius rates](https://docs.nebius.com/compute/resources/pricing)
and [Jev pricing](https://docs.typesafe.ai/models).

Public artifacts include [integrity checks](integrity.json), [metadata and hashes](metadata.json),
[case identifiers](case-identifiers.json), [aggregate logic confusion counts](logic-confusion.json),
and the summaries above. Original sources are [GSM8K](https://github.com/openai/grade-school-math)
and the [authors' ProofWriter archive](https://aristo-data-public.s3-us-west-2.amazonaws.com/proofwriter/proofwriter-dataset-V2020.12.3.zip). Raw external examples and
full token traces remain in private backups under the documented dataset-rights
policy; public aggregates alone do not permit a per-example token audit. Public
benchmark exposure during pretraining cannot be excluded. Correct final answers
also do not certify each reasoning step or general reasoning ability.

The full local suite passed **206 tests**, including five optional backend checks;
lint, formatting (105 files), the AI-guidance checker (46 Markdown files), and
package build passed. New regressions were observed failing before implementation
or correction, as documented in the protocol. The final-source CI and review status
are recorded in [PR #2](https://github.com/OVRLab/jev-guided-decoding/pull/2). Automated
Codex review was unavailable because its review quota was exhausted. This work
remains on the review branch; no merge, model release or package publication is
claimed.
