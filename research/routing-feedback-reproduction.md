# Reproducing the R28 attribution study

The [protocol](routing-feedback-plan-v1.md) fixes scientific decisions before
inference. The [public manifest](protocols/routing-feedback-v1/manifest.json)
binds the original source files, data, evaluator, model revision and existing
adapter. Later manuscript/publication helpers do not change that frozen worker.
The [manuscript](manuscript.md) distinguishes historical R27 evidence from R28.

## What is available

- Source, tests, registered protocol and exact hash manifest are public.
- The existing live adapter is in the [R25 archive](../reports/2026-09-23-gated-repair/artifacts/gated-repair-retry-v4/live-2501-epoch2.safetensors.gz),
  SHA-256 after decompression `24a768171705e82018bd0961c77e71202f90606cb043ec850781a1a8679f8591`.
  Original Granite and hosted Jev weights are not redistributed here.
- IFEval inputs and its unchanged evaluator are retrieved directly from the pinned
  [Google Research source](https://github.com/google-research/google-research/tree/e6890f85757dd84e27ca6df2dd30651dafad28e0/instruction_following_eval).
  Respect the upstream [Apache-2.0 license](https://github.com/google-research/google-research/blob/e6890f85757dd84e27ca6df2dd30651dafad28e0/LICENSE).
  The acquisition helper checks every downloaded file against the frozen manifest.
- An inference directory contains prompt-only cases, the selected adapter and
  manifest; a separate grading directory contains constraint metadata and the
  evaluator. Transfer only the inference directory to a worker.
- The [public numerical replay](../reports/2026-09-25-routing-feedback/replay/) contains
  case outcomes and fixed selection maps that support
  offline statistical replay without questions, generated answer text, token IDs,
  API payloads or credentials. This is distinct from reproducing the raw-token
  integrity audit or independently checking the grader against generated text.

## Acquire without paid model calls

Run inside this repository using Python 3.11–3.13 and the lockfile. A fresh
`results/` destination is required; the helper refuses overwrites.

```bash
uv sync --locked --extra dev --extra transformers
uv run --no-sync python research/iterations/routing_feedback/reproduce.py acquire \
  --destination results/r28-reproduction-inputs
```

This downloads public source files and decompresses the already published adapter.
It does not load a model or call Jev. Original input ordering, case/reference
separation, the 539 eligible cases and data/checkpoint hashes must match exactly.
The two excluded checker keys are 1122 and 1129; no cases were excluded based on
model outcomes. Source files listed in the manifest must remain byte-identical.

## Run a new experiment deliberately

This stage needs CUDA, the pinned original Granite weights, a Jev credential and
a separately authorized compute budget. It incurs new charges. The historical
manifest's spending fields document OVRLab's authorization, not permission to
spend on a contributor's account. Preserve it for exact replay; register a separate
execution envelope for another organization or a different resource ceiling.
Do not start the long-running worker merely to inspect the report.

```bash
uv run --no-sync python research/iterations/routing_feedback/run.py \
  --folder results/r28-reproduction-inputs \
  --output results/r28-reproduction-outputs \
  --key-file /absolute/path/to/private/jev-key
```

Keep the key outside the repository and output archive. Original model and Jev
revision IDs are pinned; provider retirement, access changes and hardware kernels
can limit exact repetition. This worker stops on a failed or unresolved Jev attempt
without replaying it, retaining the budget reservation and incomplete records.
Set independent cloud expiry and retrieve outputs before deleting owned resources.

## Admit integrity before quality scoring

The audit uses the inference environment and pinned tokenizer, without inference
or new Jev calls. It checks source/checkpoint/data bindings, full coverage,
selection/donors, exact prefixes/decodes, internal hook positions, native
likelihood records, job/work accounting, base-weight records and API receipts.

```bash
uv run --no-sync python research/iterations/routing_feedback/audit.py \
  --folder results/r28-reproduction-inputs \
  --output results/r28-reproduction-outputs \
  --report results/r28-integrity.json
```

The grader uses a separate local environment so its dependencies need not be
installed on the GPU host. References stay local. The original environment used
Python 3.12.13 and these explicit evaluation versions:

```bash
uv venv --python 3.12 results/r28-grader-venv
uv pip install --python results/r28-grader-venv/bin/python -e . \
  absl-py==2.3.1 langdetect==1.0.9 nltk==3.9.2 immutabledict==4.2.2
results/r28-grader-venv/bin/python -m nltk.downloader \
  -d results/r28-nltk-data punkt punkt_tab
NLTK_DATA="$PWD/results/r28-nltk-data" \
  results/r28-grader-venv/bin/python research/iterations/routing_feedback/grade.py \
  --folder results/r28-reproduction-inputs \
  --grading results/r28-reproduction-inputs-grading \
  --output results/r28-reproduction-outputs \
  --admission results/r28-integrity.json \
  --report results/r28-analysis.json \
  --private results/r28-private-grades.json
```

An existing audit or grade is not overwritten. The grade command verifies the
admitted file hashes and evaluator bindings before scoring. Original raw decoded
responses are supplied to the unchanged checker. Language detection and bootstrap
seeds are fixed. Missing outcomes remain incomplete; they are not quietly omitted.

## Public numerical replay

The public export helper accepts only case ID, arm, strict/loose booleans and
per-instruction booleans; extra fields or text are rejected. The selection file
must match the independently admitted analysis. Export and replay are offline:

```bash
uv run --no-sync python research/iterations/routing_feedback/reproduce.py export \
  --private results/r28-private-grades.json \
  --selection results/r28-reproduction-outputs/selection.json \
  --analysis results/r28-analysis.json \
  --destination results/r28-public-replay
uv run --no-sync python research/iterations/routing_feedback/reproduce.py replay \
  --folder results/r28-public-replay
```

The replay reconstructs policy quality scores and paired intervals from numerical
case outcomes. It does not independently establish response correctness, token
provenance, production latency, or cloud charges. Those require the unchanged
checker with raw outputs, the integrity archive, and provider accounting.

## Verification and remaining editorial work

The initial worker passed 648 repository tests locally and eight new mechanism/
audit regressions on the GPU. Four GitHub CI jobs passed on worker source
`c418df6`. Separate upstream checker tests passed 48/48; 12 constructed
pass/fail/empty checks passed. New reproduction helpers have separate tests and
are not retroactively part of the frozen worker. The combined local suite passes
652 tests; complete reacquisition matches the frozen 539-case dataset and adapter.
A separate synthetic grading/export/replay integration checks all seven policies
and ten contrasts; those artificial fixtures are not study results.

The completed real-data replay matches all seven policy scores and ten paired
contrasts across 1,616 outcomes. All 652 tests pass after finalization. A separately
labeled warning inspection reproduces every original strict/loose boolean; the
[report](../reports/2026-09-25-routing-feedback/README.md) discloses the upstream
loose-language fallback without changing the registered grades.

Before publication, review authorship/contributions, cited related work, licenses,
all claims against the final completed report, and the distinction between the
numerical replay and private raw integrity evidence. The complete earlier record
stays linked; unfinished Qwen and the unrun broad benchmark tasks remain unfinished.
