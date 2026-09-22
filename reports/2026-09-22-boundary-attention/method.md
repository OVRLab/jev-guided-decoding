# R18 method: a decision inside one Granite prefill

The [frozen protocol](../../research/boundary-attention-plan.md) tests conditional
hosted Jev source-relevance guidance in unchanged Granite 4.0 1B. Zero-indexed
layer 19 is the first layer touched by the existing eleven-head treatment. R18
places the request decision immediately before that layer, after observing native
attention at layer 18. There is no generated-answer pilot and no repeated prefill.

```text
Original question + complete evidence + shared answer instruction
                              |
                       tokenize once
                              |
                   Granite layers 0 through 17
                              |
                   Granite layer 18 attention
                              |
         observe ONE last-query row of native post-RoPE attention
         -> evidence mass / source entropy / head disagreement
                              |
                   finish native layer 18
                              |
         +---- pre-hook immediately before layer 19 ----+
         |                                              |
         |  development-frozen threshold rule            |
         |             /                    \           |
         |           SKIP                  CALL          |
         |             |                     |           |
         |             |           hosted Jev            |
         |             |      question + source text     |
         |             |        -> relevance scores      |
         |             |          /             \        |
         |             |      failure          success   |
         |             |         |                |      |
         |             +---------+         fixed head    |
         |                   |             biases armed  |
         +-------------------|--------------------|------+
                             |                    |
                Granite layers 19 through 39, same prefill
                selected heads biased only on success
                             |
                    Granite final vocabulary logits
                             |
                     Granite greedy first token
                             |
             cached autoregressive decoding, same branch
             (all 40 layers run for each subsequent token)
                             |
                      EOS or 32-token cap
```

The lower-layer KV cache stays owned by the same request while Jev is awaited.
The final-query observation is computed once during prefill. Later decoding does
not refit the gate, observe new features or request Jev again. Active relevance
biases persist at their selected heads for all generated tokens. A failed receipt
counts as an attempted call and preserves the native branch and its error record.

## What changes relative to R17

| Property | R17 pilot gate | R18 boundary gate |
| --- | --- | --- |
| Decision input | Up to eight native output tokens and token statistics | Native layer-18 final-query source attention |
| Decision time | After a buffered native pilot | Inside the first prefill, before layer 19 |
| Successful call | Discard pilot and create a fresh guided prefill/cache | Continue the existing prefill/cache |
| Skipped/failed call | Retain native pilot/cache | Continue native computation |
| Final semantic token owner | Granite | Granite |
| New model training | None | None |
| Jev input | Original question and sources | Original question and sources |

R17 and R18 gates are fitted separately. An output-confidence threshold cannot be
transplanted to a source-attention feature. Comparing these selected gates combines
their routing quality and their computation; matched never/always controls isolate
the observation/boundary overhead without changing final token paths.

## Features and treatment

Let `a[h,k]` be the last prompt query's native layer-18 attention probability for
query head `h` and key token `k`. The observer recreates that row from the actual
post-RoPE Q/K, model scaling and mask, using FP32 softmax. It handles grouped-query
attention by repeating the appropriate KV head. It does not allocate a full
queries-by-keys attention tensor. For disjoint source-token sets `S[j]`, save
`m[h,j] = sum(k in S[j]) a[h,k]` and `t[h] = sum(j) m[h,j]`.

Normalize within evidence: `p[h,j] = m[h,j] / t[h]`; use a uniform source
distribution if a head has zero evidence mass. Let `pbar[j]` be the mean of
`p[h,j]` over heads and `H` Shannon entropy with natural logarithms. Features are:

- Evidence mass: mean over heads of `t[h]`.
- Source entropy: `H(pbar) / log(number of sources)`.
- Head disagreement: `(H(pbar) - mean_h H(p[h])) / log(number of sources)`.

For one source the entropy denominator is one and both entropy features are zero.
Tiny negative disagreement from rounding is clamped to zero. Reconstruct saved
features within 1e-12; decisions use the original recorded values. High entropy
or disagreement is a candidate proxy for usefulness, not a verified account of
Granite's uncertainty or a readable chain of thought.

The unchanged treatment adds **5** to source-key attention logits for sources with
Jev relevance **>0.65**, at these `(layer, query head)` coordinates:

