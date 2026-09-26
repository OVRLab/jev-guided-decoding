# R22 reproduction and validation

Scientific code/data are frozen at `dffb8e4`; the source-only parent is `499577f`.
The manifest stores 27 exact scientific file hashes and all dataset hashes. Its
dirty flag includes new protocol files awaiting the data commit, not a changed
run-time source. Reporting, independent auditing and descriptive-readout code
are subsequent additions and are not represented as part of that initial freeze.

## Offline replay from public archives

Use the repository lockfile with development and Transformers extras. The pinned
Granite tokenizer must be available locally for decoding; no model inference or
Jev credential is needed for these audits. The default core-only installation
does not contain Torch/Transformers.

```bash
uv sync --locked --extra dev --extra transformers
```

Extract and verify each archive from the repository root:

```python
import gzip
import hashlib
import json
from pathlib import Path

report = Path("reports/2026-09-23-learned-feedback")
destination = Path("results/r22-public-replay")
for name, info in json.loads((report / "raw-artifact-hashes.json").read_text()).items():
    blob = (report / name).read_bytes()
    assert hashlib.sha256(blob).hexdigest() == info["archive_sha256"]
    data = gzip.decompress(blob)
    assert hashlib.sha256(data).hexdigest() == info["original_sha256"]
    target = destination / info["original_path"]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
```

```bash
uv run --no-sync python research/diagnostics/learned_feedback_audit.py \
  --freeze research/protocols/learned-feedback-v1 \
  --results results/r22-public-replay/learned-feedback-v1
uv run --no-sync python research/diagnostics/learned_feedback_semantics.py \
  --cases research/protocols/learned-feedback-v1/test.json \
  --answers results/r22-public-replay/learned-feedback-v1/test-answers.jsonl
uv run --no-sync python research/diagnostics/learned_feedback_descriptive.py \
  --cases research/protocols/learned-feedback-v1/test.json \
  --results results/r22-public-replay/learned-feedback-v1
uv run --no-project --with matplotlib==3.10.6 python \
  reports/2026-09-23-learned-feedback/plot.py
```

The public replay contains exactly the 28 byte-verified remote files: 26 study
files and the worker log/exit marker. A rolling local backup also retained two
stale lock files after their remote removal; those were excluded from the public
inventory. The audit's output hashes therefore describe the completed remote
study, not stale operational files. No original result was changed.

All 12 adapter checkpoint archives are included, with original safetensors hashes
in the artifact index and selected hashes in `selection.json`. A checkpoint
requires the matching [bridge implementation](../../research/iterations/learned_feedback/bridge.py),
rank 16, layer 19, scale 0.1, hidden size 2048, the pinned original Granite model,
and the recorded staged prompt/token protocol. It is not a merged model checkpoint
or a supported serving API. Original IBM model terms and TypeSafe service terms
remain separate from this repository's software license.

## Verification and preserved corrections

- Real model: exact zero-adapter parity; maximum nonzero full/cache logit difference
  0.0000248 within 0.0001 absolute/relative tolerance; adapter gradients present,
  original-weight gradients absent; original weight digest unchanged after study.
- Independent artifact audit: source/data/input/receipt/work reconstruction,
  checkpoint hashes, matched initialization/order, 6,144 training forwards,
  768 development and 3,456 test generations, 864 successful receipts, selection
  before test, and exact primary analysis replay all pass.
- The R21 admission and replication separately reconstruct from their public
  archives. R21A's insufficient natural-error exposure remains a failed admission;
  R21B's single unassessed partial name remains unassessed.
- New bridge/runtime/study/audit/readout tests first failed during missing-module
  scaffolding. The runtime then exposed a real empty-cache mismatch; reusing the
  existing zero-length cache repair fixed it before source/data freeze. A negative
  admission test initially failed to reject an unbound artifact; binding all
  R21B audited file hashes fixed it before live training. Relevant logs are in
  [validation](validation/).
- The post-result descriptive helper's first artifact run used two wrong metadata
  field names (`reference`, `elapsed_seconds`); it stopped without inference or
  producing results. Using the actual `answer` and `seconds` schema fixed the
  report-only helper. Frozen study/audit inputs and primary results did not change.
- A secondary registration-time statement was corrected after comparing local
  backup progress with remote timestamps. The grammar was frozen after test draft
  preparation started, before any final test answer. Original and corrected
  records are both retained; see [timing correction](readout-timing-correction.json).
- A copied cleanup supervisor initially watched an older study's exit-marker
  filename. Its local process was restarted with the correct marker while the
  remote worker continued unchanged. Final cleanup was then delayed by CLI login
  expiry. Existing sign-in refresh resolved it; no paid inference was restarted.
- Credentials were sent privately over SSH, permission-restricted and checked for
  equality without exposing their value. No credential or private cloud resource
  identifier belongs in the public archives. Public raw/derived content is scanned
  before push; private provisioning and auth files remain outside tracked content.

Canonical repository validation and CI outcomes are recorded in
[validation/final-checks.md](validation/final-checks.md). The source/wheel build
does not claim to package the research checkpoints or a trained-model release.
