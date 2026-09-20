# Testing rules

Apply [AGENTS.md](../../AGENTS.md) and the [TDD workflow](../skills/tdd-workflow.md).
For behavior changes, write the test, observe the expected failure, implement the
minimum change, and verify the regression plus affected flows. Do not retrofit
claims of test-first development after the fact.

Use independent fixtures and Arrange–Act–Assert. Test observable contracts, not a
copy of the selection formula or mocks that merely reproduce implementation.
Include least-initialized inputs, budget boundaries, nonfinite/type-invalid values,
early EOS, Unicode/token boundaries, provider failure, and cancellation when relevant.

Keep unit/integration checks offline with fake transports and deterministic small
models. Distinguish these from scoped live provider/model verification. Report
optional dependency skips and absent hardware honestly; do not disable failing
tests to make a change green. There is no configured percentage coverage gate yet.

Documentation-only changes use the guidance checker and navigation/command review.
Only rerun live benchmarks when changes or unresolved findings justify their cost.
