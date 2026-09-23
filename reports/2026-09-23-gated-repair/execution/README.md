# Execution checks

These are test-first failure logs and preflight/build/server validation logs.
Local home/repository paths are redacted; hashes bind the distributed versions.
They contain no API credentials. Frozen inference source remains at the protocol
revision even when later report-only helpers add local tests. The v3 GPU server
passed all 527 tests before inference; report-only tests bring local total to 529.

The machine uses a ten-hour poweroff timer and a nine-hour systemd worker cap.
The local supervisor backs up the dedicated result directory every 45 seconds,
verifies final remote/local SHA256 digests after the worker stops, and deletes
only the experiment-owned instance, managed disk, address allocations and
security rules/group. Resource deletion remains pending until the final report.

V4 passed all **536 local tests in 10.19 seconds** and all **536 server tests in
16.99 seconds**, with Ruff, source/wheel builds and the guidance checker passing.
The new client/auditor tests initially failed because modules were absent. During
implementation, fixture validation caught missing case metadata, and the delivery
audit caught a string/decimal budget-term mismatch; these were corrected before
freezing or dispatch. Simulated-clock tests exercise real cooldown validation.
The last four GitHub CI jobs at data freeze `6bade56` also pass. External automated
review remains unavailable due to its reported quota; no human review is recorded.

The later read-only source-data audit adds two tests: both failed first because
the module was absent, then all **538 local tests passed in 10.36 seconds**.
Ruff and source/wheel builds pass. The GPU worker remains at its frozen 536-test
revision; no inference was repeated for this reporting-only addition.
