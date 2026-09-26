# R29-A localized correction capacity study

**Running, 2026-09-26. No test-quality result yet.**

The [registered protocol](../../research/structured-correction-plan-v1.md) tests
whether targeted Jev judgments can drive useful repairs through a trained internal
Granite branch while preserving correct answers. The [design proposal](../../research/structured-correction-proposal.md)
records its motivation and prior work. The north-star objective remains unachieved.

This is an **authored mechanism diagnostic**, not IFEval, IFBench, another public
benchmark, unseen-template generalization, or evidence of superiority to larger
models. Its 256 worlds comprise 128 training, 32 development and 96 held-out cases,
balanced across temporal object tracking and compositional container/room tracking.
Every case requests three room names; all three correct is the primary readout.
Formatting is reported separately. No constrained decoder or fixed UNKNOWN is used.

The new 262,144-parameter branch follows zero-indexed block 19 of frozen dense
Granite 4.0-1B. Attention over three question/draft span representations binds
localized correctness probabilities to the residual transformation. Original
Granite and Jev weights stay frozen, and Granite generates every final token.
Correct training drafts retain their exact generated token sequence as targets;
incorrect drafts use independently constructed corrections.

Five equal-capacity conditions use matched initialization, data, optimizer and two
seeds: structured live feedback, one scalar score, constant feedback, live feedback
provided as text, and a nondeployable oracle diagnostic. Held-out comparisons also
include native generation, blind repair and shuffled structured feedback. The
checkpoint and secondary retention threshold are selected only on development data
and saved before any test generation. Primary comparisons concern raw candidates;
offline retention is not a claim of measured API or generation savings.

## Admission and execution evidence

- Source `71bf96440cb7c3bde7a06139df5677e6fc142864`; frozen manifest SHA256
  `025db0b26b7c3c6223ab4e66bd0aaf092f1b05be4286069872e87e2f97fd26cc`.
- All 661 local tests, lint, format, documentation check and build passed; all four
  CI jobs passed. Nine relevant tests also passed in the cloud environment.
- Actual Granite FP32 MPS and CUDA checks passed: initial/off identity, adapter-only
  gradients, cached/full agreement and equal argmax. Maximum logit differences
  were 0.0000748634 on MPS and 0.0000305176 on CUDA.
- [API admission](../../research/structured-correction-admission-v1.md) succeeded
  operationally on six constructed fixtures, but only 16/18 slot judgments were
  correct. The all-correct fixture flag is false and remains disclosed. Questions
  and data were not changed after this finding.
- A separate **artificial** 2,144-output artifact smoke test passed statistical
  reconstruction and rejected missing-output and changed-Jev-draft attacks. Those
  synthetic scores are pipeline tests and are excluded from research results.
- One AWS L4 was launched at 05:59:21 UTC. The worker started at 06:03:52 UTC, with
  a 4.5-hour experiment deadline and an independent five-hour host shutdown.
  Incremental backups run every minute and cloud checks every 15 minutes.

## Completion requirements

The full study expects 2,144 generated outputs, 256 successful Jev requests,
2,560 training examples across epochs/conditions/seeds, and ten selected adapters.
An underpowered development cohort or operational failure stops before the
appropriate next stage; incomplete work will not be called a full result.

After completion: verify final backup inventory and hashes, remove owned cloud
resources, audit exact prompts/tokens/judgments/checkpoint selection and independent
reference replay, then publish scoped scores, paired effects, damage/recovery,
feedback dependence, work and reconciled costs. All outcomes, including negative
or interrupted results, will remain in the research record.

The stage reservation is $8.412 within a cumulative $125 ceiling, starting from
the prior conservative estimate of $113.99886002437508. Reservation is not actual
spend or an invoice; taxes/network remain unconfirmed. No broad benchmark run,
model release, paper submission or architecture improvement is established here.
