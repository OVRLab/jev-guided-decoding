# Preserved full-precision interruption

The worker passed numerical admission and generated 113 natural training drafts.
112 Jev receipts succeeded; request 113 failed without a valid usage receipt.
Its 65,536-token reservation remains charged conservatively. No optimizer update,
checkpoint selection or held-out generation occurred. All owned resources were
verified deleted after a hash-verified final backup.

`raw-records.json.gz` is a JSON mapping of relative filenames to their exact UTF-8
contents; `hashes.json` binds every entry. It includes the final 20 worker files
plus one **stale intermediate backup of budget.lock**: the stopped worker had
removed that lease, but append-only rsync retained an earlier local copy. This
file is not evidence of an active process and is never copied into a new active
budget lease. It remains explicitly frozen as predecessor snapshot metadata.
The continuation preserves scientific JSONL prefixes and never replays the failed
request. Dataset/source attribution follows the R25 protocol notices.
