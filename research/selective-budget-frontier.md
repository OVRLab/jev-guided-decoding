# R17 development-frozen call-budget frontier

Registered 2026-09-22 after development selection and while the held-out run was
in progress, before inspecting held-out aggregate quality. This is a separately
registered exploratory **offline branch replay**, not a new live arm or one of the
four primary comparisons. It preserves the original protocol and its outcome:
the quality-minus-0.02-call-cost objective selected an always-calling gate.

## Question and frozen procedure

Can a smaller Jev call budget retain useful improvement over native Granite?
For each development call ceiling 0.25, 0.50 and 0.75, select from the exact R17
threshold candidates (three pilot features, five development quantiles, both
directions, always/never). Maximize equally weighted authored accuracy and Hotpot
F1 subject to the **unweighted development fraction** of calls being at most the
ceiling. Break ties by fewer development calls, then canonical gate JSON. Include
the no-call rule so every ceiling has a feasible choice. The selected guidance
policy remains the R17 development winner; do not search it again.

Freeze the three selected rules and their complete development candidate scores
in a tracked JSON file before inspecting held-out aggregate quality. Bind that
file to the development selection, this plan, and the implementation with SHA-256.
Do not change rules after test results. Development ceilings need not hold on the
test distribution: disclose realized calls in both test domains and overall.
These are request-count ceilings, not token, dollar or latency ceilings.

## Evaluation and accounting

After the main run is complete and its independent artifact/provenance audit
passes, apply each frozen rule to the native pilot features already recorded for
each test input. Choose the exact recorded always-guided output if the rule calls,
otherwise the exact native output. The main audit proves actual gated branches
have the same token identities. Reuse does not create new independent examples.
No reference answer enters the rule at inference; development grades train the
small threshold selector in the same way as in the main study.

Report all three rules and both domains, including quality, actual replay call
fraction, expected random-routing quality at that same count, and routing value.
Report paired exploratory 95% world/question bootstrap intervals (10,000 draws)
for replay-minus-native, replay-minus-always and routing value, plus routing's
existing fixed-count permutation diagnostic. Keep paired light/heavy contexts
together for confidence intervals. There is no confirmatory significance claim
or selection of a winning budget using these test results.

Account for prospective model work exactly from the recorded deterministic
branches: skipping requires native final forwards; calling requires native pilot
forwards plus the fresh guided final forwards and an extra prefill. Report discarded
pilot tokens and processed tokens. Report selected receipt input tokens as a
hypothetical call-token bill. These are **reconstructed work/call counts**, not
measured throughput, new API requests, actual cloud savings or live gated latency.
Any failed common receipt retains its native fallback and unknown token charge.

Preserve all original raw artifacts. Analyze only audit-bound files and reject
modified frozen rules, changed development selection or changed study artifacts.
Test independent fixtures for budget feasibility, development-only selection,
branch/work reconstruction and tamper rejection before analyzing test quality.

Implementation: `research/diagnostics/selective_budget.py`. Selection artifact:
`research/protocols/selective-budget-frontier-v1/selection.json`. No paid call or
new model forward is authorized by this supplementary script.
