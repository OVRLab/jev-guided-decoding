# R13 V2: recovery for never-started jobs

Registered after the original test stopped at job 3,016 (3,015 complete, one
failed; 3,284 never started). The original run remains stopped and immutable.
Its last soft-step request took the client's HTTP 429/529 exhaustion path.
That path discarded the exact status/body and incorrectly reported known usage;
the durable ledger correctly retained its full 65,536-token reservation. The
precise HTTP status cannot be reconstructed. All 19 remote result files were
hash-verified locally before the first VM, managed disk and task network rules
were deleted. Weights before/after match.

The owner's instruction to resolve issues and run the full test, under the same
$50 cumulative budget, authorizes this bounded operational recovery. This does
not change the scientific policy or erase the failed attempt. Before further
calls, carry this second historical unknown at its full maximum charge in a new
copy of the stopped shared ledger, recording the reason and authorization.
Run one newly authored authentication/service diagnostic, not the failed test
request. Preserve its manifest, receipt or failure. A failed diagnostic blocks
the GPU launch pending a separately recorded decision.

## Continuation contract

- Freeze an explicit schedule containing only the 3,284 keys absent from the
  original start log; verify that the original 3,016 starts exactly match the
  initial segment of the frozen randomized arm order. Never replay any started
  job, including the failed job. Retain that failure as incorrect in the original
  6,300-job denominator and report incomplete operational success explicitly.
- Keep original worlds, seeds, order, model revision, prompts, grammar, scoring
  rubric, one-attempt requests, limits, bias, final ownership and statistics.
  Do not use partial accuracy to select jobs or tune any parameter. The transport
  patch only retains redacted 429/529 diagnostics and marks absent receipts unknown;
  it does not change successful requests or their interpretation.
- The continuation has a separate frozen source manifest and output directory.
  Verify unchanged inference modules against V2, allowing only the documented
  transport diagnostics patch and new continuation runner. Record loading and
  hardware again; compare the unchanged weight digest with the original run.
- For at most three new explicit HTTP 429/529 failures, persist the failed job,
  halt dispatch, retain its reservation at the maximum under this recorded
  authorization, then wait at least 60 seconds and at least the parsed Retry-After
  delay before the **next never-started job**. A delay over 300 seconds or more than
  three incidents stops the continuation. No failed request/job is retried.
  Other provider, timeout, model, provenance or backend failures stop immediately.
- Fresh reservations remain exclusive on one shared ledger, with its historical
  $3 Jev cap. Cooldowns and incidents are separate operational records and count
  toward wall time. No zero-charge settlement is invented for an absent receipt.
- Use one new L40S, never concurrent with the deleted first VM, and a four-hour
  shutdown guard. Expected remaining inference is about 80 minutes. The original
  $50 allowance is cumulative; new deployment time does not reset it.

## Completion and interpretation

Merge raw records for analysis only after proving disjoint job keys and matching
frozen inputs. Preserve both source segments and original stopped summaries.
All failed/missing jobs remain incorrect. Recompute the original three clustered
contrasts once on the combined planned denominator; flag the operational protocol
amendment and separate machine/time segments. Timing includes per-job work, while
recovery/setup/cooldown is reported separately. If all remaining jobs run, say all
planned jobs were attempted, not that every job succeeded or all gates passed.

Tests first reproduce lost retryable diagnostics, then verify explicit schedule
exclusions, failure retention, maximum-charge authorization, bounded cooldown and
no retry on ambiguous timeouts. Publish complete permitted evidence, independently
audit prompts/tokens, retrieve/hash-check results and verify resource deletion.

The provider's [HTTP API documentation](https://docs.typesafe.ai/api.md) describes
429 as rate limiting and 529 as temporary overload and advises delayed backoff.
It does not supply this run's lost status or an actual token-usage receipt.
