# R19 verification record

Before implementation, six capability tests failed because the new modules did not
exist; after implementing the scorer, policy and runtime they all passed. A fresh
split-isolation test then failed because data preparation was not implemented;
it passed after implementation. Finally the map/token/gate/cache audit regression
failed because the new analyzer did not exist; it passed after implementation.
Original test-first logs are retained locally; these failures demonstrate absent
capabilities, not a historical defect in R18.

Current focused check: nine tests pass, including receipt failure/max charging,
no retry, cancellation drainage, native/cache preservation, attention-map scope,
reference exclusion, fit feature validation and audit rejection of tampering.
GPU admission, live hosted integration and held-out evaluation remain pending.

## Pre-inference server correction

The first GPU-host environment check passed 443 tests and failed one historical
R14 overload-recovery test: its real 60-second wall clock expired on the slower
CPU host. No R19 admission, model download or hosted API request had begun. The
failure log is retained. That test now uses a module-scoped deterministic clock;
an additional regression confirms the production deadline still rejects the exact
limit. Asyncio and model-runtime clocks, scientific source hashes, experiment
limits, prompts, datasets, policies and graders are unchanged. This is a test
portability correction, not a quality-driven protocol amendment.
