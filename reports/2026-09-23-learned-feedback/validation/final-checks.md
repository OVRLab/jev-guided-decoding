# R21/R22 final validation

2026-09-23, with inference extras installed locally:

| Check | Outcome |
| --- | --- |
| `uv run --no-sync pytest -q` | 485 passed; no skips |
| `uv run --no-sync ruff check .` | Pass |
| `uv run --no-sync ruff format --check .` | 380 Python files already formatted |
| `uv run --no-sync python scripts/check_ai_docs.py` | 49 guidance files pass |
| `uv build` | Source distribution and wheel built |
| R21A/R21B public archive reconstruction | Both match original independent audits |
| R22 compressed archive extraction and independent reconstruction | All 28 file hashes match; complete audit JSON identical |
| R22 primary, secondary and descriptive replay | Exact agreement; no model/API calls |
| Frozen scientific source/data check | R22 27 files match; previous R20/R21 manifests unchanged |
| Figure review | PNG visually inspected; SVG/PDF use the same layout |
| Public-content scan | Actual Jev key and private cloud identifiers absent, including decompressed archives |
| Cleanup | Exit 0, verified result retrieval, all owned resources deleted |

The small descriptive helper first lacked a module, then gained pairing tests.
A separate unassessed-draft test first lacked the required classification helper;
the helper now retains `None` as unassessed instead of treating it as false.
Its replay produces exactly the same R22 counts. No frozen scientific module
was changed to implement reporting or satisfy the audit.

The first final lint pass found one unused plotting variable and long lines;
removing it and formatting the plotting file resolved the failures without
changing plotted numbers. The [reproduction log](../reproduction.md) retains
other development, metadata, registration and operational corrections.

The full PR inventory was checked against its actual `feat/initial-controller`
base, with focused review of the added study/runtime/data/audit/test sources and
their reporting changes. The PR preserves the previous cumulative research
history rather than presenting it as one prospective experiment. There are no
submitted reviews or review threads. The automated Codex reviewer reports quota
exhaustion; it was unavailable, not an approval. GitHub CI for the pushed revision
is checked separately before handoff. PR #2 remains unmerged; no model was released.

Public development logs normalize local repository paths and trailing whitespace.
Original private logs remain retained; raw scientific archives are byte-exact.
