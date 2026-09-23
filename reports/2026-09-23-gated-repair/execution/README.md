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
