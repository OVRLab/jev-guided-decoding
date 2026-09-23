"""Reconstruct R21 identities, token provenance, receipt scores and spending offline."""

import argparse
import hashlib
import json
import re
import runpy
from pathlib import Path

from jev_guided_decoding.jev import _probability
from jev_guided_decoding.local_claims import LocalClaimScorer

ROOT = Path(__file__).resolve().parents[2]
S = runpy.run_path(str(ROOT / "research/iterations/semantic_feedback/study.py"))
LABELS = ("constructed_supported", "constructed_unsupported", "granite_draft")


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def receipt_check(row):
    r = row["jev"]
    raw = r["raw_response"]
    require(raw["model"] == r["model"] == "jev-1.13.0", "Receipt model mismatch")
    require(r["attempts"] == 1, "Receipt attempt mismatch")
    for key in ("input_tokens", "output_tokens"):
        require(type(raw["usage"][key]) is int and raw["usage"][key] >= 0, "Invalid usage")
        require(raw["usage"][key] == r[key], "Receipt usage mismatch")
    require(sorted(row["question_order"]) == sorted(LABELS), "Question mapping mismatch")
    scores, complete = {}, {}
    for i, label in enumerate(row["question_order"]):
        scores[label] = _probability(raw["answers"], f"support_{i}")
        complete[label] = _probability(raw["answers"], f"assessable_{i}")
    require(row["scores"] == [scores[k] for k in LABELS], "Receipt score mismatch")
    require(row["completeness"] == [complete[k] for k in LABELS], "Completeness mismatch")
    return r["input_tokens"], r["output_tokens"]


def independent_entity(text, names):
    for name in names:
        if re.fullmatch(r"\s*" + re.escape(name) + r"\.*\s*", text, re.I):
            return name
    return None


def index_rows(path, key):
    values = S["J"]["rows"](path)
    require(len({v[key] for v in values}) == len(values), "Duplicate artifact row")
    return {v[key]: v for v in values}


