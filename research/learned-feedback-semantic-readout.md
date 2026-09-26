# R22 descriptive complete-color readout

Registered at 05:42:52 UTC while test draft preparation was underway, before
any final test answer or aggregate test inspection. The initial timing description
incorrectly said training was still underway; the local progress copy lagged the
remote worker. The [timing record](../reports/2026-09-23-learned-feedback/readout-timing-correction.json)
preserves this correction; no readout pattern or primary metric changed. Keep the primary whole-color metric and all source freezes
unchanged. This is a secondary diagnostic of answer-format confounding, not an
extra architecture selection endpoint or a general language judge.

Independently of the reference color, recognize a whole color word (optionally
wrapped in quotation marks or Markdown bold), `color badge`, `a color badge`,
`it is color`, `the color is color`, `the badge is color`, or
`the badge color is color`, allowing case, whitespace and one terminal period.
The word `color` in these templates stands for one of the eight dataset colors.
Everything else is unresolved: do not extract a correct-colored substring from
negation, multiple alternatives, incomplete text, a citation or arbitrary prose.
Compare the extracted color with structural truth only after parsing the answer.

Report matched/resolved/unresolved counts per arm and lower/upper correctness
bounds when unresolved text remains. These accepted templates denote complete
answers to the color question, but are not an exhaustive English semantic
evaluator. Do not turn unresolved text into a verified error, tune patterns on
test, or use this diagnostic to select a checkpoint. Keep raw answers and primary
grades. A separate method field records when this protocol/code were frozen.

Sources: [R22 primary plan](learned-feedback-bridge-plan.md),
[independent readout](diagnostics/learned_feedback_semantics.py).
