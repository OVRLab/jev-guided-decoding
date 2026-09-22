"""Independent reconstruction of anonymous grading and unchanged Granite token provenance."""

import argparse
import hashlib
import json
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
S = runpy.run_path(str(HERE / "study.py"))
G = S["G"]
J = S["J"]
D = S["BASE_D"]
ROOT = S["ROOT"]
A = runpy.run_path(str(HERE.parent / "benefit_sufficiency/analyze.py"))
PORT = runpy.run_path(str(ROOT / "research/diagnostics/benefit_sufficiency_audit.py"))
require = A["require"]


def score_summary(values):
    if not values or any(v is not None and type(v) is not bool for v in values):
        raise ValueError("Invalid semantic labels")
    hits = sum(v is True for v in values)
    unknown = sum(v is None for v in values)
    return dict(
        n=len(values),
        correct=hits,
        unresolved=unknown,
        lower=hits / len(values),
        upper=(hits + unknown) / len(values),
    )


def verify_judgments(packets, path, tokenizer):
    rows = J["rows"](path)
    starts = J["rows"](path.with_suffix(".starts.jsonl"))
    lookup = {p["id"]: p for p in packets}
    require(
        len(rows) == len(starts) == len(lookup)
        and {r["id"] for r in rows} == set(lookup)
        and {r["id"] for r in starts} == set(lookup),
        "Missing/duplicate judge records",
    )
    metadata = json.loads(path.with_suffix(".metadata.json").read_text())
    require(
        metadata["model"] == G["MODEL"]
        and metadata["revision"] == G["REVISION"]
        and metadata["enable_thinking"] is False
        and metadata["greedy"] is True
        and metadata["max_new_tokens"] == 128,
        "Judge settings changed",
    )
    require(
        metadata["rubric_sha256"] == hashlib.sha256(G["RUBRIC"].encode()).hexdigest(),
        "Rubric changed",
    )
    for r in rows:
        p = lookup[r["id"]]
        require(
            G["digest"](p["packet"]) == p["packet_digest"] == r["packet_digest"],
            "Judge input binding",
        )
        rendered = tokenizer.apply_chat_template(
            G["messages"](p["packet"]),
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        ids = tokenizer(rendered, add_special_tokens=False)["input_ids"]
        require(
            ids == r["input_ids"]
            and hashlib.sha256(json.dumps(ids).encode()).hexdigest() == r["prompt_ids_sha256"],
            "Judge prompt identity",
        )
        require(0 < len(r["output_ids"]) <= 128, "Judge output budget")
        text = tokenizer.decode(
            r["output_ids"], skip_special_tokens=True, clean_up_tokenization_spaces=False
        )
        require(text == r["raw_text"], "Judge output text")
        try:
            result = G["parse"](text) if len(r["output_ids"]) < 128 else None
        except ValueError:
            result = None
        require(result == r["result"], "Judge grade changed")
    complete = json.loads(path.with_suffix(".complete.json").read_text())
    require(
        complete["outputs_sha256"] == D["sha"](path) and complete["packets"] == len(rows),
        "Judge completion binding",
    )
    return rows


def audit(folder, output):
    from transformers import AutoTokenizer

    m = S["verify"](folder)
    tok = AutoTokenizer.from_pretrained(G["MODEL"], revision=G["REVISION"], local_files_only=True)
    packets = json.loads((folder / "validation-packets.json").read_text())
    rows = verify_judgments(packets, output / "validation.jsonl", tok)
    f = json.loads((folder / "fixtures.json").read_text())
    admission = G["admission"](
        f["validation"],
        [r for r in rows if r["id"].startswith("validation/")],
        [
            {**r, "id": r["id"].removeprefix("repeat/")}
            for r in rows
            if r["id"].startswith("repeat/")
        ],
    )
    recorded = json.loads((output / "judge-admission.json").read_text())
    require(all(recorded[k] == v for k, v in admission.items()), "Judge admission reconstruction")
    require(
        recorded["manifest_sha256"] == D["sha"](folder / "manifest.json")
        and recorded["validation_outputs_sha256"] == D["sha"](output / "validation.jsonl"),
        "Admission binding",
    )
    if not admission["passed"]:
        require(not (output / "generation").exists(), "Generation after failed admission")
        return dict(
            at=J["now"](),
            status="admission_failed",
            admission=admission,
            generations=0,
            provider_attempts=0,
            judge_outputs=len(rows),
        )
    cases = json.loads((folder / "test.json").read_text())
    case_by = {c["id"]: c for c in cases}
    gen = output / "generation"
    out = J["rows"](gen / "outputs.jsonl")
    starts = J["rows"](gen / "starts.jsonl")
    require(json.loads((gen / "freeze.json").read_text()) == m, "Generation freeze changed")
    expected = {f"test/{c['id']}/{a}" for c in cases for a in S["ARMS"]}
    require(
        len(out) == len(starts) == len(expected)
        and {r["job"] for r in out} == expected
        and {r["job"] for r in starts} == expected,
        "Incomplete generation schedule",
    )
    start_by = {r["job"]: r for r in starts}
    gt = AutoTokenizer.from_pretrained(m["model"], revision=m["revision"], local_files_only=True)
    R = runpy.run_path(str(HERE.parent / "benefit_sufficiency/runtime.py"))
    inputs = J["rows"](gen / "inputs.jsonl")
    encoded = {r["id"]: r for r in inputs}
    require(len(encoded) == len(inputs) == len(cases), "Prompt count mismatch")
    for c in cases:
        rebuilt = {"id": c["id"], **R["encode"](gt, D["public_view"](c))}
        require(json.loads(json.dumps(rebuilt)) == encoded[c["id"]], "Saved prompt mismatch")
    receipt_rows = J["rows"](gen / "receipts.jsonl")
    receipts = {r["key"]: r for r in receipt_rows if r["status"] != "started"}
    dispatched = {r["key"]: r for r in receipt_rows if r["status"] == "started"}
    require(
        len(receipt_rows) == 2 * len(receipts) and set(receipts) == set(dispatched),
        "Receipt dispatch count",
    )
    for key, r in receipts.items():
        require(
            key == hashlib.sha256(json.dumps(r["payload"], sort_keys=True).encode()).hexdigest()
            and r["reservation"] == dispatched[key]["reservation"],
            "Receipt identity",
        )
        if r["status"] == "complete":
            raw = r["raw_response"]
            require(
                raw["model"] == r["model"] == m["jev_model"] and r["attempts"] == 1,
                "Provider identity",
            )
            require(raw["usage"]["input_tokens"] == r["input_tokens"], "Receipt usage")
            require(
                [raw["answers"][f"relevance_{i}"]["noul"] for i in range(len(r["scores"]))]
                == r["scores"]
                and raw["answers"]["sufficient"]["noul"] == r["sufficient"],
                "Raw provider judgment",
            )
    checker = PORT["guarded_checker"](A["check_output"], A["P"]["vector"])
    for row in out:
        c = case_by[row["case_id"]]
        gate, canned = S["configuration"](row["arm"])
        require(
            row["policy"] == m["treatment"]
            and row["gate"] == row["requested_gate"] == gate
            and row["instruction_strength"] == 5
            and row["mode"] == "dual",
            "Treatment changed",
        )
        require(
            row["domain"] == D["domain"](c) and row["world_id"] == c["world_id"], "Case binding"
        )
        st = start_by[row["job"]]
        require(
            st["at"] > recorded["at"] and all(row[k] == v for k, v in st["metadata"].items()),
            "Start/admission binding",
        )
        check = {**row, "logical_jev_calls": 1} if canned else row
        checker(check, encoded[c["id"]], D["public_view"](c), gt, m)
        require(row["grade"] == D["grade"](c, row["text"]), "Historical lexical grade changed")
        events = row["forward_events"]
        require(
            len(events) == row["model_forwards"]
            and [e["query_tokens"] for e in events]
            == [len(encoded[c["id"]]["input_ids"])] + [1] * (len(events) - 1),
            "Measured work",
        )
        if canned:
            require(
                row["physical_jev_attempts"] == row["logical_jev_calls"] == 0
                and row["local_callback_count"] == 1
                and row["provider_kind"] == "canned"
                and row["sufficient"] == 0
                and row["raw_scores"] == [0.5] * len(c["sources"]),
                "Canned/provider confusion",
            )
        elif row["arm"] == "native":
            require(
                row["physical_jev_attempts"] == row["logical_jev_calls"] == 0,
                "Native called provider",
            )
        else:
            receipt = receipts[row["receipt_key"]]
            require(
                receipt["payload"]
                == S["S"]["S"]["payload_for"](D["public_view"](c), m["jev_model"]),
                "Reference leakage",
            )
            require(
                row["physical_jev_attempts"] == row["logical_jev_calls"] == 1, "Dual request count"
            )
            if receipt["status"] == "complete":
                require(
                    row["raw_scores"] == receipt["scores"]
                    and row["sufficient"] == receipt["sufficient"],
                    "Applied judgments",
                )
    complete = json.loads((gen / "completion.json").read_text())
    require(
        complete["weights_before"]
        == complete["weights_after"]
        == J["rows"](gen / "loads.jsonl")[0]["weights_before"]
        and complete["outputs"] == len(out)
        and complete["completed_schedule"],
        "Weight/completion mismatch",
    )
    ledger = J["rows"](gen / "ledger.jsonl")
    settled = {r["id"]: r["input_tokens"] for r in ledger if r["event"] == "settle"}
    maximum = {r["id"] for r in ledger if r["event"] == "charge_max_unknown"}
    reserve = [r["id"] for r in ledger if r["event"] == "reserve"]
    require(
        len(reserve) == len(set(reserve)) == len(receipts)
        and set(reserve) == set(settled) | maximum
        and set(settled).isdisjoint(maximum)
        and set(reserve) == {r["reservation"] for r in receipts.values()},
        "Ledger reservations",
    )
    for r in receipts.values():
        require(
            settled.get(r["reservation"]) == r["input_tokens"]
            if r["status"] == "complete"
            else r["reservation"] in maximum,
            "Ledger settlement",
        )
    frozen = json.loads((output / "grading-freeze.json").read_text())
    for key, name in [
        ("packets", "blind-packets.json"),
        ("mapping", "blind-mapping.json"),
        ("judgments", "judgments.jsonl"),
        ("generation", "generation/outputs.jsonl"),
    ]:
        require(frozen[key + "_sha256"] == D["sha"](output / name), "Grade freeze changed")
    packets = json.loads((output / "blind-packets.json").read_text())
    mapping = json.loads((output / "blind-mapping.json").read_text())
    judgments = verify_judgments(packets, output / "judgments.jsonl", tok)
    require(
        frozen["at"] > json.loads((output / "judgments.complete.json").read_text())["completed_at"],
        "Grading freeze order",
    )
    joined = G["join"](packets, mapping, judgments)
    index = {(r["case_id"], r["arm"]): r for r in joined}
    raw_index = {(r["case_id"], r["arm"]): r for r in out}
    require(set(index) == set(raw_index), "Blind mapping coverage")
    for key, row in raw_index.items():
        require(
            index[key]["packet_digest"] == G["digest"](G["packet"](case_by[key[0]], row["text"])),
            "Blind answer mapping changed",
        )
    domains = {}
    for domain in ("synthetic", "hotpot", "squad2"):
        cohort = [c for c in cases if D["domain"](c) == domain]
        values = {
            a: [
                index[c["id"], a]["result"]["correct"] if index[c["id"], a]["result"] else None
                for c in cohort
            ]
            for a in S["ARMS"]
        }
        arms = {a: score_summary(v) for a, v in values.items()}
        for a in S["ARMS"]:
            arms[a]["legacy_mean"] = sum(
                D["quality"](c, raw_index[c["id"], a]["grade"]) for c in cohort
            ) / len(cohort)
            arms[a]["legacy_semantic_disagreements"] = sum(
                (D["quality"](c, raw_index[c["id"], a]["grade"]) == 1) != (v is True)
                for c, v in zip(cohort, values[a], strict=True)
                if v is not None
            )
        comparisons = {
            a: A["bootstrap"](
                cohort,
                [float(v is True) for v in values["dual"]],
                [float(v is True) for v in values[a]],
                m["primary_interval"],
                203092331,
            )
            for a in ("native", "static")
        }
        groups = {}
        for missing in (False, True):
            mask = [i for i, c in enumerate(cohort) if c["missing"] == missing]
            if mask:
                groups[str(missing)] = {
                    a: score_summary([values[a][i] for i in mask]) for a in S["ARMS"]
                }
        sensitivity = {}
        for arm in ("native", "static"):
            sensitivity[arm] = {
                "worst_for_dual": A["bootstrap"](
                    cohort,
                    [float(v is True) for v in values["dual"]],
                    [float(v is not False) for v in values[arm]],
                    m["primary_interval"],
                    203092331,
                ),
                "best_for_dual": A["bootstrap"](
                    cohort,
                    [float(v is not False) for v in values["dual"]],
                    [float(v is True) for v in values[arm]],
                    m["primary_interval"],
                    203092331,
                ),
            }
        domains[domain] = dict(
            arms=arms,
            comparisons=comparisons,
            by_missing=groups,
            unresolved_sensitivity=sensitivity,
        )
    unresolved = sum(r["result"] is None for r in judgments)
    return dict(
        at=J["now"](),
        status="complete",
        admission=admission,
        generations=len(out),
        final_tokens=sum(len(r["final"]["token_ids"]) for r in out),
        weights_unchanged=True,
        provider_attempts=len(receipts),
        provider_failures=len(maximum),
        known_input_tokens=sum(r.get("input_tokens", 0) for r in receipts.values()),
        unique_judge_packets=len(packets),
        unresolved_packets=unresolved,
        quality_claims_admitted=unresolved / len(packets) <= 0.05,
        domains=domains,
        judge_outputs=len(rows) + len(judgments),
        judge_generated_tokens=sum(len(r["output_ids"]) for r in rows + judgments),
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--results", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    result = audit(a.manifest, a.results)
    D["dump"](a.output, result)
    print(json.dumps({k: v for k, v in result.items() if k != "domains"}))


if __name__ == "__main__":
    main()
