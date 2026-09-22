import copy
import json
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    return runpy.run_path(str(ROOT / "research/iterations/semantic_evaluation" / name))


def test_semantic_packets_hide_identity_and_bind_exact_response():
    s = load("judge.py")
    c = dict(
        question="Where?",
        sources=[dict(id="D1", text="The parcel is in Rome.")],
        references=["Rome"],
        missing=False,
        arm="dual",
        sufficient=0.1,
        id="secret",
    )
    p = s["packet"](c, "It is in Rome.")
    assert set(p) == {"question", "evidence", "references", "answerable", "response"}
    assert "secret" not in json.dumps(p) and "dual" not in json.dumps(p)
    for field in ("question", "response", "references", "evidence"):
        other = copy.deepcopy(p)
        other[field] = str(other[field]) + " changed"
        assert s["digest"](p) != s["digest"](other)


def test_strict_judge_parser_never_turns_malformed_output_into_correctness():
    s = load("judge.py")
    assert s["parse"]('{"correct":true,"reason":"Equivalent answer."}')["correct"] is True
    for text in (
        "true",
        "{}",
        '{"correct":"false","reason":"x"}',
        '{"correct":1,"reason":"x"}',
        '{"correct":false,"reason":""}',
        '{"correct":true,"reason":"x","arm":"dual"}',
        '{"correct":true,"correct":false,"reason":"x"}',
    ):
        with pytest.raises(ValueError):
            s["parse"](text)


def test_judge_admission_requires_both_classes_every_category_and_repeats():
    s = load("judge.py")
    f = load("fixtures.py")["fixtures"]()
    rows = [
        dict(id=x["id"], result=dict(correct=x["gold"], reason="gold")) for x in f["validation"]
    ]
    repeats = [
        dict(id=x["id"], result=dict(correct=x["gold"], reason="gold"))
        for x in f["validation"][:12]
    ]
    assert s["admission"](f["validation"], rows, repeats)["passed"]
    bad = copy.deepcopy(rows)
    for row in bad[:6]:
        row["result"]["correct"] = not row["result"]["correct"]
    assert not s["admission"](f["validation"], bad, repeats)["passed"]
    assert not s["admission"](f["validation"], rows[:-1], repeats)["passed"]
    repeats[0]["result"]["correct"] = not repeats[0]["result"]["correct"]
    assert not s["admission"](f["validation"], rows, repeats)["passed"]


def test_fixtures_are_disjoint_balanced_and_references_stay_out_of_candidates():
    f = load("fixtures.py")["fixtures"]()
    assert len(f["development"]) == 24 and len(f["validation"]) == 96
    assert len({x["id"] for xs in f.values() for x in xs}) == 120
    assert sum(x["gold"] for x in f["validation"]) == 48
    assert len({x["category"] for x in f["validation"]}) == 12
    dev = {x["packet"]["question"] for x in f["development"]}
    assert not dev & {x["packet"]["question"] for x in f["validation"]}


def test_blind_deduplication_and_join_reject_missing_or_changed_evidence():
    s = load("judge.py")
    c = dict(
        id="case",
        question="Where?",
        sources=[dict(id="D1", text="In Rome.")],
        references=["Rome"],
        missing=False,
    )
    rows = [
        dict(case_id="case", arm=a, text=t)
        for a, t in [("native", "Rome"), ("dual", "Rome"), ("static", "Milan")]
    ]
    packets, mapping = s["blind"]([c], rows)
    assert len(packets) == 2 and len(mapping) == 3
    labels = [
        dict(id=p["id"], packet_digest=p["packet_digest"], result=dict(correct=True, reason="x"))
        for p in packets
    ]
    assert len(s["join"](packets, mapping, labels)) == 3
    with pytest.raises(ValueError):
        s["join"](packets, mapping, labels[:-1])
    labels[0]["packet_digest"] = "wrong"
    with pytest.raises(ValueError):
        s["join"](packets, mapping, labels)


