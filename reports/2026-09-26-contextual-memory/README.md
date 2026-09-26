# R31 matched contextual memory — running

**Execution began 26 September 2026 at 12:44 UTC** on one AWS g6.xlarge L4 in
Frankfurt. [Prospective protocol](../../research/contextual-memory-plan-v1.md)
compares twelve matched adapters using contextual or position-matched embedding
memory, structured/scalar/constant feedback and two seeds. Scalar is the lead
chosen from completed R30 evidence. No R31 quality result is available yet.

The planned 512/64/256 split is fresh and independently replayed. The study records
11,840 generated outputs, 832 Jev requests, 832 extractions, 12,288 training-example
passes and 1,536 optimizer updates. Granite supplies every final token. Memory
extraction and training targets remain separate, and selected checkpoints freeze
before test generation. Original Granite and Jev weights stay frozen.

Source: `30bb4bc184d3ce553af9b4f59f8e0da17a6a2eaf`.
Frozen manifest: `78af8126bb8f3cccaf893b26ea88ed4695bdaf85a52f6d5ce8cdbb6a7fa4fe65`.
All 695 local tests and four CI jobs passed at this source; 22 relevant tests passed
on the actual worker. CUDA mechanical admission passes initial/off identity,
original-weight/gradient ownership and cached/full agreement (maximum logit error
0.00003815, equal argmax). Native drafts and live Jev judgments are being collected.

A [documented audit revision](../../research/contextual-memory-audit-correction.md)
normalizes the equivalent `cuda:0`/`cuda` device label without rewriting raw evidence
or changing the worker, protocol or any scientific comparison. The final replay
uses the [corrected audit entrypoint](../../research/diagnostics/audit_contextual_completion_v2.py).

The single worker costs $1.0064/hour, has an independent expiry at 17:40:10 UTC,
and has separate internal/service timeouts. The stage reserves at most $16 under
the owner's cumulative $175 cap. The prior conservative closed estimate is $122.90;
these are not invoices and tax/network remain unconfirmed. Incremental backups run
about every minute and cloud health checks at least every 15 minutes. Completion
requires verified immutable backup, owned-resource deletion and full independent
audit before publishing quality results or selecting the next paid stage.
