# Development workflow rules

Follow [AGENTS.md](../../AGENTS.md) and the executable
[workflow](../../docs/development-workflow.md).

1. Read the request, relevant code/tests, scope/status, and affected flow.
2. Plan the goal, changes, corner cases, failure paths, and verification.
3. For changed behavior, observe the intended test failure before implementing;
   documentation-only work uses a validation plan.
4. Make the smallest scoped change; use existing helpers before adding abstractions.
5. Run focused checks, then relevant end-to-end and repository validation.
6. Review the diff, update docs/status, and follow [Git workflow](common-git-workflow.md).

Use primary documentation for changing API/runtime assumptions. Preserve working
local/offline workflows and dependency optionality. Do not add an unavailable tool,
extra model call, or persistent planning document without a task-related need.
