# R20 supplementary blind answer inspection

Registered after the main source freeze and before live evaluator admission or
new Granite test generation. This supplements interpretation without changing the
frozen judge, inference, grading thresholds or primary endpoints.

If evaluator admission succeeds and test grading completes, inspect the first 24
anonymous packets from the already randomly ordered packet file, after the grade
freeze and before treatment-level analysis. The coding assistant receives only
those packets, without arm identities or Qwen labels, and records binary semantic
judgments with short reasons. Compare these saved judgments against Qwen afterward,
retaining disagreements and the full sampling rule. Do not use the comparison to
retune the evaluator, select an architecture or replace registered primary scores.

This is a small descriptive check for evaluator transfer to actual generated
answers. It is not an independent human annotation study: the reviewer is the
implementing coding assistant, can access the wider repository and knows the study
hypotheses. Model identities and existing judge labels are withheld from the review
payload, but strict operator isolation is not claimed. Sampling is by unique packet,
not by case or arm, because identical case/answer pairs were deduplicated. Report
that unit and avoid treating its agreement fraction as a precise error-rate estimate.
If admission fails, there are no generated test packets to inspect; record that the
supplement was not executed instead of substituting validation fixtures.
