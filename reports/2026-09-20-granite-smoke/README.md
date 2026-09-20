# Initial Granite/Jev smoke results — 2026-09-20

The prototype successfully steers generation between sentences, but this small
experiment does **not** establish a quality improvement. Jev guidance was slower,
had slightly lower lexical token F1 than all three controls, and falsely rejected
the ending of one correct answer. These findings do not establish general model
accuracy or statistical significance.

## Setup

- Original `ibm-granite/granite-4.0-1b` at revision
  `6a7381ba1f54d684ff508d991aeb7dc580157103`, 1,631,750,144 parameters, zero trainable.
- Apple M1 Pro, MPS BF16; PyTorch 2.8.0, Transformers 4.57.1, Python 3.12.13.
- Source commit `66d8328306d7badf887e74d86c6b703da0706ea3`, clean working tree.
- Jev requested and returned `jev-1.13.0`.
- Twelve short fictional document questions, one seed (42), three candidates for
  `likelihood` and `jev`, temperature 0.8, top-p 0.95, 48-token chunks.
- Support/relevance/completion thresholds: 0.75 / 0.60 / 0.75; at most one candidate
  resampling retry per step. No threshold tuning was performed on this run.
- The same source evidence and question go to every mode; reference answers remain
  local to scoring and never reach either model.
- Both candidate batch sizes are warmed up; mode order is rotated across cases.
  Timing excludes loading/warm-up and includes generation, scoring, and network waits.

## Twelve-case comparison

| Mode | Exact match | Token F1 | Mean elapsed | Generated tokens | Decode slots | Jev calls | EOS finishes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| greedy | 33.3% | 0.8181 | 1.10 s | 181 | 181 | 0 | 12/12 |
| sample | 33.3% | 0.8267 | 1.19 s | 198 | 198 | 0 | 12/12 |
| likelihood | 33.3% | 0.8218 | 2.70 s | 573 | 621 | 0 | 12/12 |
| jev | 33.3% | 0.8154 | 3.71 s | 632 | 684 | 28 | 11/12 |

Token F1 and exact match are lexical comparisons against reference strings, not
independent correctness judgments. Token F1 ignores word order and can reward
misleading answers; exact match can penalize valid paraphrases. All twelve runs
per mode are included, including the guided run marked `all_rejected`.
The other guided runs finished with EOS, and no API error occurred.

The controls share configured ceilings, but actual compute is not equal: guided
runs used 684 decode slots versus 621 for likelihood selection, and 9,807 repeated
prefill tokens versus 9,135. Extra retries and different continuations explain
some of the timing difference. This is a serial CPU/GPU-plus-network prototype,
not a serving throughput benchmark; no GPU-server speed claim follows from it.

The reported guided smoke run used 33,764 Jev input tokens, costing an estimated
$0.001418 at the configured $0.042 per million input tokens. The separate
continuation demo used 3,641 input tokens, estimated at $0.000153. These estimates
exclude local compute and earlier development probes; they are not billing records.

## Observed failure cases

**False rejection of a correct ending (`optional-step`).** Granite answered:

> No, a profile photo is not required to save the form.

Jev scored the sentence's support at 0.98 and relevance at 0.95. For the subsequent
empty EOS, it scored completion between 0.64 and 0.69 across the two attempts,
below the configured 0.75 threshold. The controller correctly enforced its policy
and returned `all_rejected`, retaining the accepted sentence. This is a verifier /
threshold failure, not a transport failure. A lower threshold might accept this
answer, but would need evaluation on a separate validation set.

**Unsupported causal wording accepted (`missing-cause`).** The evidence explicitly
gave no reason for a postponement. Jev first rejected candidates asserting that a
future schedule announcement caused it, but after resampling accepted:

> The test run was postponed because there is no provided reason for the postponement in the given notice.

That phrasing incorrectly turns absence of information into a cause. Jev assigned
support 0.85 and relevance 0.64, both above the configured thresholds. Greedy
Granite also produced unsupported causal wording on this case. The experiment
therefore shows an intervention that still failed to reliably correct the answer.
These observations are the implementation author's reading of the published
traces, not blinded human grading.

## Evidence of guidance during generation

The separate `two-sentence-continuation` fixture explicitly requests two sentences.
Its guided trace contains three decisions:

1. Select `The Lumen release checklist is owned by Mira.` from the first batch.
2. Generate and select ` Tomas is the backup reviewer.` using the first sentence's
   accepted **token IDs** as the continuation prefix.
3. Evaluate and accept EOS against the completed answer.

Both guided decoding and the likelihood control produced the same correct text.
The guided run took 4.54 seconds and three API calls versus 3.60 seconds for the
control. Both used 54 generated token slots and 1,218 prefill tokens. This confirms
the integration mechanism, not a quality advantage. It remains a Transformers
controller, not a vLLM scheduler extension or a change to model weights.

## Reproduce and inspect

Run from the repository root at the source revision above:

```bash
uv sync --locked --extra transformers --extra dev
uv run --no-sync jev-decode benchmark \
  --config configs/granite-4.0-1b.toml \
  --dataset data/grounded-smoke.jsonl \
  --modes greedy sample likelihood jev --seeds 42 \
  --output results/reproduction-smoke
uv run --no-sync jev-decode benchmark \
  --config configs/granite-4.0-1b.toml \
  --dataset data/continuation-demo.jsonl \
  --modes likelihood jev --seeds 42 \
  --output results/reproduction-continuation
```

Provide a Jev key as described in the repository README. API outputs and timings
can vary across reruns, even with pinned model IDs and generation seeds.

- [Smoke metadata](smoke/metadata.json), [summary](smoke/summary.json),
  [all candidates, answers, judgments and timings](smoke/runs.jsonl).
- [Continuation metadata](continuation/metadata.json),
  [summary](continuation/summary.json), [step trace](continuation/runs.jsonl).

All published inputs are fictional repository fixtures. Per-run memory data is in
the traces; MPS current/driver allocations are not peak measurements.

The next experiment should use a separate, harder dataset and independent grading,
then compare actual generation budgets across several seeds. These results do not
yet justify optimizing a vLLM integration for a demonstrated quality gain.
