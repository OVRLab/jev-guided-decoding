# Python reviewer guide

Read [AGENTS.md](../AGENTS.md) and the
[Python rules](../.claude/rules/python-coding-style.md). Review changed code and
callers before commenting; use the repository's existing lint and test commands.

Inspect runtime validation independently from annotations, optional imports,
context-manager cleanup, device/dtype assumptions, tensor lifetime, and exception
classification. Check awaited tasks, blocking work on the event loop, lock ownership,
and whether cancellation actually ends the underlying model/provider work.

For generation, inspect EOS/padding, full-versus-fragment text decoding, token
likelihood normalization, cache isolation, and count definitions. For records,
inspect JSON-serializable finite values, explicit missing judgments, no-overwrite
output behavior, and whether summaries match raw evidence.

Report concrete defects and evidence; do not weaken lint/tests or add undeclared
type-checking requirements just to complete a review.
