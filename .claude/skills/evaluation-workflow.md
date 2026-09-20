# Evaluation workflow

Project-specific extension of OVRLab's evidence-before-claims and evaluation-driven
development lessons. Follow [AGENTS.md](../../AGENTS.md) and [FEATURE.md](../../FEATURE.md).

Before experimenting, define the hypothesis, baseline/control modes, datasets and
rights, validation/test split, independent rubric, seeds, budgets, and stop criteria.
Check which component actually supplies the scored output. For generator-quality
claims, test that the generator owns the final tokens in all arms and that system
instructions, examples, task instructions, and grading require the same format.
Keep target/reference answers out of generation and scorer inputs. Preserve failed,
empty, incomplete, and rejected runs in the denominator or explicitly disclose
any exclusions and their reasons.

Separate candidate-generation benefit from scorer-selection benefit. Compare actual
prefill/decode work, padded slots, accepted tokens, retries, and HTTP attempts;
equal configured ceilings are not equal compute. Record elapsed time, load/warm-up
treatment, concurrency, device/dtype, revisions, and provider usage/pricing assumptions.

Do not tune on held-out cases, rerun only poor cases until they improve, or use Jev's
own scores as independent proof that its choices were correct. Report lexical metrics
as lexical metrics, qualitative review as such, and uncertainty appropriate to sample size.

Keep raw public-safe inputs, candidates, decisions, returned model versions, and
summary provenance together. Write a new dated report for a new experiment;
never rewrite historical evidence to match a desired conclusion. Negative results
and differences from a hypothesis are findings, not reasons to hide a run.


When joining generated outputs to an oracle, verify the recorded question and
source evidence as well as the case ID. A reused ID can otherwise attach a valid
label to a different problem. Keep missing planned runs in the denominator.
