# Reproduce R24 analysis without API calls

Use the repository's pinned core environment (`uv sync --locked --extra dev`).
The archive is a gzipped JSON object mapping each filename to its exact original
UTF-8 text. Restore to a new ignored directory, validate every SHA256 against
`artifact-hashes.json`:

```bash
python3 - <<'PY'
import gzip, hashlib, json
from pathlib import Path
report = Path("reports/2026-09-23-public-critic")
target = Path("results/r24-restored")
target.mkdir(parents=True, exist_ok=False)
archive = (report / "artifacts/receipts.json.gz").read_bytes()
manifest = json.loads((report / "artifact-hashes.json").read_text())
assert hashlib.sha256(archive).hexdigest() == manifest["archive_sha256"]
files = json.loads(gzip.decompress(archive))
hashes = manifest["original_files"]
for name, text in files.items():
    assert Path(name).name == name
    data = text.encode("utf-8")
    assert hashlib.sha256(data).hexdigest() == hashes[name]
    (target / name).write_bytes(data)
assert set(files) == set(hashes)
print(f"Verified {len(files)} files")
PY
```

Then reconstruct scores:

```bash
uv run --no-sync python research/iterations/public_critic.py analyze \
  --freeze research/protocols/public-critic-v1 \
  --output results/r24-restored --save results/r24-replayed-analysis.json
```

Only `run` performs paid calls and reads the existing private key file. Analysis
needs no key, model download, GPU or provider request. Compare the replayed JSON
to the published `analysis.json`; input artifact hashes must match byte for byte.

The additional receipt audit verifies each reservation, beyond the analyzer's
aggregate ledger check:

```bash
python3 - <<'PY'
import hashlib, json
from pathlib import Path
root = Path("results/r24-restored")
freeze = Path("research/protocols/public-critic-v1")
ledger = [json.loads(x) for x in (root / "budget.jsonl").read_text().splitlines()]
reserved = [x["id"] for x in ledger if x["event"] == "reserve"]
settlements = [x for x in ledger if x["event"] == "settle"]
settled = {x["id"]: x["input_tokens"] for x in settlements}
receipts = [json.loads(p.read_text()) for p in sorted(root.glob("*-response.json"))]
ids = [x["reservation"] for x in receipts]
assert len(ids) == len(set(ids)) == len(reserved) == len(set(reserved)) == 60
assert len(settlements) == len(settled) == 60
assert set(ids) == set(reserved) == set(settled)
assert all(settled[x["reservation"]] == x["input_tokens"] for x in receipts)
done = json.loads((root / "completion.json").read_text())
assert done["calls"] == 60 and done["reserved_unknown_calls"] == 0
assert done["known_input_tokens"] == sum(settled.values()) == 50475
assert done["manifest_sha256"] == hashlib.sha256((freeze / "manifest.json").read_bytes()).hexdigest()
actual = json.loads(Path("results/r24-replayed-analysis.json").read_text())
published = json.loads(Path("reports/2026-09-23-public-critic/analysis.json").read_text())
assert actual == published and done["usd"] == actual["usd"]
print("Exact analysis and all 60 receipt settlements verified; no API calls")
PY
```

The frozen source manifest includes the request builder, independent readout,
budget and client transport. Do not alter them and then call the old manifest a
new run. Negative-path offline tests cover a failed/unknown request retaining its
reservation without retry, no-overwrite behavior, and exhausted budget dispatching
zero requests. API routing/version/usage behavior is also covered by the package's
existing tests. A new live rerun needs a new output directory and explicit budget
accounting; source changes need a new recorded protocol.
