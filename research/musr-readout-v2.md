# MuSR final-line readout correction — v2

The zero-API [native readability admission](musr-native-admission-v1.md) completed
on twelve already exposed questions with 11 readable selections, two exact format
passes and no length stops. One rejected response repeats the question before an
otherwise exact numbered choice. No reference answers or accuracy were examined.

Before fresh public inference, extend the reference-free parser as follows: when
there is no `ANSWER:` field and the response has multiple nonempty lines, consider
only its last nonempty line, and accept it only if it explicitly gives one valid
number **and** the matching full option text. Preserve offsets into the actual
response for memory extraction. A bare trailing number, option text alone after
prose, contradictory number/text, multiple choices or unfinished thinking remains
unreadable. This fallback is never an exact requested-format pass. An explicit
but invalid `ANSWER:` field still takes precedence and remains invalid.

Write regressions and observe the old parser fail the intended capability first;
then implement, reparse all twelve saved outputs without model calls, and preserve
both readout counts. Recheck exact original-token span extraction. Do not change
the prompt, outputs, limits or model based on this inspection. Future scores must
name this parser version and disclose its difference from the author's evaluator.
This is a development-set readout correction, not an accuracy improvement or an
independent generalization result. R31 sources and its running study are unaffected.

## Offline result

The new final-line regression first failed because v1 returned no selection; all
eight focused interface/provider/audit tests then passed after implementation.
[Offline replay](diagnostics/musr-single-interface-20260926/native-readout-v2.json)
reads **12/12** saved selections and still reports **2/12** exact formats. Exact
original-token memory alignment also passes for all twelve responses. This replay
made no model/API calls and used no reference labels. The original v1 archive and
11/12 count are preserved. The parser identifier is `musr-exact-selection-v2`.
