# R26-A readout integration defect and prospective v2 fix

Recorded 2026-09-24 after inspecting the exposed development outputs, while the
unchanged R26-A timing run continued. This amendment is **post-hoc to R26-A** and
prospective only for a later, separately frozen evaluation. No fresh case is run
or regraded here; the R26-A primary parser and its failed admission stay intact.

The R26 parser accepts explicit final letters and exact option text on the last
line, but omitted the existing R23 reader's labeled full-option form. For example,
`C. a nucleus` followed by an empty `Final:` wrapper states a choice that this
parser rejects. The [diagnostic](../reports/2026-09-24-selective-admission/native-format-diagnostic.json)
finds 19 such additional recognizable answers among 40 eligible original drafts.
That does not show all 19 are correct. Even with those recognized, seven answers
remain outside these simple forms, so this correction alone does not establish
38/40 admission or readiness for full benchmarking.

The separate [v2 module](evaluation/choice_readout_v2.py) integrates the existing
full-option reader using only the target option list. It preserves explicit final
answers, rejects multiple stated alternatives, wrong option text, malformed
references and nonempty conflicting/invalid final decisions. Public demonstrations
may reuse A/B/C labels; they are not used as the target option list. Reference
truth is compared only after extraction and cannot choose the extracted answer.
Three [regression tests](../tests/test_choice_readout_v2.py) failed before the module
existed, then passed. This module is not installed into the frozen worker or audit.

Before fresh benchmark generation, use each task's declared official-compatible
prompt and extractor, test the expected output forms on exposed development data,
and freeze any deliberate compatibility differences. In particular, full MMLU-Pro
uses its five-shot protocol rather than treating the R26 zero-shot pilot as a full
evaluation. Instruction-following constraints require their independent evaluator;
they must not inherit a permissive multiple-choice fallback. No larger-model
superiority or architectural improvement follows from repairing a parser.
