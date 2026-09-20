# Verified implementation inventory

Inventory introduced on 2026-09-20 by
[PR #1](https://github.com/OVRLab/jev-guided-decoding/pull/1); its GitHub status
records whether it has merged. Entries describe this checkout: on the work branch
they are changes under review, and on the default branch they are merged features.
No package or model publication is recorded. A merged feature is not automatically
a published release.

| Implemented in this checkout | Evidence |
| --- | --- |
| Generic controller with four selection modes and bounded outcomes | [controller](src/jev_guided_decoding/controller.py), [tests](tests/test_controller.py) |
| Jev client with typed validation and bounded retries | [client](src/jev_guided_decoding/jev.py), [tests](tests/test_jev.py) |
| Frozen Transformers backend and exact-token continuation | [backend](src/jev_guided_decoding/backends/transformers.py), [offline backend tests](tests/test_transformers_backend.py) |
| CLI, lexical benchmark, and pinned Granite configuration | [README](README.md), [config](configs/granite-4.0-1b.toml) |
| 12-case live smoke run plus separate two-sentence demonstration | [dated report and raw traces](reports/2026-09-20-granite-smoke/README.md) |

The recorded smoke run used original Granite with zero trainable parameters.
Guided decoding averaged 3.71 seconds versus 1.10 seconds greedy, with no
established quality gain. One correct ending was rejected and misleading causal
wording was accepted elsewhere. These are historical small-sample findings,
not freshly rerun checks or a general accuracy estimate.

## Not implemented or not demonstrated

- vLLM extension, retained-prefix cache reuse between chunks, or concurrent serving.
- Neural fusion, training, changed model weights, or a new Hugging Face checkpoint.
- Improved held-out answer quality, general mathematical reasoning, or GPU-server speedups.
- Validated compatibility beyond the recorded Granite and tiny-model checks.

Update this inventory when verified behavior changes, naming the PR/report and
keeping branch, merged, experimental, and released states distinct. Guidance-only
work is tracked in [the adaptation record](docs/ai-guidance-import.md).
