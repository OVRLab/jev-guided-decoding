# R16 validation record

Status: live study in progress; final artifact audit and completion are pending.

## Test-first development and local verification

- Initial capability suite: 13 failures because new modules did not exist; this
  established missing scaffolding, not reproduction of thirteen existing defects.
- Cache integration then exposed the pinned Transformers empty-cache representation
  `(batch, 0)`, which reports a length of one. Explicit zero-sequence attention
  tensors repair initialization; cached/full-prefix tiny-model logits agree.
- Added full dynamic-flow testing verifies relevance refresh after actual generated
  tokens, isolated caches, framing attribution and unrestricted final-token ownership.
- Relative-path FP32 entrypoint regression failed before the path-resolution fix;
  it now passes. This was fixed before FP32 execution or model/scorer study jobs.
- Final implementation suite: **375 local tests passed**, including 20 R16 tests.
  Ruff lint and formatting pass; guidance checker passes; wheel and sdist build.

## Remote setup and admission

One Nebius L40S, eight vCPUs, 32 GiB RAM and 80 GiB SSD. CUDA Torch 2.8.0,
Transformers 4.57.1, Python 3.12.13. Runtime uses one CPU intraop and interop thread.
The first bootstrap on old source hit a 60-second offline-test deadline; explicit
thread counts resolved it. The 374-test implementation suite and subsequent
20-test R16 suite pass on the server. This setup failure is retained in the log.

The first BF16 admission stopped at cache/full difference 0.5 before any Jev call
or benchmark job. The separate diagnostic performed twelve comparisons per
precision: BF16 maximum 0.5458984375, FP32 0.0000591278076171875, identical argmax
in every pair. All frozen cohorts/schedule hashes are identical in the FP32
amendment. FP32 admission passed exact old/new hook and zero identities, plus the
stricter 0.0001 full-vocabulary cache tolerance and equal argmax.

The raw `backend` metadata is inherited from the package adapter. Its temperature,
top-p and `cache_between_chunks` fields describe that adapter's unused `propose()`
path. R16 calls its own greedy `Session` with a retained, isolated per-request cache;
exact argmax decisions and processed token counts are the evidence for actual study
behavior. Those historical metadata fields are preserved, not silently rewritten.

The API credential was transferred privately, byte-verified without logging it,
and checked as mode 0600. Live receipts, not credential-file presence alone, prove
that the hosted scorer operated. No credential belongs in a public artifact.

## Reproduction

Install the pinned environment with `uv sync --locked --extra dev --extra transformers`.
Download the pinned model snapshot using the model/revision in the manifest.
Set up a private Jev credential as described in the project docs. Use a fresh output
folder and the [FP32 runner](../../research/iterations/adaptive_attention_fp32.py):

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 uv run --no-sync python \
  research/iterations/adaptive_attention_fp32.py run \
  --manifest research/protocols/adaptive-attention-fp32 \
  --output results/my-adaptive-attention --device cuda --local-files-only
```

The actual cloud launcher additionally sets `torch.set_num_threads(1)` and
`torch.set_num_interop_threads(1)` before running the entrypoint; its recorded
launcher/revision is included with execution evidence. No cloud account or key
is required for offline tests. Reproducing live inference spends provider/GPU funds.

The independent audit needs no GPU or provider calls:

```bash
uv run --no-sync python research/iterations/adaptive_attention/analyze.py \
  --manifest research/protocols/adaptive-attention-fp32 \
  --results results/my-adaptive-attention \
  --output results/my-adaptive-audit.json
```

It refuses an incomplete schedule. Public gzip artifacts must first be decompressed
into a fresh directory, preserving their basenames. Checksums bind the originals.

Review automation on PR #2 currently reports a review quota limit; there are no
human reviews. Passing CI does not imply scientific or human review approval.
