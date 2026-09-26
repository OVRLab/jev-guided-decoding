# R15 validation record

## Before inference

The original model/policy/data runner had 343 local passing tests (3.46 s),
including eight new R15 checks. Its first test invocation failed because the new
policy/data modules did not exist; two later runner tests failed for the missing
runner. Other boundary tests passed on their first run and are not described as
reproduced regressions. A pinned-tokenizer preflight encoded all 1,632 contexts
without model forwards; 144–438 tokens and seven distinct allowed label tokens.

The first VM bootstrap failed an existing tiny-model 20-second deadline with
unbounded default CPU threading. Setting OMP_NUM_THREADS=2 and MKL_NUM_THREADS=2,
as used by the real runner, yielded 343 passing remote tests in 4.63 s. Both
bootstrap logs are retained privately; this did not execute a paid benchmark.

## Recovery failures and regression evidence

The 103rd development Jev request timed out without a receipt. The original runner
stopped as specified and retained the reservation. Four recovery tests cover
common failed-block accuracy, successful-only log-probability tie breaking,
transport admission/count limits, conservative charge and refusal to replay.
The first three failed for the absent helper, then passed; the fourth mocked
transport flow passed when added. The complete local suite reached 349 passes.

A detached-Git pull failed during deployment; a prelaunch service could not find
the helper and exited before inference. The prelaunch log/status are retained.
After checkout of the exact committed source, four remote recovery tests passed.
The first recovery then failed on its second zero-check snapshot because the
helper reused a write-once JSON utility. This implementation error was preserved
as its own interrupted segment and documented before selection or test inference.

Two full-development mocked tests reproduced the old helper's FileExistsError and
its rejection of a partially completed block. The separate repaired helper passed
both complete development/selection flows with repeated atomic snapshot updates,
individual-job restoration, and no duplicate provider calls. They passed remotely
in 6.73 s; all 352 local tests passed in 3.81 s before continued inference.

The separate independent auditor's first two tests failed for its absent module,
then passed. Its failure-inclusive grading regression reproduced KeyError on a
failed outcome before the auditor was extended; it subsequently passed. Analysis
changes do not change frozen model/inference code or replay paid operations.

The repaired run completed development and 47 test contexts before HTTP 503.
Two held-out continuation tests failed for the absent helper and then passed,
verifying a completed prior context is skipped, the failed paid context retains
eight failed dependent/four generated independent outcomes, and only a never-started
context gets a new request. The local suite reached 354 passes in 4.60 s.

A subsequent no-new-operations prelaunch falsely rejected a JSON list/Python tuple
comparison in the freeze guard. Exact raw JSONL equality verifies no model/scorer
jobs were added. A new regression reproduced that ValueError, then passed with
JSON normalization; it also rejects a genuinely changed selected-policy hash and
confirms the original freeze bytes remain unchanged. All 355 local tests passed
in 3.92 s, and the three focused remote tests passed in 0.21 s before continuation.

## Final verification

Full raw-result audit, figure review, artifact checksums, resource deletion,
canonical checks and final CI status are recorded here after completion.

The complete independent raw audit passed on its first full-artifact invocation:
2,879 exact encoded inputs, 34,679 model decisions, 1,630 valid receipts, 1,465
zero/native label-token pairs, two failed receipts and 98 failed dependent output
records. It also verifies all original prefixes, selection, per-request budget
settlements and both paired primary intervals. All five loaded segments have the
same model-state digest. No new inference was performed by the analysis.

All 57 published raw artifacts passed byte-exact gzip round-trip checks. The five
scientific figures were visually inspected as PNGs: titles, labels, contrasts,
development-grid selection, shaded challenge region and ablation values are legible;
matching SVG/PDF exports are included (15 files). The independent audit and separate
execution-delta summary agree on actual work, avoiding duplicate counts for copied
prefixes. Figure generation used NumPy 2.5.3 and Matplotlib 3.10.8.

All 69 remote result files matched their local hashes before deletion. The VM,
managed disk, task security rules/group and both task address allocations were
verified absent. Completion was exit 0; cloud cleanup finished at 2026-09-22
00:11:30 UTC, with address-absence checks afterward. The new estimate is $1.90,
cumulative $11.17/$50, including conservative charges for unknown requests.

## Reproduce the offline audit

From the repository root, decompress the published JSONL copies into a fresh
ignored directory (original compressed files stay unchanged):

```bash
uv run --no-sync python - <<'PY'
from pathlib import Path
import gzip
import shutil
source = Path('reports/2026-09-22-evidence-attention-refinement')
target = Path('results/r15-public-audit')
target.mkdir(parents=True, exist_ok=False)
for part in ('artifacts', 'interrupted/transport', 'interrupted/checkpoint',
             'interrupted/service', 'interrupted/freeze-prelaunch'):
    for path in (source / part).iterdir():
        output = target / path.relative_to(source)
        output.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == '.gz':
            output.with_suffix('').write_bytes(gzip.decompress(path.read_bytes()))
        else:
            shutil.copyfile(path, output)
PY
uv run --no-sync python research/analysis/evidence_v2.py \
  --manifest research/protocols/evidence-attention-v2 \
  --results results/r15-public-audit/artifacts \
  --original results/r15-public-audit/interrupted/transport \
  --prior results/r15-public-audit/interrupted/checkpoint \
  --service-prior results/r15-public-audit/interrupted/service \
  --freeze-prior results/r15-public-audit/interrupted/freeze-prelaunch \
  --ledger results/r15-public-audit/artifacts/api-ledger.jsonl \
  --output results/r15-public-audit/reproduced-audit.json
```

The locked inference extras supply the tokenizer/Transformers dependencies; no
provider key or GPU is required for this audit. The pinned tokenizer may be fetched
from Hugging Face if not cached. Live reruns use the frozen original protocol and
runner; the recorded recovery scripts are deliberately bound to the hashes of
these particular interrupted segments and must not overwrite or replay them.

## Review status

The full PR remains research work on its branch. Review threads were inspected;
there were no review threads, and the automated Codex reviewer reported that its
code-review usage quota was exhausted. This is not an approval or scientific review.
No merge, package/model publication, paper submission or human scientific review
is claimed. Final canonical check and CI outcomes are recorded with the final commit.

Final canonical checks passed: guidance checker (49 Markdown files), Ruff lint,
Ruff formatting (209 Python files), **355 tests in 4.09 s**, and wheel/source builds.
The documented public decompression/audit command also passed and reproduced all
counts, selected policy and statistics. Exact credential absence was checked
privately across all candidate public files, including decompressed traces; no
credential value is included in the report or verification output.
