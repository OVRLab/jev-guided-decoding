# R23 secondary readout admission (post hoc)

Recorded 2026-09-23 after all native outputs and the fixed native qualitative
packets were inspected, while larger-model generation is still running. Preserve
the frozen primary protocol, outputs and scores. No inference is rerun or changed.
This secondary development diagnostic is **not preregistered** and must not
replace the primary or enter a final benchmark scorecard.

The primary explicit-Final parser rejects 11 of 12 native MuSR outputs. The first
fixed inspection includes an unambiguous correct full-option first line rejected
only for lacking `Final:`. Native math also contains a correct computed total
followed by a literal formatting placeholder. Thus primary strict readout success
cannot be reported as general reasoning accuracy.

For choice tasks only, admit an additional conservative readout: if the primary
parser is unparseable, match a complete standalone answer-option line against
**all** options in the question. The label and full option text must agree;
normalize only case/whitespace and terminal sentence periods/markdown emphasis.
Require one unique matched option and reject competing option-labeled lines.
Do not match a word somewhere inside reasoning, infer an option from its reference,
use Jev as judge, or choose a fallback at random. Apply the same rule to every
choice output from both models; preserve all remaining ambiguity as unparseable.
Report primary and secondary counts side by side, not a corrected official score.
Math/IFBench retain their original evaluators. Manual observations of correctly
computed but malformed math are qualitative, not an invented semantic aggregate.

The upstream MuSR evaluation file at
`b1f4d4168a9cfc6760e8b74d728e4516023dfaa5` uses a different numbered ANSWER prompt
and random selection if extraction fails. We do not borrow that fallback as
semantic evidence. Full-task admission must separately specify official metric
parity, formatting and real-answer validation; R23 remains a development diagnostic.

Validation: test before implementation on invented option texts, including
contradictory choices, label/text disagreement, incidental reasoning mentions,
and a valid explicit final that revises an earlier choice. Bind outputs to frozen
case IDs/prompts, retain both extraction provenance and independently joined
references, and archive every primary/secondary disagreement for inspection.
