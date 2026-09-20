# Flow and regression catalog

Use [the development workflow](docs/development-workflow.md) and
[test guidance](agents/tdd-guide.md) to choose validation for changed behavior.
Existing test references are evidence of present coverage, not a claim that every
future edge case listed below is already tested.

| Flow | Contract and failure cases | Current evidence / suitable validation |
| --- | --- | --- |
| Contributor setup | Core installation/imports without torch, GPU, key, or private helper; optional extras explicit | [CI](.github/workflows/checks.yml), package build, documented install and CLI help |
| Baseline generation | No Jev credential read or provider call; original model remains frozen | [controller tests](tests/test_controller.py), [backend tests](tests/test_transformers_backend.py), CLI smoke when backend changes |
| Candidate continuation | Exact accepted IDs feed the next step; discarded branches stay isolated; whitespace/Unicode decoding stays faithful | [controller tests](tests/test_controller.py), [backend tests](tests/test_transformers_backend.py), [two-sentence trace](reports/2026-09-20-granite-smoke/continuation/runs.jsonl) |
| Jev evaluation | Relevant evidence supplied explicitly; references withheld; malformed/missing/nonfinite judgments are errors | [client tests](tests/test_jev.py), scoped synthetic live check for changed API/prompts |
| Selection and EOS | Thresholds enforced; empty EOS checks completion; empty initial answer and premature end cannot pass by default | [controller tests](tests/test_controller.py), [EOS regression](tests/test_jev.py) |
| Rejection and budgets | Retry same prefix with bounded work; count discarded/padded work and HTTP attempts; keep partial result/status | [controller tests](tests/test_controller.py), new boundary tests for affected counters |
| Provider failure | Classify 429/529; honor Retry-After; timeout may be billed; no silent unscored fallback | [client tests](tests/test_jev.py), fake transport negative paths |
| Benchmark recording | Unique cases, no reference leakage, fresh output path, exact raw traces and summary; failed/incomplete runs retained | [benchmark tests](tests/test_benchmark.py), inspect CLI output and recompute summaries for changed artifacts |
| Documentation changes | Entrypoints discover rules, links remain local/valid, commands are portable, historical reports untouched | [AI-docs tests](tests/test_ai_docs.py), `uv run --no-sync python scripts/check_ai_docs.py` |

For cancellation or future parallel scheduling, add request ownership, lock/cache
isolation, timeout, and late-result tests before implementation. Do not claim the
single-backend prototype validates concurrent serving. Run real inference only
when the changed behavior needs it and scoped resources/data are available.
