# R13 V2: shared final-label grammar

Registered after the complete V1 development pilot and before further live model
inference or any R13 test outcome. All earlier raw files and frozen manifests are
retained. See [V1 protocol](structured-study-protocol.md) and its
[failed-pilot report](../reports/2026-09-21-structured-study/README.md).

V1 completed 168/168 jobs and 192 authenticated Jev calls with no service/backend
errors. All 960 lookahead claims were independently gradable, all 240 checkpoints
were reached, all 168 token audits passed, and staged/zero matched 24/24 pairs.
However, only 121/168 final responses obeyed the output contract. Failures included
empty EOS and explanatory prose reaching the 16-token ceiling. No test job was
admitted. Both before/after model digests matched. This is a failed formatting
pilot, not a successful quality evaluation.

V2 changes only the common final-generation implementation and associated work
accounting/audit. Every arm now greedily generates under a token trie containing
exactly `TRUE</final>`, `FALSE</final>`, and `UNKNOWN</final>`. Code supplies the
opening delimiter and the complete set of syntactically valid alternatives;
Granite's original probabilities determine the semantic label. Jev never scores
or chooses that final label. The mask has no access to references or rule closure.
No response string is substituted for model-generated token IDs.

The final loop reserves 16 forward calls and 15 seconds independently of reasoning
budgets, uses the exact accepted prefix, and records each token/prefix/probability
and repeated prefill count. Closing tokens may have only one syntax-permitted
choice; this is disclosed constrained generation, not learned formatting ability.
The first label choice remains Granite's greedy choice among all valid labels.
Format success is therefore principally an operational property of this shared
constraint. The native arm is now **direct Granite with constrained labels**, not
unconstrained free text. All seven arms have this identical final restriction.

All other V1 commitments remain: same authored development worlds (now exposed),
same still-unseen 300 test worlds, seeds, seven arms, prompts, intermediate grammar,
lookahead/rubric, bias/KL limits, operational gates, planned 168 + 6,300 jobs and
world-clustered primary comparisons. The frozen V2 files record new source hashes
and identical data hashes. No optimization uses test outcomes. V1's reported
format/accuracy results are not recomputed under V2's changed generation method.

Tests first observed missing final-runtime/controller support, then verified all
three labels remain available, the real tiny model determines the chosen token,
reasoning-budget exhaustion cannot consume the final reserve, and independent
final-prefix reconstruction rejects altered traces. The Granite tokenizer itself
is checked locally before GPU execution. The existing L40S is retained during this
active repair; its original 18-hour deadline and cumulative $50 authorization
remain unchanged. V1 consumed 270,264 Jev input tokens ($0.011351088 at list price).
There is no new spending allowance. The shared server ledger continues in place.
