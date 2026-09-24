# R27-C: complete IFBench and AIME 2026 comparison

Registered on 2026-09-24 before fresh inference. Run all **300 IFBench prompts**
and **30 AIME 2026 problems**, using the frozen R27 serial engine, model profiles,
selected adapters, Jev version, routing threshold and controls. This stage is
independent of GPQA scores and does not modify its frozen worker or protocol.

## Inputs and scoring

The [input and exposure admission](full-short-tasks-admission-v1.md) supplies exact
source revisions, hashes and transformations. IFBench preserves original prompt
strings without an answer-format suffix. Report strict prompt-level pass as
primary and loose pass separately, for all 300 and the 288 untouched prompts.
Use the pinned upstream evaluator and recorded dependency environment; seed
language detection to 2701 and apply the tested null-padding handling. All 300
empty/nonempty fixture paths passed without errors or implicit random parameters.

AIME uses all 30 problems from `math-ai/aime26` revision
`79037aebdb6580008fb960d17cb21fd3099083e3`, without prior project inference or
manual inspection of their problem/answer text. Source hashes and schema checks
are recorded separately. These are the 15 AIME I and 15 AIME II problems, from
the Mathematical Association of America; credit the original competition and
the Math-AI dataset curators. The dataset card labels its packaging Apache-2.0;
do not imply that our package license relicenses the underlying contest problems.
Keep question/answer-bearing artifacts private and publish hashes and aggregates.

The pinned [Inspect loader](https://github.com/UKGovernmentBEIS/inspect_evals/blob/e3402e36c6c1c161797a8b8e7ebbffca05e47fea/src/inspect_evals/aime2026/aime2026.py)
uses the same dataset revision and problem/answer fields. Its
[shared scorer](https://github.com/UKGovernmentBEIS/inspect_evals/blob/e3402e36c6c1c161797a8b8e7ebbffca05e47fea/src/inspect_evals/utils/aime_common.py)
uses the last substantive line, strips boxed notation and performs numeric
matching. R27 retains its prospectively registered `#### NUMBER` prompt and
numeric extractor instead: explicit hash/boxed/final answers and a bare number
are accepted, with the latest explicit match taking precedence. This is
**OVRLab zero-shot numeric pass@1**, not exact Inspect prompt/extractor parity
or an official model-card reproduction. Nine synthetic admission cases verify
empty/refusal failure, leading zeros, boxed answers with closing display-math
delimiters, competing explicit answers and reference-independent extraction.

One native sample per problem/profile is evaluated; no voting, gold-controlled
retry or sample selection. Leading zeros do not change numeric value. Incomplete
thinking and unparseable answers are incorrect. Report the 30-problem denominator
and descriptive problem-paired 95% intervals; this small set cannot establish
broad mathematical superiority. Use the v3 auditor, which delegates numeric and
single-line choices to the unchanged v2 contract.

## Comparisons and inference ownership

Use original Granite 4.0-1B, live Jev-conditioned repair after block 19, all six
registered routed arms, Jev-free always-self-refinement, Granite 4.2-3B thinking
and Qwen3-4B-Instruct-2507. Native profiles stay unchanged, including their distinct
precision, sampling and output ceilings. All final answers are generator-owned.
Every original draft is sent to Jev; this stage tests skipped repair work, not
conditional Jev-call savings. Keep references and evaluator-only constraints off
the worker and out of Jev requests. Do not inspect fresh grades until generation
is complete, and do not tune this stage from GPQA or its own grades.

The combined 330-case stage saves repeated setup/model loading; each task retains
its own denominator, exposure split and score. Cross-task averages are not a
ten-benchmark score. All planned cases must complete for every comparator before
claiming a complete task comparison. An interrupted stage preserves all attempts,
marks remaining coverage missing and does not silently shrink denominators.

## Budget and operations

Reserve **$24** for this stage, independently of GPQA's $24 reserve. Actual prior
spend is $47.39595151031136; actual spend plus both open reserves is
**$95.39595151031136**, below the $110 cumulative cap with $14.60 unallocated.
Do not treat an open reserve as already charged, or spend it again elsewhere.

The exposed three-prompt IFBench profile extrapolates to $8.59 of generation;
the three-problem GSM8K proxy extrapolates to $0.61 for 30 problems, but is a weak
proxy for AIME. These exclude setup/API/evaluation and are neither quotes nor
confidence bounds. Bound execution with an 11-hour worker deadline, 12-hour
independent VM shutdown and $0.25 Jev cap on one L40S with an 80-GiB disk, at the
verified $1.75458/hour before tax/separate network. No automatic extension.

Use periodic private backups, verify every final remote-file hash, then delete
owned compute, disk and network resources. Record all setup/failure time and
provider attempts. References remain local; credentials use private files.
Freeze code, data, evaluator, environment and checkpoint hashes before launch.

The seven remaining task rows, including MuSR, retain separate cost and evaluator
admission requirements. A complete three-task tranche would be progress toward
the north star, not completion of the ten-task objective or proof of novelty.
