# R20 evaluator transfer failures

The [blind inspection](blind-review.md) exposed two clear cases where Qwen credited
an answer that did not supply the requested fact, and a third disagreement involving
an ambiguous unanswerable label. The fixed [illustrative examples](examples.md)
then exposed the same problem outside the blind sample. These are additional
unblinded diagnostics, not new primary endpoints or a regraded test.

The first authored score repair changes an incorrect red-room answer to only
`[E02]`. Qwen calls the citation correct while deriving black from evidence E02/E03
in its own reason. In the authored regression, it rejects `[E01]` for omitting the
terminal colour. In the Hotpot regression, it credits a static answer that ends
after “born on 3 June” without the requested year, supplying 1865 in its reason.
The evaluator is inconsistently completing the candidate's answer itself.

A subsequent narrow syntax count identifies responses consisting only of bracketed
evidence IDs, whitespace and optional punctuation. It does not identify all incomplete
or wrong-type responses. Counts below include every matching generated outcome;
the judge has graded exact duplicate case/answer pairs only once.

| Domain | Arm | Citation-only outputs | Qwen credits as correct |
| --- | --- | ---: | ---: |
| Authored | Native | 14 | 1 |
| Authored | Static | 0 | 0 |
| Authored | Jev dual | 18 | 8 |
| HotpotQA | Each arm | 0 | 0 |
| SQuAD2 | Native | 1 | 1 |
| SQuAD2 | Static | 0 | 0 |
| SQuAD2 | Jev dual | 1 | 1 |

The [machine-readable diagnostic](citation-only-diagnostic.json) retains the exact
regular expression and every matched output/grade. It is reproduced by the
[editorial reporter](../../research/diagnostics/semantic_evaluation_report.py).
The rule was chosen after the fixed examples were inspected. No primary score,
reference or confidence interval is changed, and no error-adjusted quality claim
is substituted. These counts are not a comprehensive estimate of judge error.

The positive authored contrast is therefore a real effect on the frozen judge's
scores, with known measurement error and an unresolved amount of semantic benefit.
The inspection neither establishes that every gain is an artifact nor validates
the remaining gains. The artifact field `quality_claims_admitted` checks the
registered unresolved-packet threshold; it does not certify evaluator transfer or
human-verified correctness. All 1,070 test judgments parsed, so that field is true
despite the substantive mistakes documented here.

The next evaluator needs tests where plausible supporting evidence is present but
the candidate gives only a bridge entity, a citation or an unfinished response.
Its job is to judge the candidate's answer, not solve the question on the candidate's
behalf. Independent review of benchmark questions, references and answerability is
also needed; these exposed cases cannot serve as fresh validation for a revised judge.
