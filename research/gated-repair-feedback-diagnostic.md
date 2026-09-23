# R25 feedback agreement diagnostic

Specified 2026-09-23 during held-out repair generation, after API collection and
before inspection of held-out correctness. This is a **post-start descriptive
supplement**, not a change to primary metrics, a new superiority endpoint or a
preregistered-before-inference claim. No new model/API calls or label changes.

Purpose: distinguish a weak correctness signal from a repair branch that fails
to use a useful signal. On the completed, independently audited test cohort,
join Jev's actual probability of native-answer correctness to the native answer's
fixed reference grade. Jev is a critic here, never a competing answer generator.
These measurements cannot substitute for Granite-generated-answer accuracy.

Report both domains and their union. Flag for repair exactly when p(correct) is
less than 0.5, matching the existing retention policy; ties retain native. Report
errors flagged/missed and correct answers flagged/retained, with their counts and
denominators. Missing feedback remains missing and is excluded from critic
statistics with its count shown, while primary generation scores retain every
planned case. Do not treat neutral fallback as a Jev observation.

Compute descriptive error-detection AUROC by all error/correct pairs using
1−p(correct), awarding half credit for ties; return null when either class is
absent. Show both all available cases and the parseable-native subset. This
distinguishes disagreement caused by the registered output format from agreement
on parseable answers; it does not establish semantic correctness of unparseable
answers or recalibrate the threshold. No significance test, threshold search or
claim of a new generator score is introduced.

Require the completed primary tokenizer audit and its bound raw files. Verify
one-to-one case, native grade and feedback coverage, valid finite probabilities,
and explicit missing-feedback provenance. Test tied scores, p=.5, one-class and
missing strata, duplicate evidence and corrupt source bindings before use. Publish
the helper source hash and primary-analysis hash with the derived result. Keep
the source-data, primary, training, delivery and retention audits unchanged.