def audit(freeze, output, tokenizer):
    m = S["verify"](freeze)
    require(json.loads((output / "freeze.json").read_text()) == m, "Run manifest mismatch")
    cases = {c["id"]: c for c in json.loads((freeze / "cases.json").read_text())}
    rows = index_rows(output / "outputs.jsonl", "id")
    drafts = index_rows(output / "drafts.jsonl", "id")
    requests = index_rows(output / "requests.jsonl", "id")
    starts = index_rows(output / "starts.jsonl", "job")
    require(
        set(cases) == set(rows) == set(drafts) == set(requests) == set(starts),
        "Incomplete coverage",
    )
    hw = json.loads((output / "hardware.json").read_text())
    done = json.loads((output / "completion.json").read_text())
    require(
        done["unchanged_weights"]
        and hw["original_weights_sha256"] == done["before_sha256"] == done["after_sha256"],
        "Weight provenance mismatch",
    )
    provider_input, provider_output, tokens = 0, 0, 0
    scorer = LocalClaimScorer("offline-payload-reconstruction")
    for ident, c in cases.items():
        r, draft, req = rows[ident], drafts[ident], requests[ident]
        require(r["status"] == "complete" and r["job"] == ident, "Incomplete result")
        require(starts[ident]["metadata"] == {"id": ident, "motif": c["motif"]}, "Start identity")
        expected_messages = S["D"]["messages"](c)
        require(r["messages"] == expected_messages, "Prompt reference leak/mismatch")
        encoded = tokenizer.apply_chat_template(
            expected_messages, tokenize=True, add_generation_prompt=True
        )
        require(
            encoded == r["prompt_token_ids"] == draft["prompt_token_ids"], "Prompt token mismatch"
        )
        require(r["draft_token_ids"] == draft["draft_token_ids"], "Draft token mismatch")
        require(0 < len(r["draft_token_ids"]) <= m["max_new_tokens"], "Token ceiling")
        require(
            all(type(t) is int and 0 <= t < len(tokenizer) for t in r["draft_token_ids"]),
            "Invalid token",
        )
        text = tokenizer.decode(r["draft_token_ids"], skip_special_tokens=True)
        require(text == r["draft"] == draft["draft"], "Granite text provenance mismatch")
        token_ids, stop = S["trim_ids"](r["draft_token_ids"], set(hw["eos_ids"]))
        require(token_ids == r["draft_token_ids"] and stop == r["stop"], "Stop provenance mismatch")
        owner = None
        for event in c["events"]:
            if event["parcel"] == c["parcel"]:
                if event["kind"] == "assign":
                    owner = event["courier"]
                elif event["kind"] == "deny":
                    require(owner != event["courier"], "Contradictory rendered world")
        require(owner == c["owner"] and owner != c["wrong_owner"], "Constructed truth mismatch")
        entity = independent_entity(text, c["people"])
        oracle = {"entity": entity, "supported": entity == owner} if entity else None
        require(oracle == r["draft_oracle"] == draft["draft_oracle"], "Draft oracle mismatch")
        request, candidates, order = S["feedback_inputs"](c, text)
        payload = scorer._build_payload(request, "", candidates)
        require(
            payload == r["payload"] == req["payload"] and order == r["question_order"],
            "Scorer input mismatch",
        )
        require(
            req["payload_sha256"]
            == hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest(),
            "Request digest mismatch",
        )
        # Drafts can themselves mention a color; evidence may never contain badge facts.
        require(payload["state"] == {"evidence": c["assignments"]}, "Evidence allowlist mismatch")
        inp, out = receipt_check(r)
        provider_input += inp
        provider_output += out
        tokens += len(r["draft_token_ids"])
    ledger = S["J"]["rows"](output / "jev-budget.jsonl")
    reserves = [e for e in ledger if e["event"] == "reserve"]
    settlements = [e for e in ledger if e["event"] == "settle"]
    require(len(ledger) == 1 + len(reserves) + len(settlements), "Unknown or extra budget event")
    require(len(reserves) == len(settlements) == len(cases), "Receipt/ledger coverage")
    require(
        len({r["id"] for r in reserves}) == len(reserves)
        and {r["id"] for r in reserves} == {r["id"] for r in settlements},
        "Ledger reservation binding",
    )
    require(
        sum(r["input_tokens"] for r in settlements) == provider_input == done["input_tokens"],
        "Ledger input total",
    )
    require(
        done["successful_calls"] == len(cases) and done["unknown_calls"] == 0, "Completion calls"
    )
    expected = S["A"]["analyze"](list(rows.values()), planned=m["cases"])
    require(
        expected == json.loads((output / "analysis.json").read_text()), "Analysis reconstruction"
    )
    return dict(
        passed=True,
        cases=len(cases),
        draft_tokens=tokens,
        provider_requests=len(cases),
        provider_input_tokens=provider_input,
        provider_output_tokens=provider_output,
        unchanged_weights=True,
        source_files=len(m["sources"]),
        constructed_claims=len(cases) * 2,
        admitted=expected["admitted"],
        mean_generation_seconds=sum(r["generation_seconds"] for r in rows.values()) / len(rows),
        mean_jev_seconds=sum(r["jev"]["seconds"] for r in rows.values()) / len(rows),
        output_files={p.name: S["sha"](p) for p in sorted(output.iterdir()) if p.is_file()},
    )


def main():
    from transformers import AutoTokenizer

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--freeze", type=Path, required=True)
    p.add_argument("--results", type=Path, required=True)
    a = p.parse_args()
    tok = AutoTokenizer.from_pretrained(S["MODEL"], revision=S["REVISION"], local_files_only=True)
    print(json.dumps(audit(a.freeze, a.results, tok), indent=2))


if __name__ == "__main__":
    main()
