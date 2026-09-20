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
| Explicit step/final frames, exact-token search, deduplication, bounded resampling and backtracking | [implementation](docs/reasoning-controller.md), [controller tests](tests/test_reasoning.py), [scorer tests](tests/test_reasoning_scorer.py) |
| Reasoning CLI and final-only Jev control; baseline operation without credentials | [CLI tests](tests/test_reasoning_cli.py), [reasoning config](configs/granite-4.0-1b-reasoning.toml) |
| 16-run framed reasoning mechanism check: five verified backtracks, but no completed step-guided answers | [live report and all outcomes](reports/2026-09-20-reasoning-controller/README.md) |
| Opt-in worked proposal examples, fixed rule oracle, and a completion planner that excludes all prior attempts | [protocol](docs/proposal-generation-experiment.md), [prompt tests](tests/test_reasoning_prompts.py), [oracle tests](tests/test_proposal_probe.py), [completion tests](tests/test_proposal_completion.py) |
| 32 development batches and 48 separate evaluation attempts: step Jev 6/12 verdict matches, equal to greedy/likelihood; all UNKNOWN worlds unsolved | [full report, raw traces, and independent grades](reports/2026-09-20-proposal-generation/README.md) |
| Fixed final choices and direct-Jev control; separate generated-token/decision provenance, reserved budgets, and validated uncertainty/error outcomes | [implementation](src/jev_guided_decoding/verdict.py), [controller tests](tests/test_fixed_verdict.py), [client tests](tests/test_verdict_scorer.py), [CLI tests](tests/test_fixed_verdict_cli.py) |
| 18-run fixed-choice check: 6/6 verdict matches for both fixed mode and direct Jev, versus 2/6 existing step guidance; both UNKNOWN cases classified | [dated report and all evidence](reports/2026-09-20-fixed-verdict/README.md) |
| Intermediate-reasoning investigation: 16 fixed-candidate scorer calls and four generated-derivation runs | [follow-up report](reports/2026-09-20-reasoning-investigation/README.md), [proposed engine design](docs/reasoning-step-investigation.md) |

The recorded smoke run used original Granite with zero trainable parameters.
Guided decoding averaged 3.71 seconds versus 1.10 seconds greedy, with no
established quality gain. One correct ending was rejected and misleading causal
wording was accepted elsewhere. These are historical small-sample findings,
not freshly rerun checks or a general accuracy estimate.

## Not implemented or not demonstrated

- vLLM extension, retained-prefix cache reuse between chunks, or concurrent serving.
- Guaranteed semantic candidate diversity; deduplication currently uses exact token IDs.
- Neural fusion, training, changed model weights, or a new Hugging Face checkpoint.
- Improved held-out answer quality, general mathematical reasoning, or GPU-server speedups.
- Validated compatibility beyond the recorded Granite and tiny-model checks.

Update this inventory when verified behavior changes, naming the PR/report and
keeping branch, merged, experimental, and released states distinct. Guidance-only
work is tracked in [the adaptation record](docs/ai-guidance-import.md).
