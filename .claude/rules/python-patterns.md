# Python inference patterns

- Keep the `Backend` and `Scorer` contracts distinct from orchestration and CLI output.
- Pass accepted token IDs forward directly; do not decode and re-tokenize prefixes.
- Store exact full decoded text for evaluation when fragment decoding is not additive.
- Own caches per branch/request, and make sharing/copying semantics explicit.
- Keep blocking model work off the async event loop; await async tasks and own clients.
- Use bounded concurrency if added; cancellation of a thread wait does not instantly
  cancel a GPU kernel or prove that a provider request never ran.
- Apply a returned score only to the same request, prefix, and candidate set.
- Preserve `None` for an unasked judgment rather than inventing a probability.
- Keep deterministic policy and arithmetic in Python, with model judgments as inputs.

Read [architecture guidance](../../agents/architect.md) before changing ownership,
batching, caches, or scheduling; validate the actual device/runtime contract.
