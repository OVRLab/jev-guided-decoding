# Test-driven development workflow

Repository reference guide, adapted from OVRLab's accumulated TDD guidance;
[AGENTS.md](../../AGENTS.md) remains authoritative. Read it directly when the host
does not have a skill loader. No named subagent or extra provider is required.

## Apply to a change

1. Define the observable behavior and the affected [flow](../../flows.md).
2. Write a deterministic regression/capability test. Set up inputs independently
   and assert the externally meaningful outcome, including a relevant failure path.
3. Run the targeted pytest command and inspect the failure. Record whether it
   demonstrates a missing feature, a reproduced defect, or only missing scaffolding.
4. Implement the smallest correction, rerun that test, and inspect the passing output.
5. Refactor only where it helps the changed code, then validate relevant integration
   paths and the [canonical checks](../../docs/development-workflow.md).

Use fake HTTP transports for provider errors, `tmp_path` for output, and the existing
tiny causal model for token/generation contracts. Keep clocks, seeds, resources,
and mutable state owned by each test. Tests should not depend on order, network,
the maintainer's key, or a downloaded checkpoint.

Cover accepted and rejected branches, stopping without new text, absent optional
fields, invalid numeric values, work already spent on rejected candidates, and
ambiguous failures when those contracts change. A test that repeats the same code
formula is weak evidence; assert the decision or trace the user relies on.

Documentation-only work uses a validation plan. If validation tooling changes,
test that tooling's failures before implementing. Live experiments remain separate
from offline checks; report actual setup, budgets, and outputs without claiming
that mocks establish model quality or that an unrun coverage tool passed.
