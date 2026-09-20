# Refactor guide

Read [AGENTS.md](../AGENTS.md). Establish passing behavioral coverage before cleanup;
for an uncovered contract, add the missing check first. Keep refactoring scoped to
the requested area and preserve interfaces, token identity, outcomes, and metrics.

Do not combine unrelated renames, formatting, dependency upgrades, or parameter
tuning with a bug fix. After changes, rerun affected tests and the relevant complete
flow. If behavior or measurements change, describe it as a behavior change rather
than labeling it a pure refactor.
