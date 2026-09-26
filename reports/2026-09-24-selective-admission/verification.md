# R26-A verification and review

## Executed evidence

- Frozen worker source `66d1f01`, data `4e1316c`, attribution/worker checkout
  `39a5f7e`; all recorded bindings remain unchanged. The clean freeze and data,
  pinned model revisions and adapter hashes are in the protocol manifest.
- All 297 generated records and 186 model jobs completed.
  Independent code reconstructs exact chat input/output token IDs, EOS/limits,
  selected gates, prefix ownership, numerical cache checks, batch ordering/work,
  physical requests, provider receipts, conservative charges and weight digests.
- 21 remote result files matched local SHA-256 hashes
  before deletion; all 19 public inference files matched
  after fresh gzip extraction and reproduced the analysis exactly without paid
  generation or API requests. All owned resources were verified absent.
- Nebius CLI authentication expired after verified backup and before the first
  stop request could execute. The existing login was renewed without expanding
  access, cleanup retried, and compute/disk/network absence verified. The VM
  expiry remained independent of CLI authentication; no workload was rerun.
- Actual credential strings and private machine paths were checked without printing
  secrets before raw inference artifacts were published. Source licenses and data
  notices remain attached; the software license does not relicense them.
- Primary format admission failed, as recorded. The v2 readout correction is
  separate and prospective; it did not change the frozen run or its primary audit.

## Local checks

- Before freeze: 572 tests passed; remote worker bootstrap also passed the offline
  suite before paid model dispatch. Expected missing-behavior failures are archived.
- After audit and readout regressions: `uv run --no-sync pytest -q` passed all
  **584 tests in 10.48 seconds**, with no skipped tests in the recorded local log.
- `uv run --no-sync ruff check .`, `uv run --no-sync ruff format --check .`,
  `uv run --no-sync python scripts/check_ai_docs.py`, and `uv build` passed at
  `684bb76`. Later report-only edits do not require another paid experiment.
- Final documentation validation, public-link checks and diff hygiene are recorded
  in `execution/final-doc-checks.log`.

## CI and review context

At source/auditor checkpoint `684bb76`, all Python 3.11/3.12 checks passed in
[push CI](https://github.com/OVRLab/jev-guided-decoding/actions/runs/35963647840)
and [PR CI](https://github.com/OVRLab/jev-guided-decoding/actions/runs/35963652677).
Final report-commit CI is checked after push and reported in the PR.

The full PR scope/diff was inspected against actual base `feat/initial-controller`
(`4c43f489d7bbdcb2bbd464edcaba7505539d1e08`), with bulk research artifacts verified
through hashes and independent replay. The R26 increment leaves the earlier R25
frozen sources, checkpoints, raw records and analyses unchanged. Review included
resource ownership, budget caps, source/reference separation, exact token lineage,
API timeout/charge accounting, parser ambiguity and result-claim consistency.

No human review or inline thread was present in the retrieved context. The
[automated reviewer quota is exhausted](https://github.com/OVRLab/jev-guided-decoding/pull/2#issuecomment-5749510900);
this is unavailable review, not approval. Scientific peer review and independent
replication have not occurred. No merge, package release or Hugging Face model
release is part of this pilot.
