# Controlled Granite + Jev study — 2026-09-20

**This configuration did not demonstrate an accuracy gain from intermediate Jev
guidance.** Guided Granite plus the final Jev Choice scored **507/600 (84.5%)**;
direct Jev scored **508/600 (84.7%)**. All three adjusted comparison intervals
include zero. In **542/600 guided runs (90.3%)**, no intermediate step survived:
the final decision payload was identical to the paired direct-Jev payload.
This is evidence about this frozen text-search implementation, not proof that
intermediate guidance can never help.

All **2,400 main jobs and 96 separate stress jobs** were recorded, with no
provider/backend failures, cancellation, missing jobs, or unknown usage. The
temporary GPU, disk, security group, and rules were deleted after all 27 result
files were backed up and hash-verified. No weights were trained or published.

## Main comparison

ProofWriter OWA D5 test split: 200 distinct theories, one question per theory,
three seeds (42, 43, 44), four executed arms. There are **200 independent
problems**, not 600. Label balance is 67 ENTAILED, 67 CONTRADICTED, 66 UNKNOWN.
Reference labels and provable depths were independently checked with symbolic
forward chaining. All uncertain and unfinished outcomes count incorrect.

| Executed arm | Correct / planned | Accuracy | Decision coverage | Mean time |
| --- | ---: | ---: | ---: | ---: |
| Intermediate guidance + fixed Choice (`fixed_jev`) | 507/600 | 84.50% | 523/600 | 2.49 s |
| Unguided Granite + fixed Choice (`unguided_fixed_jev`) | 497/600 | 82.83% | 514/600 | 6.04 s |
| Final-only filtering + fixed Choice (`final_only_fixed_jev`) | 490/600 | 81.67% | 505/600 | 10.56 s |
| Direct Jev, no Granite (`direct_jev`) | 508/600 | 84.67% | 521/600 | 0.29 s |

All four arms use the same fixed final Choices, original evidence, and unique-winner
probability threshold of 0.75. Non-decisions are `uncertain_verdict`, distinct from
semantic UNKNOWN. Final Choices receive accepted steps but never the generated
final label. Coverage is completion of the Choice, not completion of a derivation.

| Paired accuracy difference | Percentage points | Adjusted interval | Problem wins / losses / ties |
| --- | ---: | ---: | ---: |
| Guided minus unguided + Choice | +1.67 | [−3.00, +6.33] | 22 / 15 / 163 |
| Guided minus final-only + Choice | +2.83 | [−1.67, +7.50] | 26 / 17 / 157 |
| Guided minus direct Jev | −0.17 | [−2.00, +1.67] | 6 / 6 / 188 |

Intervals use 5,000 paired problem-cluster bootstrap draws over seed-averaged
correctness, with 98.333% intervals per comparison (Bonferroni nominal 95%
familywise level). These are approximate finite-sample intervals. The predefined
success rule requires all three lower bounds above zero; it was not met. This
does not establish equivalence. Full confusion matrices, conditional accuracy,
per-depth and per-seed results are in [main-summary.json](main-summary.json).

## What happened inside the search

Guided search stopped with `no_eligible_branch` in 581/600 runs and reached a
generated final in 19/600. Only 58 runs retained any intermediate step; there were
96 accepted steps in total. The independent partial checker recognized 72 new
supported atomic claims and could not parse 24 steps. It found no recognized
unsupported guided claim, but **does not certify the unparsed text, explanations,
or cited derivations**. Its full-closure check does not prove a valid local chain.

Unguided and final-only searches retained 2,922 and 3,197 steps respectively;
their partial audits found 814 and 886 unsupported leading claims. Guided search
therefore filtered aggressively, but usually left the final classifier without
additional reasoning. The 542 empty guided payloads were checked for exact equality
with their paired direct payloads. Small outcome differences can still occur
between separate hosted calls. This explains why the study mainly measures a
fallback to direct classification, rather than a frequently successful guided chain.

UNKNOWN recall was 78.28% guided, 79.80% unguided, 80.30% final-only, and 80.81%
direct. Corresponding precision was 92.26%, 93.49%, 93.53%, and 93.02%. Correct
depth-five answers were 42/72, 45/72, 42/72, and 41/72. These subgroup counts do
not establish an advantage or a monotonic relationship with proof depth.

## Generated-answer control limitation

Post-run inspection found **conflicting output instructions**: the shared
[examples prompt](../../src/jev_guided_decoding/framing.py) asks for a verdict
and its reason inside the final frame, while the
[ProofWriter request](../../experiments/proofwriter_data.py) asks for only the
exact label. Generated finals include explanations and sometimes misspell the
label. All three derived generated-answer controls score 0/600 on the frozen
strict contract. **That is not a clean measurement of Granite's reasoning ability.**

The already specified secondary diagnostic accepts a correct first label while
retaining incomplete attempts in the denominator:

| Derived generated-answer control | Completed finals | Strict correct | Correct first label |
| --- | ---: | ---: | ---: |
| Granite alone, preserved unguided path | 449/600 | 0/600 | 155/600 (25.83%) |
| Intermediate-guided generated final | 19/600 | 0/600 | 10/600 (1.67%) |
| Final-filtered generated final | 65/600 | 0/600 | 33/600 (5.50%) |

These reuse existing search paths; they are neither independent runs nor a normal
unconstrained direct-Granite baseline. The conflicting instructions affect all
generation arms, including their search dynamics; the four code-rendered Choice
scores still describe the observed configuration, but should not be generalized
to a corrected prompt or other reasoning architectures. No prompts, grading rules,
raw results, or held-out runs were changed after seeing these results. A follow-up
would first reconcile the contract on development data and then use fresh evaluation
problems under a new frozen protocol.

