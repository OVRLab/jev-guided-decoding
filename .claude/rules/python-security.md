# Python security details

Follow [SECURITY.md](../../SECURITY.md). Do not use `eval`, `exec`, pickle, unsafe
YAML loading, shell interpolation, or generated Python to interpret untrusted
model/provider output. Use structured subprocess arguments for developer commands.

Keep remote model code disabled by default. Review dependencies and the actual
loader/serialization path when adding models; do not claim a file extension alone
makes arbitrary artifacts safe. Validate output paths according to the caller's
trust boundary and preserve the CLI's no-overwrite behavior.
Use exclusive creation when publishing a new single-run artifact. An existence
check before model loading does not protect against another process creating the
path during inference. Test that race without overwriting the competing result.

Credentials belong in approved environment/key-file inputs, never request state,
repr/debug output, or stored traces. Tests use clearly fake keys. A checksum or
synthetic test credential is not automatically an exposure; inspect context.

Preserve exhausted retryable responses too: status, bounded redacted body and
parsed Retry-After. A missing usage receipt stays unknown even on HTTP 429/529;
never infer a zero charge or replay an ambiguous request during recovery.
