# R24 disagreement inspection

This post-hoc, unblinded inspection covers **all five** disagreements between the
fixed Jev threshold and the recorded reference labels. It changes no labels,
scores, prompts or thresholds. The implementing assistant performed the reading;
it is not independent human adjudication. Exact inputs and receipts are in the
public archive.

| Case | Reference / Granite choice | Jev p(correct) | Observed content |
| --- | --- | ---: | --- |
| `mmlu_pro/55` | A / A | 0.26 | Granite selects Communist for a passage about workers and common ownership, matching the reference. Jev nevertheless assigns a low correctness probability; its receipt gives no rationale. |
| `musr/murder_mystery/212` | A / B | 0.57 | Granite selects Larry, citing weapon experience and political rivalry; the reference selects Sophia. Its explanation does not weigh Sophia's stated presence at the scene, possession of the weapon and threatened livelihood against those clues. |
| `musr/murder_mystery/134` | A / B | 0.77 | Granite selects Mya rather than reference Albert. Its rationale adds a claim that the weapon was discovered at her campsite, which the narrative does not state. The story supplies incriminating details for both suspects. |
| `musr/murder_mystery/213` | B / B | 0.44 | The final choice matches the reference, but the explanation claims no evidence connects Sophia to the weapon or a motive, contrary to explicit story details. Correct final choice and sound explanation are distinct measurements. |
| `musr/object_placements/31` | B / B | 0.41 | The reference asks where Sarah would look, not the microphone's actual final location. Granite selects the reference location but explains it using the initial actual location, without discussing Sarah's knowledge. |

Jev returns a probability, not an explanation of its judgment. These observations
cannot identify why it disagreed or prove that the reference is wrong. In
particular, the critic was explicitly instructed to judge the final decision;
it is only a hypothesis that flawed rationale could influence its false flags.
Future repair evaluation must measure final-answer regressions separately from
explanation corrections and independently review genuinely ambiguous references.

The two murder cases `212` and `213` share an identical opening, characters and
setting but have different narrative evidence and opposite reference answers.
They are related scenario variants, not independent stories. Their outcomes
remain separate recorded cases; R24's Wilson intervals and R23's problem-level
bootstrap do **not** adjust for that relationship. They are descriptive small
development summaries. Future split construction must exclude related scenario
variants as well as exact exposed IDs/content duplicates, and use the appropriate
story clusters for uncertainty. Identical openings identify this pair; they do
not prove that all remaining stories are unrelated.
