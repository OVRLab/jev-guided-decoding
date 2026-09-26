# R25: Jev-gated internal repair on natural Granite drafts

Registered 2026-09-23 before data selection, inference or training. Follows R24's
useful error detection and R22's failure to use its learned feedback inputs.
This is an architecture pilot, not the full ten-benchmark study or a novelty claim.

## Budget authorization

The owner raised the **cumulative** cap from $50 to $75 on 2026-09-23. Starting
estimated use is $36.773534922020566, leaving $38.226465077979434 before tax/network.
Reserve $14.40 for R25: at most eight hours of one L40S/16vCPU/64GiB and 80GiB
SSD at $1.75458082/hour, plus $0.25 for Jev and rounding/cleanup. Worker deadline
seven hours, independent machine poweroff eight hours, regular local backups and
verified deletion. No H200, extra GPU or automatic extension. Historical $50
protocols are unchanged. A later larger-model comparison requires its own freeze
and reserve within $75; this pilot does not claim to complete the whole program.

## Hypothesis and architecture

A natural draft supplies information about what the model actually misunderstood.
A learned repair branch can exploit Jev's error probability if feedback controls
the branch directly rather than being an optional feature that training can ignore.
Original Granite 4.0-1B and hosted Jev stay frozen. Train only a rank-64 residual
module after decoder block 19 (zero indexed), leaving 20 downstream blocks to
process it. This fixed middle placement controls comparison with R22; optimal
layer placement remains untested. For hidden vector h and p = Jev probability
that the draft's final answer is correct:

    s = RMS(h); g = 1 - p
    h' = h + g * 0.5 * s * tanh(U * tanh(D * h/s))

D/U are new trainable matrices, U initially zero. Explicit g=0 is identity even
after training. This prevents a learned condition projection from discarding the
signal; it does not guarantee useful changes or even changed final tokens.
The intervention starts at the last prompt position predicting the first repair
token and applies to subsequent repair positions, never retroactively to the
draft. Jev is called once after a complete/bounded draft; its score is held fixed
through repair. No per-layer API call, Jev-generated answer, logit mask or forced
UNKNOWN. All final tokens come from Granite's full vocabulary. Cache is new for
every arm, prompt and draft token IDs are preserved exactly, and hooks are scoped.

## Data, separation and targets

Use public GSM8K and ARC-Challenge as two independent development domains, with
source revisions and file hashes frozen before inference. Both are auxiliary
benchmarks, not substitutions for the ten-task north-star suite. GSM8K: 192 train
and 32 development cases from source train, excluding all 24 R23 cases by source
ID and normalized question. ARC: 192 source train and 32 source validation.
Fresh pilot evaluation: 96 GSM8K source test and 96 ARC source test. Select by
SHA256 ordering of `r25/<id>`, independent of answers and model behavior. Reject
normalized exact question duplicates across splits and against earlier exposed
GSM8K content; record exclusions. This does not prove absence of pretraining
contamination or near-duplicate semantic variants. No MuSR story variants reused.

Generate the original 1B's natural draft on every case first, greedy, native chat
template, maximum 1,024 new tokens, no truncation, 8,192 input limit. Include wrong,
correct, unparseable and cutoff drafts; no selection by correct labels. Jev sees
only public problem and actual draft, using R24's fixed final-correctness Noul.
Reference answers/solutions never enter API payloads or evaluation generation.
Training targets are GSM8K's verified source worked solution (calculator markup
removed) or ARC's `Final: <letter>`; ARC offers no reference rationale. These are
new adaptation data, not Granite pretraining data. Training and test targets are
separate files; test references are read only for offline scoring after generation.

The second-turn user instruction asks to check the draft, correct errors, preserve
correct conclusions and give a final answer; it allows full reasoning. Append chat
framing to exact draft IDs, not a retokenized transcript. Repair cap 512 tokens.
Target cap 768; any oversize example is a recorded admission failure before
training, not silently truncated. Context cap applies to training and inference.

## Training and fixed controls

Train live-gated and constant-gated (g=0.5) adapters with identical data, rank,
initialization, order and optimizer schedule for seeds 2501 and 2502. Two epochs,
AdamW lr 0.001, zero weight decay, accumulation eight, gradient clip one, float32
adapter math with BF16 backbone. All base gradients must stay absent and exact
base weight digests must agree before/after. Choose epoch per mode/seed by
mean accuracy on the 64 development cases, earliest epoch on ties. Save every
checkpoint and selection before any test draft, API call or output.

On all 192 test cases run: original native draft; untrained blind repair; untrained
text-feedback repair receiving the same probability; each seed's matched constant
adapter; each seed's live adapter with real, within-task cyclically shuffled, and
inverted feedback. Shuffling has no self donor and uses fixed ID order, not labels.
All adapter arms use exactly the blind repair prompt. Text feedback is explicitly
a harness control. Report identity/feedback sensitivity, wrong-to-correct recovery,
correct-to-wrong damage, malformed outputs and cutoff behavior. The native draft
is shared computational work, count it once per deployed two-pass system, while
all actual experimental work and API requests count in spending.

## Primary analysis and stopping

Prospectively use the R23 complete-option readout plus strict numeric extraction,
identically for every arm; no credit for a correct value only inside reasoning.
Primary effect is seed-mean live accuracy minus native, and versus matched constant
and blind repair on the 192 fresh cases. Report each domain and seed, effect sizes
and paired stratified problem bootstrap 95% intervals (10,000 draws, seed 2500).
Pair seeds within each problem, do not inflate N by treating seeds as new cases.
All planned cases remain denominator; missing/failed is incomplete, not success.
Also show real/shuffled/inverted final-token and correctness differences; a gain
without feedback dependence is adaptation evidence, not useful Jev integration.
No post-test tuning. The threshold for spending on a larger-model replication is
positive live-minus-native and live-minus-constant effects in both domains; an
interval crossing zero remains preliminary. Otherwise diagnose the limitation
and preserve the result without claiming the north star is reached.

## Implementation and verification

New `research/iterations/gated_repair` modules for normalization/freeze, hook,
training/runtime, audit and analysis; behavior tests first. Test g=0 identity,
nonzero causal effects only at allowed positions, monotonic feedback scaling,
invalid values, cleanup on exception, cached/full parity, gradient ownership,
exact token-prefix preservation, reference-free requests, disjoint data, donor
maps, tie selection, finite limits, missing/duplicate output rejection and paired
metrics. Preserve initial red logs. Real-model mechanical admission precedes
training. Pin Granite revision 6a7381ba1f54d684ff508d991aeb7dc580157103,
Jev 1.13.0, Torch 2.8.0, Transformers 4.57.1, Python 3.12.13 and source hashes.
Jev uses the existing validated scorer with one attempt, durable maximum-input
reservation before dispatch and stop on ambiguous errors; no blind paid replay.
The credential is transferred privately to the owned worker only if needed and
never included in artifacts. Archive prompts, exact IDs, raw API receipts, losses,
checkpoints and timing; audit/replay offline, public sanitized records and report.
Run canonical checks, inspect the actual PR base and available CI/reviews, leave
model release and broad superiority claims pending evidence.

### Pre-inference numeric admission detail

The pilot deliberately switches R22's float32 backbone to BF16 to fit a practical
GPU repair study. Zero-initialized and gate-zero output parity must be exact.
For a nonzero adapter's full-prefix versus cached-step fixture, permit at most
0.125 absolute logit difference and require identical argmax; record the measured
difference. This accommodates BF16 matrix-shape kernel differences, not a claim
of bitwise cache equivalence. Offline float32 tiny-model checks use 1e-6/1e-5.