def test_judge_runner_hashes_prompt_and_preserves_invalid_output():
    s = load("grade.py")
    p = dict(id="opaque", packet_digest="bound", packet={})
    good = s["record"](p, [1, 2], [3], '{"correct":true,"reason":"yes"}', 0.1)
    assert good["result"]["correct"] and good["output_ids"] == [3]
    bad = s["record"](p, [1, 2], [3], "invalid", 0.1)
    assert bad["result"] is None and bad["raw_text"] == "invalid"


def test_generation_configuration_keeps_native_and_static_off_the_provider():
    s = load("study.py")
    assert s["configuration"]("native")[0]["kind"] == "never"
    assert s["configuration"]("static")[1] is True
    assert s["configuration"]("dual")[1] is False
    with pytest.raises(ValueError):
        s["configuration"]("unknown")


def test_semantic_statistics_keep_unresolved_answers_in_bounds():
    s = load("analyze.py")
    stats = s["score_summary"]([True, False, None])
    assert stats["lower"] == 1 / 3 and stats["upper"] == 2 / 3 and stats["unresolved"] == 1
    with pytest.raises(ValueError):
        s["score_summary"]([1])


def test_failed_semantic_admission_prevents_generator_and_provider_work(tmp_path, monkeypatch):
    s = load("pipeline.py")
    fixtures = load("fixtures.py")["fixtures"]()
    folder = tmp_path / "freeze"
    folder.mkdir()
    (folder / "manifest.json").write_text("{}")
    (folder / "fixtures.json").write_text(json.dumps(fixtures))
    s["S"]["verify"] = lambda _: {}
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        path = Path(cmd[cmd.index("--output") + 1])
        rows = [
            dict(id=g["id"], result=dict(correct=not g["gold"], reason="wrong"))
            for g in fixtures["validation"]
        ]
        path.write_text("".join(json.dumps(r) + "\n" for r in rows))

    monkeypatch.setattr(s["subprocess"], "run", fake_run)
    output = tmp_path / "run"
    s["run"](folder, output, tmp_path / "absent-credential")
    assert len(calls) == 1 and calls[0][1].endswith("grade.py")
    assert not (output / "generation").exists()
    assert json.loads((output / "pipeline-completion.json").read_text())["paid_jev_calls"] == 0


def test_native_and_static_full_jobs_never_read_a_live_receipt(tmp_path):
    import asyncio
    from types import SimpleNamespace

    tiny = runpy.run_path(str(ROOT / "tests/test_benefit_sufficiency.py"))["tiny"]
    _, old, encoded, view, policy = tiny()
    s = load("study.py")
    s["S"]["treatment"] = lambda: policy
    runner = object.__new__(s["Runner"])
    runner.base = old.base
    runner.R = runpy.run_path(str(ROOT / "research/iterations/benefit_sufficiency/runtime.py"))
    runner.current = runner.R["Runtime"](old.base, boundary=1)
    runner.encoded = lambda _: encoded
    runner.deadline = lambda: None
    runner.cooldown = 0
    runner.receipts = SimpleNamespace(receipts={})

    async def forbidden(_):
        raise AssertionError("Live provider was touched")

    runner.receipt = forbidden
    case = {**view, "world_id": "w", "reference": "unknown", "missing": False}
    with s["J"]["Journal"](tmp_path / "jobs", {}) as log:
        runner.log = log
        native = asyncio.run(runner.job(case, "native"))
        static = asyncio.run(runner.job(case, "static"))
    assert native["logical_jev_calls"] == static["logical_jev_calls"] == 0
    assert native["physical_jev_attempts"] == static["physical_jev_attempts"] == 0
    assert static["local_callback_count"] == 1 and static["intervention_action"] == "abstention"
    assert native["final"]["token_ids"] and static["final"]["token_ids"]


def test_capped_judge_output_remains_unresolved_even_with_a_parseable_prefix():
    s = load("grade.py")
    r = s["record"](
        dict(id="x", packet_digest="y"), [1], [2] * 128, '{"correct":true,"reason":"x"}', 0.1
    )
    assert r["result"] is None and r["budget_exhausted"]
