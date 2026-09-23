# Reproducing R20

The frozen protocol is `research/protocols/semantic-evaluation-v1`, executed from
scientific commit `e1249c8`. The later optional-Torch test declaration and blind
inspection registration do not change any of its 63 scientific source hashes.

## Offline reconstruction after completed artifacts are available

Install the locked development and inference extras. The audit needs the two pinned
tokenizers and saved records, not checkpoint weights or a GPU:

```bash
uv sync --locked --extra dev --extra transformers
uv run --no-sync python - <<'PY'
from transformers import AutoTokenizer
for model, revision in (
    ('ibm-granite/granite-4.0-1b', '6a7381ba1f54d684ff508d991aeb7dc580157103'),
    ('Qwen/Qwen3-14B', '40c069824f4251a91eefaf281ebe4c544efd3e18'),
):
    AutoTokenizer.from_pretrained(model, revision=revision, trust_remote_code=False)
PY

uv run --no-sync python research/diagnostics/unpack_selective_artifacts.py \
  --report reports/2026-09-23-semantic-evaluation \
  --output results/r20-public-replay

uv run --no-sync python research/iterations/semantic_evaluation/analyze.py \
  --manifest research/protocols/semantic-evaluation-v1 \
  --results results/r20-public-replay/semantic-evaluation-v1 \
  --output results/r20-public-replay/analysis.json
```

The unpacker verifies stored/raw SHA-256 hashes and refuses an existing output
folder. The auditor reconstructs judge prompts, exact response token decoding,
strict Boolean parsing, validation thresholds and repeated labels. After admitted
main generation it additionally checks Granite inputs/tokens/maps/cache/work/weights,
receipt and budget provenance, blind packet mapping and the grading freeze. It uses
the already disclosed, narrowly bounded R19 logarithm portability adapter. It does
not rerun either model or make hosted Jev requests.

Compare all analysis fields except the `at` timestamp to the archived independent
analysis. Mechanical agreement is not independent human semantic validation.

The [registered blind inspection](../../research/semantic-evaluation-blind-review.md)
was recorded before original treatment analysis. Its saved labels and packets are
in `blind-review.json`; replay does not constitute a new blind inspection. Once
that record and the audited public artifacts exist, regenerate descriptive tables,
fixed score examples and the explicitly post-hoc citation-only syntax count:

```bash
uv run --no-sync python research/diagnostics/semantic_evaluation_report.py \
  --report reports/2026-09-23-semantic-evaluation \
  --results results/r20-public-replay/semantic-evaluation-v1

uv run --no-project --python 3.12.13 \
  --with matplotlib==3.11.2 --with numpy==2.5.3 --with pillow==12.3.0 \
  python research/diagnostics/render_semantic_evaluation.py \
  --report reports/2026-09-23-semantic-evaluation
```

Those editorial helpers preserve the frozen primary grades. The examples include
evaluator mistakes, and the citation-only count does not estimate every error;
see the [transfer diagnostics](transfer-diagnostics.md). Figures are saved as
PNG, SVG and PDF. These commands overwrite derived presentation files only.

## Fresh inference

Fresh inference requires both model checkpoints, a compatible GPU and hosted Jev
access, and incurs new costs. Never reuse an output path or silently repeat a started
packet after failure. The original cloud workflow runs:

```bash
uv run --no-sync python research/iterations/semantic_evaluation/pipeline.py \
  --manifest research/protocols/semantic-evaluation-v1 \
  --output results/semantic-evaluation-new-run \
  --key-file /path/to/private/jev-key
```

All model downloads must already exist in the cache. The cloud environment pins
Python 3.12.13, Torch 2.8.0 and Transformers 4.57.1; its thread pools are set to one.
The independent judge uses BF16, non-thinking chat framing and greedy generation;
Granite uses FP32 with the unchanged R19 runtime. A new hosted response or device
may produce different outputs. See the prospective plan for budgets and admission.
