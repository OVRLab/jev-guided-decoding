# R16 output-form diagnostics (offline, registered 2026-09-22)

While main evaluation is running and before consulting aggregate held-out quality,
record these descriptive counts to make the relaxed output contracts reviewable.
This adds no inference, retuning, new correctness metric or primary comparison.
The original parser, outcome denominators and all generated text remain unchanged.

For every test family/contract/arm, count planned recorded outcomes, completions,
provider failures, final EOS versus token-limit endings, and reasoning phase
endings. A one-token constrained answer normally ends at its token limit; that
does not indicate an incomplete label. A full-vocabulary token-limit ending means
the configured generation budget was reached, not proof that its answer is wrong
or that additional tokens would fix it. Report correctness among those endings
descriptively without removing them from the original denominator.

For synthetic tasks, use the already frozen parser to count recognized abstentions.
Separate a bare case-insensitive `UNKNOWN`, optionally followed by one period or
exclamation/question mark, from other recognized abstention text. A longer phrase
containing “unknown” belongs to the latter category. This is a surface-form count,
not a human semantic annotation. Report correct abstentions and abstentions on
answerable cases separately. Unrecognized language remains unparsed; do not repair
the parser or infer correctness from the reference while extracting an answer.

Bind the exact input output-file SHA-256 to the completed injection audit before
analysis. Preserve all counts in JSON and show full-vocabulary summaries in the
report. Tests cover natural versus bare abstention, harmful abstention, failed
outcomes, EOS/token-limit distinctions and a changed artifact digest. These are
descriptive diagnostics of the same cases, not fresh statistical replication.
