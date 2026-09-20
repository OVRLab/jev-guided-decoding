# Planner guide

Use [AGENTS.md](../AGENTS.md) before implementation. Produce the concrete goal,
affected files/interfaces, dependencies, corner cases, regression risks, and
verification. Separate current scope from possible follow-up work.

For this project, ask what observation would demonstrate the change: exact prefix
isolation, an EOS decision, bounded API behavior, or measured quality/cost. Identify
which checks are offline and which need optional hardware/provider access. Keep
durable plans only when the decision needs to outlive the task.
