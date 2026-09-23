# R23 diagnostic results

These are 76 development problems per model with different native-oriented generation profiles; they are not official benchmark scores or a ten-task aggregate. Granite 4.0-1B is greedy with a 2,048-token ceiling; Granite 4.2-3B uses native thinking, sampling and an 8,192-token ceiling.

## Frozen primary readout

| Task | Granite 4.0-1B | Granite 4.2-3B | 3B minus 1B, percentage points (exploratory 95% interval) |
| --- | ---: | ---: | ---: |
| GSM8K training math | 19/24 (79.17%) | 21/24 (87.50%) | +8.33 [-12.50, +33.33] |
| IFBench constraints | 2/12 (16.67%) | 7/12 (58.33%) | +41.67 [+16.67, +66.67] |
| MMLU-Pro validation | 10/28 (35.71%) | 18/28 (64.29%) | +28.57 [+14.29, +46.43] |
| MuSR narratives | 0/12 (0.00%) | 4/12 (33.33%) | +33.33 [+8.33, +58.33] |

IFBench primary is strict prompt success; loose results are shown below. Choice/math extraction failures receive no credit. All planned cases stay in denominators, including unfinished thinking. Primary readout scores alone cannot distinguish format violations from incorrect reasoning. Intervals are small-sample exploratory problem bootstraps; no multiplicity-adjusted superiority claim is made.

## Separate post-hoc choice readout

| Task | Granite 4.0-1B | Granite 4.2-3B |
| --- | ---: | ---: |
| MMLU-Pro validation | 12/28 (42.86%) | 18/28 (64.29%) |
| MuSR narratives | 6/12 (50.00%) | 4/12 (33.33%) |

This additional rule was specified after seeing native output. It accepts one unambiguous, complete option label plus its full text, matched against all question choices without looking at the reference key. It never replaces an already parseable primary decision. The original primary remains above. It is not independent semantic annotation or an official benchmark correction. Math and IFBench are unchanged.

## Readout and stopping outcomes

| Model / task | Primary unparseable | Post-hoc choice unparseable | Length stops | Unfinished thinking | IFBench loose correct |
| --- | ---: | ---: | ---: | ---: | ---: |
| Granite 4.0-1B / GSM8K training math | 3 | — | 0 | 0 | — |
| Granite 4.0-1B / IFBench constraints | 0 | — | 0 | 0 | 2 |
| Granite 4.0-1B / MMLU-Pro validation | 4 | 1 | 0 | 0 | — |
| Granite 4.0-1B / MuSR narratives | 11 | 0 | 0 | 0 | — |
| Granite 4.2-3B / GSM8K training math | 1 | — | 1 | 0 | — |
| Granite 4.2-3B / IFBench constraints | 4 | — | 4 | 4 | 7 |
| Granite 4.2-3B / MMLU-Pro validation | 6 | 6 | 6 | 6 | — |
| Granite 4.2-3B / MuSR narratives | 2 | 2 | 2 | 2 | — |

Unparseable means the selected readout did not yield a decision; an empty unfinished thinking response is included there. A length stop is not automatically an incomplete final answer: the raw record retains both status and stop reason. IFBench `parseable` is only nonempty text.

## Measured generation work

| Model | Exact parameters | Generated tokens | Serial generation seconds | Mean seconds / problem | Maximum allocated GPU GiB | EOS / length stops |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Granite 4.0-1B | 1,631,750,144 | 10,657 | 263.77 | 3.47 | 3.207 | 76 / 0 |
| Granite 4.2-3B | 3,659,737,600 | 202,211 | 5150.25 | 67.77 | 7.551 | 63 / 13 |

Times are CUDA-synchronized serial prefill/decode, with no separate excluded warm-up. They include thinking tokens. They exclude setup/download/model loading; all such time remains in cloud cost. Allocated memory is PyTorch allocation, not total device reservation or serving concurrency capacity. Different profiles, model generations and token counts prevent attributing these differences to parameter count alone.

Every final answer comes from the corresponding generator; there are zero Jev calls in R23. See [method](method.md), [primary analysis](analysis.json), [post-hoc readout](secondary-readout.json), [token audit](audit.json), [cost](cost.json), and [reproduction](reproduction.md).
