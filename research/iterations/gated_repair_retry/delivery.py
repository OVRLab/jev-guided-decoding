"""Independent case/physical-attempt/receipt/charge reconstruction for R25 v4."""

import math
import runpy
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from jev_guided_decoding.jev import _probability

F = runpy.run_path(str(Path(__file__).with_name("feedback.py")))
C, records = F["C"], F["records"]


def unique(rows, field):
    result = {r[field]: r for r in rows}
    if len(result) != len(rows):
        raise ValueError("Duplicate evidence key")
    return result


def audit(output, cases, native, m):
    def read(name):
        return records(output / name)

    legacy_req = unique(read("api-requests.jsonl"), "id")
    legacy_res = unique(read("api-responses.jsonl"), "id")
    legacy_fail = unique(read("api-failures.jsonl"), "id")
    if (
        len(legacy_req) != m["legacy_cases"]
        or set(legacy_res) & set(legacy_fail)
        or set(legacy_req) != set(legacy_res) | set(legacy_fail)
        or set(legacy_fail) != set(m["legacy_missing_ids"])
    ):
        raise ValueError("Legacy delivery coverage mismatch")
    new_req = unique(read("new-requests.jsonl"), "reservation")
    new_res = unique(read("new-responses.jsonl"), "reservation")
    new_fail = unique(read("new-failures.jsonl"), "reservation")
    completions = unique(read("case-completions.jsonl"), "id")
    feedback = unique(read("feedback-availability.jsonl"), "id")
    if set(new_res) & set(new_fail) or set(new_req) != set(new_res) | set(new_fail):
        raise ValueError("Incomplete new attempts")
    groups = defaultdict(list)
    for req in new_req.values():
        groups[req["id"]].append(req)
    if set(groups) & set(legacy_req) or set(groups) | set(legacy_req) != set(cases):
        raise ValueError("Replayed legacy case or case coverage mismatch")
    if set(completions) != set(groups) or set(feedback) != set(cases):
        raise ValueError("Completion/availability mismatch")
    all_requests = unique([*legacy_req.values(), *new_req.values()], "reservation")
    all_responses = unique([*legacy_res.values(), *new_res.values()], "reservation")
    all_failures = unique([*legacy_fail.values(), *new_fail.values()], "reservation")
    ledger = read("budget.jsonl")
    terms = [r for r in ledger if r["event"] == "terms"]
    reserves = unique([r for r in ledger if r["event"] == "reserve"], "id")
    settled = unique([r for r in ledger if r["event"] == "settle"], "id")
    maximum = unique([r for r in ledger if r["event"] == "charge_max_unknown"], "id")
    if (
        len(terms) != 1
        or Decimal(terms[0]["max_usd"]) != Decimal(str(m["jev_cap"]))
        or Decimal(terms[0]["usd_per_million"]) != Decimal(str(m["usd_per_million"]))
        or terms[0]["request_token_ceiling"] != 65536
        or any(
            r["event"] not in ("terms", "reserve", "settle", "charge_max_unknown") for r in ledger
        )
        or set(reserves) != set(all_requests)
        or set(settled) != set(all_responses)
        or set(maximum) != set(all_failures)
        or set(settled) & set(maximum)
        or len(maximum) > m["max_unknown_attempts"]
    ):
        raise ValueError("Physical attempt budget mismatch")
    charges, pending = {}, set()
    for event in ledger[1:]:
        key = event["id"]
        if event["event"] == "reserve":
            if key in charges:
                raise ValueError("Repeated budget reservation")
            charges[key] = 65536
            pending.add(key)
        else:
            if key not in pending:
                raise ValueError("Budget settlement before reservation or repeated")
            pending.remove(key)
            if event["event"] == "settle":
                value = event["input_tokens"]
                if type(value) is not int or not 0 <= value <= 65536:
                    raise ValueError("Invalid settled usage")
                charges[key] = value
        if Decimal(sum(charges.values())) * Decimal(str(m["usd_per_million"])) / 1000000 > Decimal(
            str(m["jev_cap"])
        ):
            raise ValueError("Historical dispatch exceeded API cap")
    if pending:
        raise ValueError("Unresolved attempt charge")
    for reservation, req in all_requests.items():
        ident = req["id"]
        if ident not in cases or req["payload"] != C["feedback_payload"](
            cases[ident], native[ident]["text"] or "(empty response)"
        ):
            raise ValueError("Request input binding mismatch")
        if reservation in all_responses:
            response = all_responses[reservation]
            if (
                response["id"] != ident
                or response["model"] != m["jev"]
                or response["raw"]["model"] != m["jev"]
                or response["attempts"] != 1
                or response["probability_correct"]
                != _probability(response["raw"]["answers"], "correct")
                or response["raw"]["usage"]
                != {
                    "input_tokens": response["input_tokens"],
                    "output_tokens": response["output_tokens"],
                }
                or settled[reservation]["input_tokens"] != response["input_tokens"]
            ):
                raise ValueError("Receipt or usage mismatch")
        elif (
            all_failures[reservation]["id"] != ident
            or not all_failures[reservation]["usage_unknown"]
        ):
            raise ValueError("Failure reservation mismatch")
    requests, responses, missing = dict(legacy_req), dict(legacy_res), dict(legacy_fail)
    previous_completion = None
    for ident, group in groups.items():
        if previous_completion is not None:
            interval = (
                datetime.fromisoformat(group[0]["at"]) - previous_completion
            ).total_seconds()
            if interval + 0.01 < 2:
                raise ValueError("New case dispatched before pacing interval")
        if not 1 <= len(group) <= m["attempts_per_case"] or [r["attempt"] for r in group] != list(
            range(1, len(group) + 1)
        ):
            raise ValueError("Attempt order or count mismatch")
        for i, req in enumerate(group):
            key = req["reservation"]
            terminal = i == len(group) - 1
            event = all_responses.get(key, all_failures.get(key))
            if event["attempt"] != req["attempt"] or event["at"] < req["at"]:
                raise ValueError("Attempt event binding/order mismatch")
            if key in new_res:
                if not terminal:
                    raise ValueError("Retried successful response")
                continue
            error = new_fail[key]
            info = error["diagnostics"]
            explicit = info.get("status_code") in (429, 503, 529)
            transport = error["message"] == "Jev request failed or timed out; it was not replayed"
            delay = info.get("retry_after_seconds", 0)
            if (
                not error["admitted"]
                or not (explicit or transport)
                or type(delay) not in (int, float)
                or not math.isfinite(delay)
                or not 0 <= delay <= 300
            ):
                raise ValueError("Fatal failure in completed delivery")
            if not terminal:
                expected = max(30 * 2 ** (req["attempt"] - 1), delay)
                if not explicit or not error["retry"] or error["cooldown_seconds"] != expected:
                    raise ValueError("Unsupported replay or backoff")
                elapsed = (
                    datetime.fromisoformat(group[i + 1]["at"]) - datetime.fromisoformat(error["at"])
                ).total_seconds()
                if elapsed + 0.01 < expected:
                    raise ValueError("Retry started before cooldown")
            elif (
                error["retry"]
                or error["cooldown_seconds"] is not None
                or (explicit and req["attempt"] != 4)
            ):
                raise ValueError("Incomplete retry sequence")
        last = group[-1]
        requests[ident] = last
        probability = None
        if last["reservation"] in new_res:
            response = new_res[last["reservation"]]
            responses[ident] = response
            probability = response["probability_correct"]
        else:
            missing[ident] = new_fail[last["reservation"]]
        done = completions[ident]
        if (
            done["attempts"] != len(group)
            or done["actual_probability_correct"] != probability
            or done["missing"] != (probability is None)
        ):
            raise ValueError("Case completion mismatch")
        if done["at"] < event["at"]:
            raise ValueError("Completion predates final attempt")
        previous_completion = datetime.fromisoformat(done["at"])
    if len(missing) > m["max_missing_cases"]:
        raise ValueError("Missing case limit exceeded")
    for ident, row in feedback.items():
        actual = responses[ident]["probability_correct"] if ident in responses else None
        if (
            row["actual_probability_correct"] != actual
            or row["effective_probability_correct"] != (0.5 if actual is None else actual)
            or row["source"] != ("missing_neutral" if actual is None else "jev")
        ):
            raise ValueError("Availability/neutral distinction mismatch")
    known = sum(r["input_tokens"] for r in all_responses.values())
    usd = (known + 65536 * len(maximum)) * m["usd_per_million"] / 1e6
    if usd > m["jev_cap"]:
        raise ValueError("API cap exceeded")
    return dict(
        requests=requests,
        responses=responses,
        missing=missing,
        feedback=feedback,
        physical_attempts=len(all_requests),
        known_input_tokens=known,
        unknown_attempts=len(maximum),
        missing_cases=len(missing),
        usd=usd,
        retries=len(new_req) - len(groups),
        legacy_cases=len(legacy_req),
    )
