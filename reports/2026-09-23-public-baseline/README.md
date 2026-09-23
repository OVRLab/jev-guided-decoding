# R23: native Granite comparison across four public task families

The first public cross-domain baseline stage is complete: **76 problems per model, 152 recorded outputs**, with token/input/model/source audits and exact public artifact reconstruction. This is a small **development diagnostic**, not official full-benchmark scores, a Granite–Jev architecture result or the completed ten-task scorecard.

## Frozen primary results

| Task | Granite 4.0-1B | Granite 4.2-3B |
| --- | ---: | ---: |
| GSM8K training math | 19/24 (79.17%) | 21/24 (87.50%) |
| IFBench constraints | 2/12 (16.67%) | 7/12 (58.33%) |
| MMLU-Pro validation | 10/28 (35.71%) | 18/28 (64.29%) |
| MuSR narratives | 0/12 (0.00%) | 4/12 (33.33%) |

Choice and math readouts require the registered explicit final decision. Some clear full-option answers omit that marker, so the primary score is not pure reasoning accuracy. The original scores remain unchanged. A separately documented **post-hoc** whole-option rule gives:

| Choice task | Granite 4.0-1B | Granite 4.2-3B |
| --- | ---: | ---: |
| MMLU-Pro validation | 12/28 (42.86%) | 18/28 (64.29%) |
| MuSR narratives | 6/12 (50.00%) | 4/12 (33.33%) |

Math and instruction-following scores do not change under this amendment. See [all task outcomes, intervals and work](tables.md) and the [fixed qualitative inspection](failure-analysis.md). No LLM judge or answer-key-informed extraction is used. Related MuSR story variants mean the exploratory intervals are not story-cluster adjusted.

## Profiles and limitations

Original 1B runs greedy with 2,048 new tokens; newer 3B uses its native thinking template, temperature 1.0/top-p 0.95/top-k disabled and 8,192 new tokens, seed 2301. Both are BF16/SDPA on the same single L40S. Ceilings include thinking and final answers. Versions, training and compute differ as well as parameter counts; this is not a causal size comparison, a matched-compute test or a best-quality configuration search.

- **Granite 4.0-1B:** 1,631,750,144 parameters; 10,657 generated tokens; 263.77 seconds serial generation; 0 length stops; 0 unfinished thinking outputs.

- **Granite 4.2-3B:** 3,659,737,600 parameters; 202,211 generated tokens; 5150.25 seconds serial generation; 13 length stops; 12 unfinished thinking outputs.

Every planned output is retained, including cutoffs. Generation timing excludes setup/download/loading; those remain in cloud cost. The [method](method.md) records exact revisions, source `36d55ce`, pre-inference IFBench admission amendment and post-hoc readout limits. A larger model hitting this ceiling is not evidence of its maximum attainable quality.

Selected MuSR/IFBench source-test items are now project development; future untouched evaluation must exclude them, duplicates and related scenario variants. GSM8K training is an auxiliary development task, not the AIME scorecard cell. The [ten-task contract](../../research/benchmark-suite-contract-v1.md) records the remaining evaluator admissions, and the [final-scorecard status](ten-task-status.json) correctly remains empty.

## What the Jev companion experiment adds

R23 contains **zero Jev interventions**. Separately, [R24](../2026-09-23-public-critic/README.md) tests the unchanged native answers: Jev flags **21/23 reference-wrong answers**, with **3/37 false flags on reference-correct answers**. This supports testing selective repair, without demonstrating any generated-answer improvement. All sixty eligible answers received a call, so no selective-dispatch savings were measured.

The next architecture candidate must learn to use feedback to repair actual Granite errors while preserving correct decisions, and demonstrate that the feedback matters against matched training and extra-reasoning controls. Its insertion layer and broad transfer remain unestablished. R22's feedback-insensitive trained bridge remains a negative result.

## Verification and resources

All 507 local tests, Ruff lint/format, the 49-file guidance check and builds pass. The GPU host passed its 492-test snapshot and the eight amended focused tests before inference; later local tests are not attributed to that older snapshot. The initial capability/readout/scorecard failures and evaluator admission evidence are retained in [validation](validation/).

The single GPU, managed disk and owned network resources are **verified deleted** after byte-verified retrieval. R23 cloud estimate **$3.0100**, R24 API **$0.002120**, combined new **$3.0121**, cumulative **$36.7735/$50**, before tax/separate network. The estimate conservatively charges the whole creation-to-verified-deletion interval; it is not an invoice.

See [primary analysis](analysis.json), [secondary readout](secondary-readout.json), [exact token audit](audit.json), [artifact hashes](artifact-hashes.json), [offline reproduction](reproduction.md), [cost](cost.json), [cleanup](cleanup.json), and [dataset attribution/terms](../../research/protocols/public-baseline-v1/NOTICE.md). No model release or paper publication is implied.
