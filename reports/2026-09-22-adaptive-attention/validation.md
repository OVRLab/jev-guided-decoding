# R16 validation record

Status: **completed**. All 16,120 main and 3,600 factorial outcomes are retained;
all three artifact audits pass, and temporary cloud resources are verified deleted.

The main audit reconstructs 3,016 inputs, 22,840 outcomes including development,
447,371 complete-output tokens and all 600 native/zero pairs. The single HTTP 529
failure follows 15 recorded intermediate tokens; it remains incorrect, with no
replay. Total recorded main forwards are 447,386. The factorial adds 3,600 complete
one-token forwards and zero paid calls. The injection audit reconciles 3,143,923
main hook calls, verifies selection before testing, and detects no answer menus
in unrestricted phases. All before/after parameter digests match.

These are code-based reconstructions of frozen inputs, traces and metrics, not
independent human replication. They share frozen tokenization/parser components
and were implemented within the same development effort. No blinded human
reasoning assessment or external scientific review has occurred.

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
- Main implementation suite: **375 local tests passed**, including 20 R16 tests.
  Ruff lint and formatting pass; guidance checker passes; wheel and sdist build.
- Four supplementary factorial tests first failed because their modules did not
  exist, then passed after implementation. At that stage the inference environment
  passed 379 tests. CI initially exposed two NumPy-dependent
  statistics tests lacking the optional-dependency skip; this test-only fix does
  not alter the frozen experiment, analysis formulas or runtime dependencies.
- Three supplementary injection-audit tests first failed on missing scaffolding,
  then passed. They detect mismatched exercised-hook counts, answer menus in open
  phases and semantic text inserted as supposedly fixed controller framing.
- Three output-form diagnostic tests first failed on missing scaffolding, then
  passed. They check bare versus natural abstention, mistakes on answerable cases,
  failure denominators, generation limits and binding to the audited output bytes.
- The current full inference suite passes **385 tests** (4.92 seconds locally).
  Core-only CI on Python **3.11 and 3.12** passes **351 tests with 13 optional
  dependency skips** on source `0637d36`. Ruff lint/format and the 49-file guidance
  check pass. Wheel and sdist also build successfully on the completed checkout.
  The later figure renderer is verified by rendering and visual inspection.

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

## Post-completion supervision recovery

The main run recorded all 16,120 test outcomes and the factorial supplement all
3,600 outcomes. After the factorial exited successfully, the operating system
removed its transient service. `systemctl is-active` returned 4 (unit absent),
which the local supervisor rejected because it expected only 0 or 3. This stopped
local postprocessing, not inference. The original error and completion records
were retained; exit code 0, 3,600/3,600 outputs, unchanged weights and an inactive,
absent service were verified before retrieving the final artifacts and continuing
offline audits/cleanup. No model job or API request was replayed. See the
[recovery record](supervisor-recovery.json).

The local example-rendering helper initially used system Python, which lacked the
installed project package. It was rerun in the pinned `uv run --no-sync` environment
without inference; the original rendering error remains in the operational log.
All five scientific figures were visually inspected. An overlapping legend in the
head-strength figure was moved clear of the bars, and the corrected image checked.
The 29 raw public artifacts have verified lossless compression roundtrips and
uncompressed SHA-256 hashes; local private credential checks passed before packaging.

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

The additional hook/contract audit and descriptive output-form analysis also use
saved artifacts, without a GPU or hosted requests:

```bash
uv run --no-sync python research/diagnostics/adaptive_injection_audit.py \
  --manifest research/protocols/adaptive-attention-fp32 \
  --results results/my-adaptive-attention \
  --output results/my-injection-audit.json

uv run --no-sync python research/diagnostics/adaptive_output_diagnostics.py \
  --outputs results/my-adaptive-attention/outputs.jsonl \
  --audit results/my-injection-audit.json \
  --output results/my-output-diagnostics.json
```

Extract the public `factorial/` artifacts into another fresh folder to reconstruct
the registered factor comparison:

```bash
uv run --no-sync python research/diagnostics/adaptive_factorial_analysis.py \
  --manifest research/protocols/adaptive-attention-fp32 \
  --main results/my-adaptive-attention \
  --supplement results/my-adaptive-factorial \
  --output results/my-factorial-audit.json
```

The standalone PNG/SVG/PDF figures can be regenerated from the audited report:

```bash
uv run --no-project --python 3.12.13 \
  --with matplotlib==3.11.2 --with numpy==2.5.3 --with pillow==12.3.0 python \
  research/diagnostics/render_adaptive_attention.py
```

The [figure environment](figure-environment.json) is separate from the locked
inference/statistical environment. All these auditors require the pinned source
and exact raw bytes. Use fresh output
paths; refusal to overwrite existing evidence is intentional. The factorial live
runner requires the recorded selected policy and completed main artifacts, and
uses only saved Jev receipts. It is not a generic continuation of a retuned study.

Review automation on PR #2 currently reports a review quota limit; there are no
human reviews. Passing CI does not imply scientific or human review approval.