## Separate synthetic stress test

Twenty-four new fictional worlds cover depths 2, 4, 6, and 7, chain/cycle and
conjunction motifs, all three labels, distracting facts, and missing premises.
Each arm ran once at seed 42. These are new instances of known logical patterns,
not a guarantee against training contamination, and are not pooled with ProofWriter.

| Arm | Correct / 24 | Accuracy | Decision coverage | Mean time |
| --- | ---: | ---: | ---: | ---: |
| Intermediate guidance + Choice | 21 | 87.50% | 22/24 | 4.44 s |
| Unguided Granite + Choice | 20 | 83.33% | 20/24 | 6.35 s |
| Final-only filtering + Choice | 18 | 75.00% | 19/24 | 12.54 s |
| Direct Jev | 22 | 91.67% | 24/24 | 0.29 s |

Guided and direct each classified all 16 provable worlds correctly; they classified
5/8 and 6/8 UNKNOWN worlds correctly. Guided search retained no step in 13/24 runs.
Its 20 accepted steps had supported leading claims under the same partial audit.
The generated-answer prompt limitation remains: strict scores are all zero;
first-label matches are 9/24 unguided, 4/24 guided, and 7/24 final-filtered.
See [stress-summary.json](stress-summary.json) for all diagnostics and intervals.
This small separate test cannot satisfy the main study's success rule.

## Actual resource use

The main arms shared generation ceilings, but consumed very different work:

| Main arm | Generated tokens | Padded decode slots | Prefill tokens | Jev calls | Jev input / output tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| Guided | 85,169 | 102,033 | 3,626,556 | 1,898 | 2,180,420 / 156,099 |
| Unguided + Choice | 309,956 | 356,526 | 13,294,827 | 600 | 490,700 / 27,357 |
| Final-only + Choice | 498,621 | 581,658 | 21,195,801 | 2,780 | 3,277,913 / 189,375 |
| Direct | 0 | 0 | 0 | 600 | 432,249 / 27,357 |

Guided generation/Jev time totals were 945.79/546.43 seconds; unguided
3,328.15/293.50; final-only 5,420.35/911.47; direct 0/172.98. Guided latency was
about 8.6 times direct latency. Its lower latency than the other Granite arms
reflects early search termination and less generation, not equivalent compute.
Stress added 260 Jev calls and 320,341 input tokens. Both JSON summaries retain
all actual counters, including rejected work, resamples, and backtracks.

Granite ran sequentially on one Nebius L40S with 8 vCPUs and 32 GiB RAM; Jev
remained a hosted API. This is not a colocated Jev measurement. Model loading and
two-token batch-one/batch-three warm-ups are excluded from per-job timing.
The longest main job was 22.54 seconds, below the unchanged 90-second limit.

The server was created at 14:57:12 UTC; main analysis finished at 18:20:48 and
stress analysis at 18:30:21. Backup verification and resource deletion completed
at 18:32:44. At the checked
[Nebius prices](https://docs.nebius.com/compute/resources/pricing), compute was
$1.5484/hour plus approximately $0.00778/hour for the 80 GiB disk. Applying these
rates to the whole creation-to-cleanup window estimates **about $5.60 before tax
and Jev fees**. This is a conservative lifecycle estimate, not an invoice; compute
stopped before cleanup completed. No study resources remain running or allocated.

## Provenance and validation

- Inference source: `62f6bedd992afb522421b4fbf73a5fcfd02f8011`, clean at freeze.
- Original `ibm-granite/granite-4.0-1b` revision
  `6a7381ba1f54d684ff508d991aeb7dc580157103`; 1,631,750,144 parameters,
  zero trainable; CUDA BF16. Jev pinned and returned `jev-1.13.0`.
- NVIDIA L40S, 46,068 MiB reported, driver 580.173.02; Python 3.12.13,
  Torch 2.8.0+cu128, Transformers 4.57.1. Accepted prefixes are recomputed
  between chunks; no serving-cache optimization or vLLM integration.
- Both manifests froze before test inference at 15:06:06 UTC. The
  [metadata](metadata.json) retains original source/prompt/data hashes, settings,
  strata, budgets, and runtime records. Public case identifiers and world digests
  are in [main](main-case-identifiers.json) and [stress](stress-case-identifiers.json).
- Offline suite: 174 tests passed locally and on the GPU server before inference;
  this is historical validation of the unchanged functional source. Separate
  [MPS](../2026-09-20-proofwriter-pilot/README.md) and
  [CUDA](../2026-09-20-cuda-pilot/README.md) development pilots are not pooled.
- Post-run offline audit exactly reproduced both saved analyses, verified all
  2,496 job paths and final decision payloads, 13,689 proposal prefixes, source
  hashes, accounting totals, and per-job budgets. Journals contained one start
  and one finish per planned job, with no replay. See [integrity.json](integrity.json).
- The main archive SHA-256 is
  `bbc5694901e8306d0bd659aa1ad53ccfd02c201864f4b320ffa3777827d1fc26`.
  The authors' archive contains no explicit dataset license file. Raw external
  examples and full traces remain in private local backups; this report publishes
  aggregates and provenance. The package's MIT license does not relicense them.

Reproduction commands, source attribution, selection details, ceilings, and the
predeclared analysis are in the [protocol](../../docs/proofwriter-experiment.md).
Reproducing these historical results requires checking out the inference source
above; later documentation commits do not change its code or prompt hashes.
