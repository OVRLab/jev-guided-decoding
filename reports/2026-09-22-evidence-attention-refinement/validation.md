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

## Final verification

Full raw-result audit, figure review, artifact checksums, resource deletion,
canonical checks and final CI status are recorded here after completion.
