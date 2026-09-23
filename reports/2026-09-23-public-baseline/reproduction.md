# Reproduce R23

## Offline reconstruction of the recorded run

Restore the public compressed artifacts to a new ignored directory, checking
both compressed and original byte hashes:

```bash
python3 - <<'PY'
import gzip, hashlib, json
from pathlib import Path
report = Path("reports/2026-09-23-public-baseline")
target = Path("results/r23-restored")
target.mkdir(parents=True, exist_ok=False)
hashes = json.loads((report / "artifact-hashes.json").read_text())
for name, expected in hashes.items():
    assert Path(name).name == name
    packed = (report / "artifacts" / (name + ".gz")).read_bytes()
    assert hashlib.sha256(packed).hexdigest() == expected["gzip_sha256"]
    raw = gzip.decompress(packed)
    assert hashlib.sha256(raw).hexdigest() == expected["raw_sha256"]
    (target / name).write_bytes(raw)
print(f"Verified {len(hashes)} files")
PY
```

Use `results/r23-restored` as `--output` in the analysis/audit commands below.
These commands download only evaluator/tokenizer files, perform no generation
and make no Jev calls. After primary analysis, reconstruct the explicitly post-hoc
choice readout:

```bash
uv run --no-sync python research/diagnostics/public_baseline_readout.py \
  --freeze research/protocols/public-baseline-v1 \
  --output results/r23-restored \
  --primary results/r23-analysis.json --save results/r23-secondary.json
```

Compare primary analysis exactly; for the audit/secondary readout, compare every
field except the newly generated `at` timestamp. Keep restored input files intact.

## Environment and a separate inference rerun

From the repository root, install the main pinned environment without changing
historical lockfiles:

```bash
uv sync --locked --extra dev --extra transformers
uv run --no-sync pytest -q tests/test_benchmark_baseline.py
```

The public protocol already contains frozen normalized cases and separate
references. Regeneration needs pyarrow 21.0.0 and downloads exact source revisions;
use a new directory and compare case/reference hashes. Do not overwrite an old
manifest or reinterpret its source hashes as a new run.

For a separately budgeted CUDA rerun:

```bash
uv run --no-sync python research/iterations/benchmark_baseline/run.py \
  --freeze research/protocols/public-baseline-v1 \
  --output results/r23-new-run
```

This downloads both public model snapshots. It needs no HF/Jev credentials and
makes no Jev requests. The output directory must not already exist. The cloud
operator must separately enforce allocation expiry and deletion; the runner's
three-hour wall limit is not a billing cleanup mechanism.

Use an isolated evaluation environment so upstream dependencies do not modify
the research inference lock. The checked-in requirements file records exact
versions and the IFBench source revision used in this run:

```bash
uv venv results/r23-eval-env --python 3.12.13
uv pip install --python results/r23-eval-env/bin/python \
  -r reports/2026-09-23-public-baseline/evaluator-requirements.txt
```

Retrieve `evaluation_lib.py` from the pinned upstream source (Apache 2.0, retain
its notices); its SHA256 is recorded in `analysis.json`:

```bash
curl --fail --proto '=https' --tlsv1.2 \
  https://raw.githubusercontent.com/allenai/IFBench/1c40f0c10d9b5c5c2f10a175a28007ebb64f7f4d/evaluation_lib.py \
  -o results/r23-evaluation-lib.py
results/r23-eval-env/bin/python research/iterations/benchmark_baseline/analyze.py \
  --freeze research/protocols/public-baseline-v1 \
  --output results/r23-new-run \
  --ifbench-evaluator results/r23-evaluation-lib.py \
  --save results/r23-analysis.json
uv run --no-sync python research/iterations/benchmark_baseline/audit.py \
  --freeze research/protocols/public-baseline-v1 \
  --output results/r23-new-run --save results/r23-audit.json
```

Audit downloads tokenizer/config files only, not model weights, and performs no
inference. Source freeze verification requires the recorded scientific source
files; report-only changes outside that set are harmless. Analysis records the
hashes of its input artifacts and evaluator.
