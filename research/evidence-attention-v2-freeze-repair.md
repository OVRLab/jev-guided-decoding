# R15 serialized-freeze comparison repair

Registered 2026-09-22 Amsterdam. The first service-continuation launch exited before
any new model/scorer operation: its safety check compared the JSON arm list to an
equivalent Python tuple and falsely rejected the held-out freeze. All raw JSONL
files are identical to the preceding interrupted segment. Its metadata, completion,
registration and copied raw files are retained as a failed prelaunch artifact.

A separate version of the continuation helper normalizes the proposed record
through JSON before comparing it with the existing JSON record, excluding only
the newly proposed timestamp. It preserves the original freeze bytes and timestamp;
any actual policy/source/data/arm change still raises. A focused regression first
reproduced the false ValueError on list/tuple equivalence, then passed with
normalization while also rejecting a changed selected-policy hash and verifying
that neither call rewrites the old file.

The [service-continuation admission](evidence-attention-v2-service-continuation.md),
selected policy, budget, deadline, failure-inclusive denominators and never-replay
rule are unchanged. This repair adds no model/API work. Freeze its source hash and
both the original service-interrupted files and this no-new-operations prelaunch
before trying the continuation again in a new output directory.
