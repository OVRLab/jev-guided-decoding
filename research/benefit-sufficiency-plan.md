# R19: expected benefit and evidence sufficiency inside Granite

Prospective protocol, registered before new live inference on 2026-09-22.
This follows the [R18 result](../reports/2026-09-22-boundary-attention/README.md).
The owner authorized implementation and evaluation, within the existing $50 total.

## Questions and mechanism

1. Does distinguishing evidence sufficiency from source relevance improve generated
   answers, particularly when the answer is absent?
2. Does a small predictor of guided-minus-native quality select useful calls better
   than random calling at the same actual request count?

Retain original Granite 4.0 1B revision
`6a7381ba1f54d684ff508d991aeb7dc580157103`, FP32, greedy full vocabulary, 32-token
ceiling, unchanged R18 prompt and weights. Observe native attention at zero-indexed
layer 18; decide before layer 19; retain the same prefill/cache. All final tokens
come from Granite. No forced UNKNOWN, answer menu, answer replacement, hidden-state
API to Jev, model-weight training or new checkpoint is involved.

One Jev 1.13.0 request contains the existing per-source relevance questions plus
one independent Noul asking whether the supplied evidence establishes an answer.
Only question and sources are sent; all labels, references and oracle paths stay
in evaluation code. Reuse exact joint receipts across controls and count all usage.
This joint-payload relevance control is not assumed identical to historical calls.

Dual treatment: sufficiency >=0.65 activates R18 relevance steering (strength 5,
threshold 0.65, its eleven heads in nine layers); sufficiency <=0.35 activates an
additive attention bias toward the existing system clause “If the evidence does
not establish an answer, explain that briefly in your own words.”; middle scores
retain native computation. Instruction bias uses the same heads and query-position
scope, at strength 2 or 5 selected on calibration. Insufficiency never fabricates an
answer token or inserts new prompt text. This is an unproven intervention hypothesis.

The pre-call gate is ridge regression predicting dual-minus-native quality.
Features: R18's evidence mass, source entropy and head disagreement, log(1+source
count), log(1+prompt length), maximum question/source lexical Jaccard. Standardize
using fit data only; use all degree-two products plus intercept. Fit three ridge
penalties (1,10,100), separately for each instruction strength. Choose strength by
calibration dual quality, then predictor/threshold by calibration routed quality
under a 50% call ceiling. Candidate thresholds are zero and 21 prediction quantiles,
clamped to >=0; also include never. Maximize equal-domain mean quality; ties prefer
fewer calls and canonical JSON. Do not refit after calibration or inspect test
grades before freeze. This trains a small controller, not Granite or Jev.

## Data and controls

Fit: 108 authored heavy worlds, 72 fresh Hotpot questions, 80 SQuAD2 questions
(40 answerable/40 impossible). Calibration: 72 new authored heavy worlds, 48
Hotpot, 80 SQuAD (40/40). Test: 144 authored worlds with light/heavy contexts (288),
160 Hotpot, 160 SQuAD (80/80): 608 inputs. Authored relation/depth/missing cells are
balanced. New seeds and aliases exclude previous protocols. Hotpot excludes all
previous project question IDs. SQuAD comes from official train-v2.0, excluding
previously used article titles, with disjoint fit/calibration/test article groups
and at most one question per paragraph. These public data are held out within this
project, not a claim of absence from model pretraining or official hidden-test scores.

Fit and calibration each run native, relevance, dual-2 and dual-5. Test runs native,
relevance, sufficiency-only (instruction bias on low sufficiency, otherwise native),
dual-always, learned benefit gate, random gate, and the frozen R18 gate applied to
the new dual treatment. The learned gate runs first to measure its physical calls;
other arms use seeded randomized order and exact receipt reuse. The random arm uses
the calibrated fraction; the primary random reference uses the actual test fraction.
All controls share prompts and output/grade contracts. There is no direct-Jev
answer-quality comparator.

## Analysis

Keep R18 authored accuracy, Hotpot full-answer F1, and SQuAD adapted natural-answer
F1, with raw EM/F1 also reported. Preserve unparsed/capped/empty outputs and errors
in denominators. Report answerable/missing cohorts, recognized/wrong abstentions,
constant-abstention reference, calls, provider errors, work, latency and cost.
Primary contrasts per domain: dual minus relevance, and learned gate minus expected
random dual/native mixture at its actual call count. Six comparisons use 10,000
cluster bootstraps and individual 99.1667% intervals (nominal 95% family coverage).
Authored contexts cluster by world, Hotpot by question, SQuAD by article. Secondary
95% intervals and subgroups are exploratory. No all-controls success conjunction.
Do not change graders or thresholds after test. Inspect first-by-ID benefits/harms
and abstention errors qualitatively; these are unblinded examples, not semantic
regrading or a second independent quality endpoint. Lexical F1 can reward wrong
answers; report that limitation and require independent semantic validation before
broad claims. Report Jev sufficiency classification separately from Granite answers.

## Implementation, failure paths and verification

New code lives in `research/iterations/benefit_sufficiency/`, with new focused tests,
protocol snapshots and a new report. Preserve every R00–R18 source/raw record.
Write and observe failing capability tests before implementation. Cover reference
leakage, finite probabilities, abstention-span binding, effect/no-effect branches,
once-only dispatch, cancellation ownership, budget/unknown attempts, fitting split
isolation and audit tampering. Reuse validated R18 threading/cache infrastructure.

Admission uses three authored fit fixtures, canned probabilities only: compare new
native/relevance/failed branches with R18 full logits/all-layer caches within 1e-4;
independently replay the instruction bias through the existing attention hook and
check exact IDs, all caches and logits. Stop on mismatch. Model weights must remain
identical before/after; independently reconstruct every prompt/token/grade/gate/map,
receipt binding and actual computation count. Freeze source, data, settings and
selection before test; no silent recovery/replay of an ambiguous paid attempt.

## Operations and publication

Prior estimated spend $27.22974113467281; total ceiling $50. Reserve at most $10
compute/disk and $2 Jev for this study, leaving a safety margin. Check current price
and capacity; use one L40S or a cheaper suitable GPU, never eight H200s. Six-hour
VM expiry and five-hour inference deadline. One CPU thread per pool. Verify private
credential transfer without exposing it. One provider attempt per payload, 90-second
timeout, durable maximum-charge reservation, failed requests fall back to native;
stop after three consecutive/twenty total failures or non-transient auth/contract
errors. Preserve incomplete work and do not retry ambiguous attempts.

Retrieve and hash-verify all raw artifacts, audit locally, then delete owned cloud
resources. Publish safe lossless artifacts, license notices, methods, results and
negative findings; update research register, paper draft and existing PR. Run the
canonical checks and inspect CI/review context. No novelty, quality or serving
performance claim is implied by implementation alone.
