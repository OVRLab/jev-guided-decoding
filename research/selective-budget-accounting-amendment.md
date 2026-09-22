# Budget-frontier fallback accounting repair

Registered 2026-09-22 while held-out inference was running, before any held-out
aggregate inspection or execution of the supplementary analysis. This changes
only hypothetical work accounting in the separately registered offline budget
frontier. The live R17 source, schedule, prompt, policy and gates remain unchanged.

Code review found that the offline helper counted a fresh guided prefill and
discarded native pilot whenever a rule requested Jev, including when the shared
receipt failed. The actual runtime reuses the native pilot after a failed request.
The repaired helper therefore counts native work on failure, while preserving the
requested call and its unknown-usage charge. Quality replay still uses the recorded
native fallback and does not change any output or grade.

A new negative-path capability test first failed because the work helper lacked a
provider-failure input; after the repair it verifies native forwards, one prefill
and zero discarded tokens. Existing successful-call and no-call checks also pass.
No model generation or provider request was replayed for this repair.

The original [selection](protocols/selective-budget-frontier-v1/selection.json)
and original source in commit `d9249ea` remain available. The repaired source is
bound by [selection-v2](protocols/selective-budget-frontier-v1/selection-v2.json).
An explicit equality check verifies that policy, development data binding, every
selected rule, and all candidate development scores are unchanged. Only source
hash and registration timestamp differ. The original plan remains unchanged;
this note discloses the operational correction instead of silently replacing the
original freeze. Use selection-v2 for the final supplementary analysis.
