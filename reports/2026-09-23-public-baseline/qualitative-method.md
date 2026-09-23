# Descriptive inspection rule

Recorded after generation began, before reading diagnostic grades. This is not a
new primary metric or a preregistered causal error taxonomy. Select at most the
first two incorrect outcomes per task and model, ordered by
SHA256(`r23-review/` + case ID). Inspect the original question/reference and final
answer; retain unparseable, truncated and empty outcomes in this selection.
Report observations and counterexamples without changing grading or rerunning
cases. A small non-blind inspection by the implementation agent cannot establish
independently annotated semantic accuracy or the cause of all model failures.
