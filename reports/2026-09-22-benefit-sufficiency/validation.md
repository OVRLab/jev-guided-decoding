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