```text
(19,6) (19,11) (19,15) (20,11) (21,14) (23,8)
(29,10) (30,4) (34,4) (37,14) (38,11)
```

Softmax then renormalizes attention across all available keys. An additive bias
can change total evidence attention; it does not conserve that mass. Uniform
threshold decisions across all sources use the earlier exact-no-op convention.
The scores are fixed from the original prompt, and do not relabel future generated
tokens as source evidence. No head, threshold or strength is retuned in R18.

## Fitting and test isolation

The 260 development inputs supply two actual outputs each: native and always
guided with the new boundary. For each of three features, consider both threshold
directions at 21 empirical quantiles, plus never-calling. Maximize mean of the
three domain quality means subject to an unweighted development call fraction
at most 50%; tie-break by fewer calls then canonical JSON. Apply the same fitting
procedure separately to R17's three pilot features. This is supervised threshold
selection on public development labels, not neural weight training.

Freeze selection before any of the 984 test inputs. Each test input runs nine
arms: native, always, boundary-never, boundary-always, boundary gate, boundary
random, pilot gate, lexical relevance and shuffled relevance. The boundary gate
runs first, ensuring its physical dispatch cannot hit a control's cached receipt.
The eight other arms run in seeded random order and reuse the exact receipt.

Authored worlds, Hotpot questions and SQuAD article pools are held apart from
development; authored worlds and Hotpot inputs also exclude previous project
exposure. SQuAD is a project subset of the public development set, not a hidden
benchmark. Prompt eligibility uses only source count and token length. Complete
original text is retained. Pretraining exposure is unknown.

## Quality and uncertainty

Authored quality is the earlier conservative parser's accuracy. Hotpot quality
is normalized whole-answer token F1; strict exact match is also retained. SQuAD
quality is maximum whole-answer F1 over references after a fixed conservative
recognizer maps an explicit uncertainty phrase to empty prediction. Empty/EOS
alone scores zero on the adapted contract. Raw SQuAD EM/F1 are reported separately.
No arm forces UNKNOWN or restricts Granite's final vocabulary. Parser failures
are contract failures, not proof that every unparsed answer is semantically wrong.

For each domain the primary contrast is the boundary gate's routing value:

```text
native mean + mean(call * (guided quality - native quality))
    minus
native mean + mean(call) * mean(guided quality - native quality)
```

This compares with expected random guidance at the same actual test call count.
It matches requests, not tokens or dollars. Three primary comparisons use 10,000
paired cluster bootstrap draws and individual 98.333% intervals (nominal 95%
family coverage). Resample authored worlds, Hotpot questions and SQuAD articles;
all contexts/questions in a sampled cluster stay together. Other contrasts use
exploratory 95% intervals. The 3-point gate-versus-always noninferiority margin is
descriptive and separate from requests saved. There is no all-controls conjunction.

## Timing, ownership and checks

Actual per-layer forward and token counts expose any recomputation. Record
prefills, discarded pilot tokens, feature time, peak allocated GPU memory, and
mean/median/p95 model and first-token times. Model time excludes measured provider
wait. Adding a saved receipt duration to a cache-hit execution estimates uncached
wall/first-token time; it is not a separately observed live deployment latency.
Tokenization/loading are outside per-question timings and inside whole-run cost.

The implementation uses serial Python hooks around native Transformers SDPA.
The model worker runs in an owned thread; a boundary callback awaits the provider
coroutine on the event loop. Repeated cancellation drains that worker before
shared hook state is released. Nested legacy/new scopes are rejected. Cache
pointer/shape checks verify identity during a wait; numerical admission separately
compares full vocabulary logits and all-layer KV values. This is not an adversarial
memory-integrity proof, concurrent service, vLLM extension or colocated benchmark.

The real-checkpoint admission has 27 checks across nine fixtures: native parity,
always-guided parity and forced-failed-receipt fallback. It uses canned scores and
no paid calls. The frozen tolerance is 1e-4, with identical accepted tokens, cache
lengths and single-prefill work required. Scientific source and model weight hashes
are verified independently of claims about quality. The resulting audits are
development-team code checks, not independent human replication or peer review.
