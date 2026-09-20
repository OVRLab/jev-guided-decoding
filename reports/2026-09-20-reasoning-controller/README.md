# Bounded reasoning controller — 2026-09-20

The implemented engine exercised framing, exact-token deduplication, bounded
resampling, and saved-branch recovery with real Granite and Jev. **Step-guided Jev
completed none of the four tasks.** Granite proposed repetitions of supplied
premises; Jev rejected them for lack of progress, and resampling did not provide
an acceptable first deduction. This is a negative end-to-end result, not evidence
of better reasoning. The actual Jev model evaluated candidates during inference;
neither model was trained or replaced by a surrogate critic.

## Protocol and outcomes

Four newly authored fictional tasks cover a two-hop implication, a missing
conjunct, a reversed implication, and a rule chain with a distractor. Each ran once
with seed 42 in four modes. The prompt, fixtures, thresholds, and budgets were
committed before execution and were not tuned or rerun to repair the outcomes.
These exposed fixtures are a mechanism check, not an independently graded held-out
benchmark. Final text and intermediate traces were reviewed by the implementation
author, separately from Jev's own judgments.

| Mode | Completed frames | Other stops | Mean elapsed | HTTP attempts | Backtracks |
| --- | ---: | --- | ---: | ---: | ---: |
| Greedy explicit steps | 2/4 | 2 premature EOS | 5.90 s | 0 | 0 |
| Likelihood search | 3/4 | 1 expansion budget | 23.48 s | 0 | 2 |
| Final-only Jev | 3/4 | 1 expansion budget | 25.94 s | 4 | 3 |
| Step-guided Jev | 0/4 | 4 no eligible branch | 5.19 s | 6 | 0 |

A completed frame is a protocol outcome, **not a correctness label**. For example,
the greedy missing-conjunct answer claimed access was established by a badge while
also admitting that the required escort was unspecified. It completed the frame
but did not correctly answer the question. Conversely, some stopped outputs
contained a sensible answer body with no closing final tag. Those remain incomplete.
Lexical exact match/F1 in the raw summary are only smoke metrics; no accuracy or
statistical quality improvement is claimed.

### What the trace establishes

- **Final boundaries:** complete `<final>` frames returned immediately without an
  extra EOS. Granite sometimes generated an opening final tag and a sensible
  answer, then EOS without the closing tag; the engine rejected that malformed
  output rather than silently repairing or accepting it.
- **Deduplication:** 223 candidates across 85 proposal batches contained 93 exact
  token-sequence repeats at the same parent. All generated/padded work was counted;
  exact duplicates were not rescored. Case, punctuation, or trailing-newline variants
  still counted as distinct, so this does not guarantee semantic alternatives.
- **Recovery:** on the two-hop task, final-only Jev assigned completion 0.74 to
  `yes, parcel Tavi is eligible for dispatch`, below the fixed 0.75 threshold.
  Python restored a saved sibling, preserving its exact prefix, and later accepted
  a final with a reason (support 0.96, completion 0.92). This demonstrates recovery
  after a rejected final; it is not proof of improved reasoning quality.
- **Bounded failure:** likelihood and final-only Jev each exhausted eight parent
  expansions on the distractor chain after two backtracks. Many alternatives
  repeated rules or differed only in whitespace. Final-only Jev made zero calls
  on this task because no complete final frame reached its scorer.
- **Step guidance:** all ten unique first-step candidates evaluated across the
  four guided tasks were copied premises, restatements, or an incomplete fragment.
  Progress scores were 0.04–0.07, below 0.60. All four searches exhausted their
  one resampling attempt at the root. No step was accepted and no sibling saved;
  live step-guided recovery was therefore not exercised. Its control flow is
  covered offline, while the live recovery above used the final-only control.

These observations identify two current bottlenecks: producing useful deductions
rather than copied premises, and reliably finishing the explicit frame format.
Rejecting copied premises can be consistent with the rubric and still make the
whole system less useful if the generator supplies no acceptable alternative.
A follow-up should test a small demonstration-based proposal prompt and more
meaningful candidate diversification on declared development cases, measure valid
candidate availability, and then freeze the configuration before held-out testing.
Neither weakening thresholds until an answer passes nor additional unproductive
search would establish a quality gain. This follow-up is not part of these results.

## Work and latency

| Mode | Generated tokens | Padded decode slots | Repeated prefill tokens | Generation total | Jev round-trip total |
| --- | ---: | ---: | ---: | ---: | ---: |
| Greedy | 311 | 311 | 4,154 | 23.59 s | 0 s |
| Likelihood | 1,418 | 1,626 | 23,262 | 93.91 s | 0 s |
| Final-only Jev | 1,559 | 1,785 | 25,584 | 101.25 s | 2.50 s |
| Step-guided Jev | 291 | 300 | 5,556 | 18.64 s | 2.10 s |

