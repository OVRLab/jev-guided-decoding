# R17 plan: selective, phase-dependent evidence attention

Owner request (2026-09-22): explore conditional Jev use and creative internal
Granite/Jev architectures, implement and test them, retaining the entire research
record. The practical objective of this iteration is a measured quality/cost
advance on unrestricted answers. A new globally useful LLM architecture is the
longer-term ambition, not a claim made by this experiment.

## Hypotheses and implementation

R16's strong additive bias helped constrained choices but sometimes made free
answers copy citations/intermediate facts. Separate three possible causes:

1. **Timing:** guide evidence assimilation in prefill, or fade guidance over the
   first eight answer tokens, instead of steering every generated position.
2. **Attention allocation:** redistribute attention *within* evidence while
   preserving its total attention mass, instead of increasing that mass. For
   each selected head/query and evidence keys S, subtract
   `logsumexp(logits[S] + bias[S]) - logsumexp(logits[S])` from all evidence keys
   after adding the relevance bias. Other keys retain their original logits.
3. **Conditional assistance:** generate at most eight native pilot tokens, then
   decide whether Jev is useful. If assistance is skipped, continue the exact
   pilot cache/tokens; if used, discard the pilot and regenerate from the original
   prompt in a fresh guided cache. Jev never supplies an answer or sees a reference.

Compare a conventional uncertainty gate with a small development-fitted benefit
gate: uncertainty does not necessarily predict that an intervention will help.
The latter fits a decision rule, not Granite or Jev weights. Account for discarded
tokens and repeated prefill. Both gates decide before receiving Jev scores.

All semantic output remains Granite's full-vocabulary greedy output. No forced
UNKNOWN, colour menu, final-answer substitution, neural-weight fusion or training
of the generator. Start from the original pinned Granite 4.0 1B checkpoint in FP32.
The eleven R16 selected heads and relevance threshold 0.65 remain fixed.

## Finite experiment

- Fresh authored development/test worlds and disjoint HotpotQA questions; exclude
  every earlier Hotpot question and authored entity. Preserve all ten complete
  Hotpot paragraphs; eligibility uses input length, never answers/support labels.
  Use 108 development worlds (one heavy context each), balanced across three
  relation wordings, depths 1–6 and missing/answerable status, plus 48 Hotpot
  development questions. Test 252 new worlds in light and heavy contexts plus
  200 Hotpot questions: 704 test inputs × nine arms = 6,336 outcomes. Six further
  Hotpot questions are mechanical admission fixtures. The R16 prompt is unchanged;
  the context ceiling increases to 3,072 tokens to obtain disjoint external data.
- Twelve interventions: additive/mass-conserving × all/prefill/fade-eight ×
  strength ln(16)/5. Select using development free-text accuracy and Hotpot F1,
  equally weighted by domain, with lower intervention cost breaking ties.
- Freeze intervention and two gate rules before test. Gates are selected using
  development utility `equal-domain quality - 0.02 * equal-domain call fraction`;
  selection and all candidates are public. No test-derived threshold changes.
  Native pilot length is eight tokens or earlier EOS. Gate features are minimum
  selected-token probability, mean token entropy, and word overlap with sources
  (a lexical proxy, not a semantic copying detector). Threshold candidates are the
  pooled development feature values at index `int(q*N)` for q = .1, .25, .5, .75,
  .9; both directions and always/never endpoints are available to the benefit gate.
  The uncertainty gate uses only low minimum probability plus endpoints. Ties use
  fewer calls then canonical gate JSON. Intervention ties prefer prefill, fade8,
  all; then lower strength, additive mode, stable policy ID. `fade8` uses
  `strength * max(0, 1 - generated_tokens/8)`; prefill includes first-token logits.
- Test native, R16 additive, mass-conserving all-token strength 5, selected always,
  uncertainty gate, benefit gate, matched random gate, lexical and shuffled
  relevance controls. Report duplicate policies as duplicates, not independent
  replications. Random gate uses the benefit gate's development call fraction.
  Execute benefit-gate first on every test input to measure actual prospective
  call avoidance. Randomize the remaining arm order. Reuse byte-identical Jev
  receipts across control arms to bound spending and isolate generation effects;
  report physical attempts separately from logical standalone calls, and distinguish
  measured gate latency from latency estimated by adding a cached call's duration.
- Four primary paired comparisons: selected always minus native, and benefit
  gate minus selected always, separately on authored accuracy and Hotpot F1.
  Individual 98.75% paired bootstrap intervals, 10,000 resamples by world/question.
  A gate preserves quality only if its lower bound exceeds the prespecified
  -3 percentage point noninferiority margin; call savings are a separate result.
  All other comparisons are exploratory 95% intervals. No all-controls gate.
- Preserve HTTP errors and ambiguous charges. On an unsuccessful Jev call, use
  native generation with an explicit fallback status; never silently replay.
  Report both end-to-end fallback quality and failure frequency.
  Preserve the provider error and fully reserve unknown usage; wait at least 60
  seconds or Retry-After before another distinct request. Stop after 20 incidents,
  three consecutive new failed calls, authentication/nontransient errors or the
  deadline. Incomplete schedules must be reported as incomplete, never successes.

## Work sequence and files

1. Check primary related methods and TypeSafe contracts; record known prior art.
2. Test-first implementation under `research/iterations/selective_attention/`;
   leave R14–R16 source/data/results immutable. Tests exercise mass conservation,
   causality, cached/full consistency, isolation, gate-before-API ordering,
   fallback, EOS, exact tokens and no-op identity.
3. Freeze cohorts, schedule, policy/gate grids and source hashes in a new protocol
   manifest. Validate independent graph truth, reference-free public views and
   no overlap. Use the existing durable journal, budget and one-attempt transport.
4. Run numerical/mechanical admission, development, freeze, then held-out tests
   on one inexpensive GPU. Bound compute/API use and capture source/runtime/weight
   hashes, phase timing, attempts, receipts and actual tokens.
5. Reconstruct all prompts, gate decisions, intervention schedules and final
   tokens offline; check all planned outcomes, paired identity, source/weight
   hashes and accounting. Inspect failures, not only averages.
6. Retrieve and verify artifacts before deleting cloud resources. Publish a new
   dated report with figures, all controls, cost, limitations and reproducibility;
   update notebook/register/manuscript and PR, run checks and inspect reviews.

## Limits and operational bounds

Prior cumulative estimated spend is $19.688713942733276 of the authorized $50.
This iteration reserves at most $15 for cloud and $3 for Jev, keeping a margin
for residual billing. One L40S-class GPU, hard poweroff expiry, a shorter runner
deadline and owned-resource cleanup; AWS is only a fallback if needed. No model
release, merge, paper submission or new account changes are part of this task.

The custom attention interface is a serial research implementation, not a
concurrent serving extension. Reject reentrancy and restore the original dispatch
on every exit. FP32 mechanical checks precede paid evaluation. Preserve any failed
admission and register amendments prospectively. If improvements fail, report that
result without selecting a new policy on exposed test data.
