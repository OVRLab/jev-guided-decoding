# Reconstructing R19

The study is still running; the artifact-dependent commands below become usable
after the completed archives and analyses are published. They reconstruct saved
evidence rather than rerun model inference. Use the completed research commit:
the auditors require all frozen scientific source hashes to match.

## Environment and tokenizer

From the repository root, install the locked development and Transformers extras.
The reconstruction needs the pinned tokenizer, not model weights or a GPU. These
setup commands download dependencies/tokenizer files; the subsequent artifact
audits make no Jev requests and use the tokenizer cache offline.

```bash
uv sync --locked --extra dev --extra transformers
uv run --no-sync python - <<'PY'
from transformers import AutoTokenizer
AutoTokenizer.from_pretrained(
    "ibm-granite/granite-4.0-1b",
    revision="6a7381ba1f54d684ff508d991aeb7dc580157103",
    trust_remote_code=False,
)
PY
```

## Lossless archive reconstruction and independent checks

Use a new output directory; the unpacker refuses to overwrite an existing path.
It verifies stored and uncompressed SHA-256 hashes, sizes and safe relative paths.

```bash
uv run --no-sync python research/diagnostics/unpack_selective_artifacts.py \
  --report reports/2026-09-22-benefit-sufficiency \
  --output results/r19-public-replay

uv run --no-sync python research/iterations/benefit_sufficiency/analyze.py \
  --manifest research/protocols/benefit-sufficiency-v1 \
  --results results/r19-public-replay/benefit-sufficiency-v1 \
  --output results/r19-public-replay/main-analysis.json

uv run --no-sync python research/iterations/sufficiency_controls.py audit \
  --manifest research/protocols/sufficiency-controls-v1 \
  --main-manifest research/protocols/benefit-sufficiency-v1 \
  --main-results results/r19-public-replay/benefit-sufficiency-v1 \
  --results results/r19-public-replay/sufficiency-controls-v1 \
  --output results/r19-public-replay/controls-analysis.json

uv run --no-sync python - <<'PY'
import json
from pathlib import Path
report = Path("reports/2026-09-22-benefit-sufficiency")
replay = Path("results/r19-public-replay")
for original, reconstructed in (
    ("independent-analysis.json", "main-analysis.json"),
    ("controls-analysis.json", "controls-analysis.json"),
):
    left = json.loads((report / original).read_text())
    right = json.loads((replay / reconstructed).read_text())
    assert {k: v for k, v in left.items() if k != "at"} == {
        k: v for k, v in right.items() if k != "at"
    }
print("Both analyses reproduce all non-timestamp fields.")
PY
```

The checks reconstruct prompt/token maps, receipt provenance, frozen development
selection, branch decisions, output-token records, work and grades. They verify
the recorded weight hashes and do not rerun GPU forward passes. Agreement is not
an independent semantic annotation of answers.

## Tables, diagnostic examples and figures

The report builder selects examples deterministically by case ID from frozen
metric differences. It does not change grades. These commands overwrite derived
editorial files only; the raw archives and protocol freezes remain unchanged.

```bash
uv run --no-sync python research/diagnostics/benefit_sufficiency_report.py \
  --report reports/2026-09-22-benefit-sufficiency \
  --results results/r19-public-replay/benefit-sufficiency-v1 \
  --manifest research/protocols/benefit-sufficiency-v1

uv run --no-project --python 3.12.13 \
  --with matplotlib==3.11.2 --with numpy==2.5.3 --with pillow==12.3.0 \
  python research/diagnostics/render_benefit_sufficiency.py \
  --report reports/2026-09-22-benefit-sufficiency
```

The renderer produces four figures in PNG, SVG and PDF. The first command uses the
study's locked analysis environment; the figure command uses a separate pinned
environment and does not alter the lockfile or scientific source freeze.

## New inference is a separate operation

Generating fresh answers requires the pinned checkpoint, compatible GPU/runtime
and live provider access, with new costs and potentially different hosted judgments.
The original joint responses are preserved so reproduction does not rely on a
future service returning identical values. The published cloud estimate includes
setup, loading, admission, inference, retrieval and verified deletion; it is not
a model-only latency or provider invoice. Dataset/model/provider licenses remain
separate from this repository's software license.
