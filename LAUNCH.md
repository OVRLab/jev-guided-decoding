# Initial experimental release target

This records the scope already agreed for the initial open-source prototype.
It is a target, not a release announcement; implementation status lives in
[LIVE.md](LIVE.md). Change this scope only when the project owner requests it.

## Required scope

- Generic Python controller with backend/scorer interfaces and Granite as its first test.
- Frozen weights and exact token-prefix continuation, with candidate selection
  before subsequent generation rather than only final-answer judging.
- Jev support/relevance checks and a separate EOS completion decision.
- Explicit retry, time, token, API, rejection, and error outcomes.
- Reproducible comparisons with greedy, sampled, and likelihood-selection controls.
- Public fixtures, full decision traces, cost/timing metadata, and honest failure analysis.
- Portable installation, CLI documentation, offline tests, CI, and development guardrails.

## Release evidence

Required tests/checks pass for the source being released. Examples work in the
documented environment; skipped optional tests and hardware limits are named.
The two-sentence flow demonstrates selection before the next sentence. Reports
identify revisions, seeds, dataset hashes, counts, and limitations. No private data,
credentials, or unsupported quality claims appear in public artifacts.

## Later work, outside this prototype

Broader held-out evaluation precedes performance claims. Retained-prefix caching,
concurrent serving, a vLLM extension, additional tested models, and learned verifier
or model adaptation are separate work with their own acceptance criteria. The
initial smoke results do not establish a quality gain that warrants those claims.
