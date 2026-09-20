# End-to-end validation guide

Read [flows.md](../flows.md) and [development workflow](../docs/development-workflow.md).
Choose the complete changed flow, its expected outputs, and failure outcomes before
running it. This repository has no browser app or dedicated browser E2E suite.

Use offline controller/client integration tests and a tiny causal model where they
exercise the contract. For real tokenizer/device/provider changes, run the smallest
scoped model/fixture check that answers the uncertainty and inspect its trace,
not just final text. State which components were real, mocked, skipped, or unavailable.

For guidance edits, navigate entrypoints, check links/commands, and run the checker;
do not spend on live inference to validate an unchanged experiment. Preserve old
reports and write a new output path for new runs.
