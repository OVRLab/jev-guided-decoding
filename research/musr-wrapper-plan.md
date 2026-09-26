# MuSR study-wrapper implementation plan

This unpaid implementation follows the [conditional design](musr-transfer-design-draft.md)
and the completed [native format admission](musr-native-admission-v1.md). It does
not authorize a paid run or select checkpoints before R31 closes.

1. Add a serial unmodified larger-Granite comparator with pinned supported
   thinking/non-thinking settings, exact prompts and tokens, per-case sampling
   seeds, no adapter/provider input, deadlines and exclusive output creation.
   Test the real cache/generation flow on a tiny model before implementation.
2. Add a prospective input/source/checkpoint contract and execution wrapper:
   require complete audited R31 evidence, verified cleanup and sufficient cumulative
   budget; use only development-selected checkpoints from its immutable artifacts.
   Keep reference labels out of generation and verifier inputs. Refuse silent resume.
3. Register a separately bounded exposed-case GPU/Jev/larger-model admission after
   R31 closes; quantify native readability, verified feedback, exact intervention
   bindings and throughput. Preserve errors and charges. Admission scores are not
   fresh public results and must not become a prompt/checkpoint search.
4. Freeze a fresh-case protocol, named comparator profiles, arm matrix, grouped
   uncertainty and resource envelope before any of the 730 untouched questions.
   Count all invalid/unfinished outputs and actual work; stop safely at the cap.

Affected files are the new `musr_transfer` namespace, focused tests, registered
protocols, notebook/register and flow checks. Existing R31 frozen sources stay
unchanged. Key failure cases are wrong model/cache, ambiguous or unfinished readout,
references in input, changed checkpoints, stale source hashes, duplicate output,
unknown provider charges, insufficient budget and deadline expiry. Offline tests
precede implementation; actual-device admission, independent raw replay and resource
deletion precede any public quality claim. No generated text is executed.
