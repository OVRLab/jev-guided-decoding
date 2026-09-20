# Python testing details

Use pytest and the [test-first workflow](../skills/tdd-workflow.md). Name tests for
observable behavior. Use `tmp_path`, `monkeypatch`, fake transports, and independent
state; keep tests independent of order, credentials, network, and model caches.

Async tests can use the existing `asyncio.run` pattern; do not require an undeclared
plugin. Test timers/retries without long real sleeps. For backend work, use the
offline tiny causal model before a scoped device/model check.

Check raw returned values, usage, status, and accepted prefixes, not just nonempty
text or a zero exit code. Do not call a lexical score proof of factual correctness.
Use [flows.md](../../flows.md) to choose additional integration/end-to-end coverage.
