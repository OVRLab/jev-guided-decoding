# R23 fixed qualitative inspection

The [recorded selection rule](qualitative-method.md) chooses the first two
primary-incorrect cases per task/model by SHA256(`r23-review/` + case ID).
All sixteen selected cases appear below, including format-only failures and
cutoffs. This is a small, unblinded inspection by the implementing assistant,
not an independently annotated error taxonomy. No score or generation was changed.

| Model | Case | Observation |
| --- | --- | --- |
| 1B | `gsm8k_train/7376` | Reports 20 remaining after the trip but misses the subsequent halving; reference 10. |
| 1B | `gsm8k_train/6198` | Correctly computes 26 in the explanation, then leaves the literal numeric-answer placeholder. Primary extraction fails. |
| 1B | `ifbench/57` | Produces a detailed SQL interview question but fails the required unique-word constraint. |
| 1B | `ifbench/180` | Fails the increasing-alliteration constraint. Independently of that checker, its response omits the requested Ideal Gas Law. |
| 1B | `mmlu_pro/25` | Explanation says three spectrum lines but selects C, whose option text is four; reference is B, eight. The internal inconsistency is directly visible without attributing the failure to a particular hidden process. |
| 1B | `mmlu_pro/2` | Describes a solution procedure but ends with −5 (A), versus reference −4 (E), without completing the required integer search. |
| 1B | `musr/object_placements/85` | Selects the complete option A, Fred's pocket, matching the reference. Primary extraction rejects the missing final marker; the post-hoc full-option readout recovers it. |
| 1B | `musr/team_allocation/165` | Selects complete option B instead of reference A. The additional readout recovers an unambiguous decision but does not make it correct. |
| 3B | `gsm8k_train/1792` | Interprets twice as many lilies as twice the roses, yielding 390; the reference uses twice the snapdragons, yielding 290. This is an interpretation difference, not an addition error. |
| 3B | `gsm8k_train/1393` | Reaches the 8,192-token ceiling after closing thinking but beginning only a fragment of the final answer. No numeric decision is available. |
| 3B | `ifbench/180` | Hits the ceiling during thinking; no final answer to check. |
| 3B | `ifbench/207` | Hits the ceiling while working through the consonant-cluster constraint; no final answer. |
| 3B | `mmlu_pro/25` | Hits the ceiling during thinking; no final choice. |
| 3B | `mmlu_pro/18` | Selects email marketing (C), versus reference door to door (G). A parsed wrong choice alone does not distinguish missing knowledge from faulty interpretation. |
| 3B | `musr/team_allocation/165` | Hits the ceiling during thinking; no final choice. |
| 3B | `musr/murder_mystery/134` | Hits the ceiling during thinking; no final choice. |

The runner's `complete` status means thinking has closed and a nonempty final
segment exists; it does **not** certify a finished or correct answer. The partial
3B math response illustrates why finish reason, parser outcome and task grade are
reported separately. Across the entire 3B schedule, 13 outputs stop at the length
ceiling: twelve during thinking and one after a partial final segment. All thirteen
receive no primary credit. Native 1B has no length stops.

The original 1B MuSR primary score of 0/12 is dominated by eleven missing-marker
readouts; the post-hoc score is 6/12. The 3B primary and secondary scores are both
4/12. Consequently, a primary-score gain from 0 to 4 cannot be described as a
demonstrated narrative reasoning improvement over 1B. Equally, this small,
cap-limited comparison does not establish that 1B is generally better than 3B.

Three engineering targets follow from observed behavior: preserve clear decisions
when improving output formatting; evaluate wrong-answer repair separately from
explanation repair; and measure whether additional reasoning actually finishes.
Jev's [separate critic diagnostic](../2026-09-23-public-critic/README.md) tests error
detection only. It does not establish any of these repair capabilities or select
an optimal internal layer. Its [disagreement inspection](../2026-09-23-public-critic/disagreements.md)
also identifies related story variants and a distinction between correct final
choices and flawed explanations.

Exact questions, references, final answers and token streams are preserved in
the [protocol](../../research/protocols/public-baseline-v1/manifest.json) and
[public artifacts](artifacts/). The frozen primary results, post-hoc readout and
all failures remain reproducible.
