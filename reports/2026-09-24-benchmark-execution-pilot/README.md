# R27-A: serial runtime engineering pilot

**Completed on exposed development cases; this is not a fresh benchmark result.**
All 132 outputs and 132 serial jobs finished. Independent
source, exact-token, prefix, numerical/cache, selected-gate, receipt and unchanged-
weight audits pass. Public compressed artifacts reproduce the analysis exactly.
The registered engineering admission passes; it requires valid measurement,
not a favorable model score or minimum formatting success rate.

## Development scores

| System | ARC (4) | GSM8K (3) | MMLU-Pro (5) | MuSR (3) | IFBench strict (3) |
| --- | --- | --- | --- | --- | --- |
| Original Granite 4.0-1B | 2/4 | 2/3 | 1/5 | 1/3 | 2/3 |
| Granite + live Jev repair | 2/4 | 2/3 | 1/5 | 1/3 | 2/3 |
| Granite-only self-refinement | 2/4 | 2/3 | 1/5 | 1/3 | 2/3 |
| Jev-routed blind repair | 2/4 | 2/3 | 1/5 | 1/3 | 2/3 |
| Matched constant adapter | 2/4 | 2/3 | 1/5 | 1/3 | 2/3 |
| Live adapter, constant strength | 2/4 | 2/3 | 1/5 | 1/3 | 2/3 |
| Inverted strength | 2/4 | 2/3 | 0/5 | 1/3 | 2/3 |
| Shuffled strength | 2/4 | 2/3 | 1/5 | 1/3 | 2/3 |
| Granite 4.2-3B thinking | 4/4 | 3/3 | 4/5 | 3/3 | 3/3 |
| Qwen3-4B-Instruct-2507 | 4/4 | 3/3 | 4/5 | 3/3 | 1/3 |

These small, previously exposed sets diagnose execution and readout. They do not
establish a scientific gain, a larger-model victory or ten-benchmark performance.
The primary independent readout is the prospectively integrated choice v2, numeric
parser and pinned IFBench strict/loose evaluator. Individual descriptive paired
intervals and loose IFBench outcomes are in [analysis.json](analysis.json).
Language detection is seeded to 2701 before any R27 output grading. R26-A's old
format failure and all old raw records/grades remain unchanged.

## What changed and what stayed fixed

[Protocol](../../research/benchmark-execution-v2-plan.md),
[immutable pilot manifest](../../research/protocols/benchmark-execution-pilot-v2/manifest.json),
[data/checkpoint notices](../../research/protocols/benchmark-execution-pilot-v2/NOTICE.md).
Serial generation eliminates finished-row padding. The runner can stop on complete
requested answer lines outside thinking; exact generated tokens remain intact.
Prompt wording, per-request seeds and serial scheduling differ from R26, so this
is not a controlled attribution of speed changes to one optimization.

Original Granite stays FP32/greedy with 2,048 output tokens; Granite 4.2-3B stays
BF16/thinking with 8,192 tokens; Qwen3-4B stays BF16/nonthinking with 16,384 tokens.
Native model-card sampling profiles and pinned revisions are retained. Actual
cutoffs, unfinished thinking, real token work, load time and latency are recorded;
unequal ceilings and a single sampling seed limit broader model comparisons.

The R25 selected live/constant adapters remain frozen after zero-indexed block 19.
All six selective arms share Jev routing; they are not Jev-free controls. An
additional original-Granite self-refinement pass ran for every case before any
Jev request and used no adapter. All final semantic choices and tokens are generated
by Granite; Jev supplies only the probability used for routing/strength.

## Execution and cost

There were 18 physical Jev requests,
0 retries and 0 missing
judgments, using 13,172 input tokens
($0.00055322). Every native draft was queried; no Jev-call saving
is claimed. Across the six selective controls, 54 repairs ran
and 54 were skipped. The separate always-self-refine
control executed all 18 extra passes.

All 21 remote files matched local hashes before
resource deletion. The one L40S, managed boot disk and owned network resources
were deleted. Inclusive created-to-cleanup compute/disk estimate plus Jev is
**$1.2225**, bringing the series to **$47.40/$110**,
leaving **$62.60** before tax/separate network. The $5 pilot
reserve was respected. [Cost/cleanup](cost-and-cleanup.json),
[artifact hashes](artifacts.json).

## Verification and next experiment

Before dispatch, 591 local and remote offline tests passed. Subsequent independent
readout/audit/input-preparation checks bring the local suite to **606 passing**;
Ruff, formatting, build and guidance checks pass. New capability tests were first
observed failing before implementation, including the unseeded language grader.
Exact public extraction/reanalysis matches without new model or Jev calls.

The [prospective GPQA protocol](../../research/gpqa-diamond-execution-v1.md) covers
all 198 questions and separately reports 196 untouched ones; its raw question and
answer-bearing artifacts remain private. Full dispatch still requires its final
manifest and cost admission. IFBench, MuSR and AIME inputs have separate prospective
admissions. The other ten-task cells remain visibly incomplete.

The existing PR remains unmerged. No human review is recorded; the automated
reviewer's quota is exhausted, which is unavailable review rather than approval.
This pilot does not publish a model checkpoint or establish architectural novelty.
