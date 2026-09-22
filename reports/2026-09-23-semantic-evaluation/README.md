# R20: blinded semantic evaluation

Implementation and prospective protocol are complete; live evaluator admission is
pending. No new Granite quality result is claimed. This study directly supports
the Granite + Jev inference-architecture objective by testing the semantic meaning
of the score changes observed in R19.

The fixed comparison is native Granite, static instruction attention without Jev,
and R19 Jev dual guidance. An independent Qwen3-14B judge sees only anonymous
question/evidence/reference/answer packets. It must first pass constructed semantic
validation, including paraphrases, false refusals, wrong partial matches and
contradictions. This is automated evaluator blinding, not independent human review.

- [Prospective protocol](../../research/semantic-evaluation-plan.md)
- [Frozen protocol and inputs](../../research/protocols/semantic-evaluation-v1/manifest.json)
- [Evaluator and rubric](../../research/iterations/semantic_evaluation/judge.py)
- [Regression and flow tests](../../tests/test_semantic_evaluation.py)
- [Previous R19 results and measurement artifacts](../2026-09-22-benefit-sufficiency/README.md)

All 462 local tests passed in 8.01 seconds, including optional inference checks.
The eleven new tests include identity exclusion, strict/duplicate-key parsing,
admission failure, duplicate-answer consistency, blind-map tampering, unresolved
score bounds, no-provider native/static generation and capped judge output.
Original missing-module capability failures and the cap regression failure are
retained locally. Runtime token/cache mechanics and scientific R19 sources are
unchanged. No cloud resource has been launched at this registration checkpoint.

The new test cohort has 528 inputs and 1,584 planned generations. The evaluator
first grades 24 development, 96 validation and twelve repeated validation packets.
Source/data freeze and evaluator admission precede test generation. If validation
fails, the pipeline stops before new Granite test answers or hosted Jev calls.

Original Granite and Jev weights remain unchanged. The evaluator is
[Qwen3-14B](https://huggingface.co/Qwen/Qwen3-14B), Apache 2.0, pinned to revision
`40c069824f4251a91eefaf281ebe4c544efd3e18`. External model, dataset and provider
terms remain separate from the repository software license.