Equal configured ceilings did not produce equal actual work. Step guidance stopped
early, so its lower time is not a speed advantage. Extra generation and the second
model are expected to add latency; the question is whether the quality benefit
justifies that work. This run shows no such benefit. Jev round trips include network
and provider work, which were not separated. There was no colocated Jev runtime or
GPU-server/concurrent-serving test.

All ten HTTP attempts succeeded and returned `jev-1.13.0`, using 8,072 input tokens.
Known input usage at the configured historical rate of $0.042 per million is
$0.000339024, excluding local compute; this is an estimate, not billing evidence.
Usage was not marked unknown. All failed/incomplete searches remain in the report.

## Provenance and reproduction

Source: `ea5b699018364b8e60c80e1bb601c091065900c9`, clean when metadata was captured.
The running process had already imported its source before later CLI artifact-write
hardening; that subsequent fix does not change generation, scoring, or these traces.
Original `ibm-granite/granite-4.0-1b` revision
`6a7381ba1f54d684ff508d991aeb7dc580157103`, 1,631,750,144 parameters,
zero trainable parameters, Apple M1 Pro, MPS BF16, macOS 26.3.1, Python 3.12.13,
PyTorch 2.8.0, Transformers 4.57.1, HTTPX 0.28.1. Model loading took 4.10 seconds
and was excluded from per-run timing. A two-token warm-up at batch sizes one and
three used the first public case and seed 42; it was also excluded. Mode order
rotated by case. MPS memory values are current allocation snapshots, not peaks.

The [config](../../configs/granite-4.0-1b-reasoning.toml) caps each request at
3 candidates, 2 retained children per parent, 1 resampling attempt, 6 path frames,
8 expansions, 6 pending siblings, 96 tokens per frame, 384 path tokens, 1,536
padded decode slots, 30,000 prefill tokens, 4,096 context tokens, 12 HTTP attempts,
and 90 seconds. Sampling uses temperature 0.8 and top-p 0.95. Thresholds are
validity 0.75, progress 0.60, completion 0.75. Kernel work cannot be instantly
interrupted, so time is a cooperative limit. No run hit the time limit here.

```bash
uv run --no-sync jev-decode reason-benchmark \
  --config configs/granite-4.0-1b-reasoning.toml \
  --dataset data/reasoning-controller-smoke.jsonl \
  --modes greedy likelihood final_jev jev \
  --seeds 42 \
  --local-files-only \
  --output results/new-reasoning-controller
```

Use a new output path and the documented Jev key setup. The run returned exit code
3 because incomplete searches were recorded. The fixture SHA-256 is
`8db76954504e9f6cc33b6ffc687850f5a4e560ef5a09a535cbf7a52662a5b3c1`.
Reference answers stayed local and were not provided to either model.

Artifacts: [metadata](metadata.json), [all raw runs](runs.jsonl),
[summary](summary.json), [offline integrity audit](integrity.json), and
[reconstructed Jev inputs](reconstructed-inputs.json). Inputs were reconstructed
offline from the recorded requests, prefixes, candidate indices, and unchanged
request builder; they were not independently captured from the network. Raw run,
metadata, and summary files were copied byte-for-byte from the CLI output.

The audit checked all 16 final/partial paths and all 85 proposal prefixes against
the pinned tokenizer and saved node graph, including all five backtracks; counted
all generated/padded/prefill work and duplicate/scored indices; checked work limits;
and reproduced the summary from the raw rows. It verifies trace integrity, not
semantic correctness. Previous investigation and smoke reports remain unchanged.

## Implementation validation

Before the live run, 90 offline tests passed with the optional tiny-model backend
installed, together with Ruff, format, documentation checks, package build, and CLI
help. New capabilities initially failed for absent modules/methods and unavailable
commands before implementation. Later boundary regressions exposed loss of a
validated path when a resample could not afford another call, and an uncaught
malformed custom scorer result; both were fixed and retained in the tests.

Review also reproduced an existing single-run output race: a file created by
another process during inference could be overwritten despite the initial path
check. Exclusive creation now prevents that overwrite, with an offline regression
and a rule in the security guidance. Final validation covers 91 tests. The live
experiment was not rerun for this artifact-write-only fix. Automated Codex review
was unavailable because the account's code-review quota was exhausted; that is not
review approval. CI status is recorded on the pull request.
