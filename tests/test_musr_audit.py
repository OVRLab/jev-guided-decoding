import json
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_independent_transfer_records_reject_changed_prefix_feedback_memory_and_usage(tmp_path):
    pytest.importorskip("torch")
    audit = runpy.run_path(str(ROOT / "research/iterations/musr_transfer/audit.py"))["check_run"]
    fixture = runpy.run_path(str(ROOT / "tests/test_musr_pipeline.py"))["exercise"](tmp_path)
    result = audit(**fixture)
    assert result["outputs"] == 36 and result["requests"] == 4
    assert result["input_tokens"] == 1000 and result["memory_extractions"] == 4

    def reject(name, mutation):
        path = fixture["output"] / name
        original = path.read_bytes()
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        mutation(rows)
        path.write_text("".join(json.dumps(row) + "\n" for row in rows))
        try:
            with pytest.raises(ValueError):
                audit(**fixture)
        finally:
            path.write_bytes(original)

    reject("outputs.jsonl", lambda rows: rows.pop())
    reject("outputs.jsonl", lambda rows: rows[0].update(text="ANSWER: 1"))
    reject(
        "outputs.jsonl",
        lambda rows: next(r for r in rows if r["arm"].startswith("live/")).update(
            probabilities=[0.9] * 3
        ),
    )
    reject(
        "outputs.jsonl",
        lambda rows: next(r for r in rows if r["arm"] == "text")["prompt_token_ids"].append(1),
    )
    reject("outputs.jsonl", lambda rows: rows[0].update(processed_tokens=0))
    reject(
        "generation-bindings.jsonl",
        lambda rows: next(r for r in rows if r["arm"].startswith("live/")).update(
            memory_digest="0" * 64
        ),
    )
    reject("memory-records.jsonl", lambda rows: rows[0].update(positions=[0]))
    reject("requests.jsonl", lambda rows: rows[0]["payload"]["state"].update(reference=1))
    reject("responses.jsonl", lambda rows: rows[0].update(input_tokens=1))
    reject("budget.jsonl", lambda rows: rows.append(dict(event="reserve", id="unresolved")))
    assert audit(**fixture) == result

    # A cheap successful response cannot retroactively authorize a request whose
    # maximum reservation exceeded the declared cap before dispatch.
    ledger_path = fixture["output"] / "budget.jsonl"
    ledger = [json.loads(s) for s in ledger_path.read_text().splitlines()]
    ledger[0]["max_usd"] = "0.003"
    ledger_path.write_text("".join(json.dumps(row) + "\n" for row in ledger))
    with pytest.raises(ValueError, match="cap|reservation"):
        audit(**(fixture | dict(manifest=fixture["manifest"] | dict(api_cap_usd=0.003))))
