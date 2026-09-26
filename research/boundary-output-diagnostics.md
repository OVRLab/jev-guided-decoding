# R18 descriptive output diagnostics

Registered after the frozen GPU run started, before inspecting any development or
held-out quality aggregates; a subsequent progress check showed development running.
This supplements the existing output/subgroup requirements in the frozen
[plan](boundary-attention-plan.md); it changes no generation, selection, scoring,
primary contrast, or confidence interval and incurs no model/API work.

After the main audit, bind its JSON, the original result bytes and the test cohort
with SHA-256. Verify that binding and reconstruct the frozen grades before reading
diagnostics. Preserve all nine arms and all three domains. Count EOS, token caps,
empty decoded answers, recognized abstentions, bare UNKNOWN, wrong abstentions,
unparsed authored answers, failed provider fallbacks, logical/physical calls and
raw SQuAD EM/F1. Report descriptive authored family/depth/context/missing groups,
SQuAD answerability/article/source-count groups and Hotpot question-type groups.
No subgroup significance tests or rule fitting are added.

For boundary, pilot and random gates, compare the existing native/always quality
on each input and tabulate called beneficial/harmful/tied cases and skipped
beneficial/harmful/tied cases. These outcome-derived labels diagnose selection;
they were unavailable to the inference-time gate. Failed calls remain calls even
when their treatment falls back. A lexical score change is not a human judgment.

Select illustrative examples deterministically by the first sorted case ID in
each domain for: guidance improves quality, guidance harms quality, gate skips a
benefit, gate skips a harm, correct recognized abstention, wrong recognized
abstention, and unrecognized nonempty output on a missing-evidence case. Record
empty categories. Display complete evidence, reference, native/always/gate output,
recorded features, decision and relevant provider receipt status. Examples are not
representative sampling, blinded human evaluation or a new grading contract.

Render the registered three-domain quality, routing intervals, call fractions,
mean/median/p95 timing, actual prefill/layer-token work, output forms and
answerability groups from the audited JSON. Report feature-observation overhead
using matched never/always branches; shared-receipt uncached timings remain
reconstructions. Keep physical API spend separate from logical standalone use.

Addendum recorded during held-out execution, before inspecting test quality
aggregates: distinguish successful calls with at least one active head from
successful calls with no active heads under the fixed uniform-score no-op rule.
Count final-token-path changes relative to native separately. Break out source
count as already registered for SQuAD; one-source contexts cannot produce mixed
source threshold decisions. These are descriptive execution counts, not a new
selection rule or additional significance test.
