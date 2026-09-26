# R14 engineering validation and review

Final local checks, 2026-09-21 UTC (handoff after midnight 2026-09-22 Amsterdam):

| Check | Observed outcome |
| --- | --- |
| `uv run --no-sync pytest -q` | 335 passed in 4.10 seconds, with local optional inference dependencies installed |
| `uv run --no-sync ruff check .` | Passed |
| `uv run --no-sync ruff format --check .` | 183 Python files formatted |
| `uv run --no-sync python scripts/check_ai_docs.py` | 49 guidance files passed |
| `uv build` | Wheel and source distribution built |
| Remote pre-execution tests | 329 passed in 125.29 seconds; later analysis tests were added locally |
| Full raw-artifact audit | Passed: 23,136 decisions/bias maps, 1,509 inputs, 756 zero pairs, 732 receipts |
| Public compressed-artifact reproduction | All 16 decompressed files match original SHA-256; full audit passed again on those files |
| Post-hoc metrics reproduction | Per-class outcomes, fixes/regressions, relevance confusion/Brier and API totals reproduced from traces |
| Frozen inference/data/protocol | Hashes match executed manifest; no post-test inference changes |
| Scientific figures | All four inspected; PNG/SVG/PDF plus source/version/hash provenance |

No model inference or paid API call was replayed during report validation. The
independent audit is a separate implementation within the same AI-assisted project;
it is not external scientific replication or peer review. CI's core-only Python
3.11/3.12 environments intentionally skip optional model tests; remote and local
inference-enabled runs provide the separate evidence above.

The active PR is [#2](https://github.com/OVRLab/jev-guided-decoding/pull/2), stacked
against `feat/initial-controller`. Its full file scope includes earlier R04–R13
controllers, studies and authored datasets, retained with their original findings.
The R14 review inspected hook/runtime/scorer/runner, source and label provenance,
causal/GQA mask behavior, score reuse, failure/spending paths, analysis/statistics,
all test results, and report claims. Public trace bytes were checked rather than
manually reading every repeated JSON row. Current review threads and comments
contain no actionable review findings. The Codex automatic reviewer reports a
usage limit; its absence is not approval. No separate human review was obtained.
CI status for the final pushed revision is available on the PR and checked at handoff.

The main reporting correction is to distinguish supported native/shuffled gains
from the unmet all-controls criterion and limited absolute accuracy. The guardrails
now require a constant-label reference/class balance for constrained-answer studies.
Earlier negative studies and the original fixed-choice objective error remain public.

Initial failures and their fixes are recorded in the [main report](README.md):
missing modules/capabilities, valid tiny hybrid-family fixture configuration,
nonzero-mask SDPA numerical tolerance, preserved provider diagnostics, independent
visible-record parsing and the reproducible diagnostic analyzer. A later added
Unicode/repeated-source regression passed immediately; no prior failure is claimed
for that additional boundary coverage. A packaging check flagged trailing whitespace emitted by Matplotlib SVG export;
the renderer now normalizes line endings before hashing the exported SVG. No
new cloud retry or inference bug was found during final review.
