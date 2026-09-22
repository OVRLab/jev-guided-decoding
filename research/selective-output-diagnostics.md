# R17 prospective descriptive diagnostics

Registered during live development, before held-out aggregate results were
inspected. No change to source policies, selection, gates, scoring or inference.
In addition to the frozen analysis, report authored accuracy and gate calls by
relation wording, depth, missing/answerable status and light/heavy context.
The authored cohort is balanced missing/answerable; constant abstention has a
50% reference accuracy and zero answerable accuracy.

For every domain/arm, count EOS versus token-cap termination, parsed coverage,
recognized natural abstentions versus the bare UNKNOWN spelling, correct and
incorrect abstentions, and failures/fallbacks. Use the unchanged R16 parser only
for descriptive tagging, without regrading outputs or interpreting unparsed
text as automatically wrong in a broader semantic sense.

Prepare at most eight examples, selecting the first lexicographic case ID for
each category: authored always-guided fixes native, authored always-guided harms
native, benefit gate skips and avoids harm, benefit gate skips and misses a fix,
Hotpot always-guided EM fix, Hotpot always-guided EM harm, correct natural authored
abstention from the benefit-gate arm, and wrong positive answer on an authored
missing-evidence input. State when a category is empty. Show full evidence,
references, native/always/gated outputs, gate decision and observed features.

These examples are illustrative automatic selections, not blinded human labels,
an additional benchmark or a causal diagnosis. Manually distinguish formatting-only
EM changes from different factual answers. Do not use examples to alter the frozen
parser or tune a new test policy. Diagnostics bind to the completed main audit's
artifact hashes before reading outputs.
