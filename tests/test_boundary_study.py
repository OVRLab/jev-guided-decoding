import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "research/iterations/boundary_attention"


def load(name):
    return runpy.run_path(str(HERE / f"{name}.py"))


def test_fresh_balanced_authored_worlds_and_reference_free_views():
    d = load("data")
    dev, test = d["synthetic"]("development", 108), d["synthetic"]("test", 252)
    assert len(dev) == 108 and len(test) == 504
    assert len({c["world_id"] for c in test}) == 252
    assert sum(c["missing"] for c in test) == 252
    assert {c["family"] for c in test} == {"original", "paraphrase", "dependency"}
    assert not {c["target"] for c in dev} & {c["target"] for c in test}
    assert all(c["id"].startswith("r18/") for c in dev + test)
    assert all(set(d["public_view"](c)) == {"id", "question", "sources", "family"} for c in test)


def test_squad_grading_preserves_raw_metrics_and_requires_explicit_abstention():
    d = load("data")
    no = dict(family="squad2", references=[], missing=True)
    yes = dict(
        family="squad2", references=["The United States", "United States of America"], missing=False
    )
    g = d["grade"](no, "The provided context does not establish an answer.")
    assert g["f1"] == 1 and g["raw_f1"] == 0 and g["abstained"]
    assert d["grade"](no, "")["f1"] == 0
    assert d["grade"](yes, "United States of America")["f1"] == 1
    assert d["grade"](yes, "The context does not state an answer.")["f1"] == 0
    assert not d["grade"](yes, "The United States. The context does not mention a date.")[
        "abstained"
    ]
    paragraph = "Mr. Smith arrived.  He left later!\nWhy?"
    sources = d["sentence_sources"](paragraph)
    assert "".join(s["text"] for s in sources) == paragraph


def test_schedule_has_exact_nine_arms_and_real_gate_first():
    s = load("study")
    cases = [{"id": "one"}, {"id": "two"}]
    jobs = s["schedule"](cases)
    assert len(jobs) == 18 and jobs == s["schedule"](cases)
    for c in cases:
        arms = [j["arm"] for j in jobs if j["case_id"] == c["id"]]
        assert len(set(arms)) == 9 and arms[0] == "boundary_gate"


def test_budget_fit_keeps_harmful_calls_out_and_validates_development_values():
    p = load("policies")
    rows = [
        dict(
            case_id=str(i),
            domain="synthetic" if i < 10 else "hotpot",
            features={k: (i % 10) / 10 for k in p["FEATURES"]},
            native_quality=float(i % 10 < 5),
            guided_quality=float(i % 10 >= 5),
        )
        for i in range(20)
    ]
    chosen = p["fit"](rows)
    assert chosen["call_fraction"] == 0.5 and chosen["quality"] == 1
    harmful = [{**r, "native_quality": 1.0, "guided_quality": 0.0} for r in rows]
    assert p["fit"](harmful)["call_fraction"] == 0
    assert not any(
        p["decision"](p["fit"](harmful)["gate"], r["features"], r["case_id"]) for r in harmful
    )
    with pytest.raises(ValueError):
        p["fit"](rows, ceiling=True)
    with pytest.raises(ValueError):
        p["fit"]([{**rows[0], "native_quality": float("nan")}])


def test_auditor_rejects_forged_features_and_non_generator_token():
    a = load("analyze")
    stats = dict(
        head_source_mass=[[0.25, 0.25], [0.25, 0.25]],
        features=dict(evidence_mass=0.5, source_entropy=1.0, head_disagreement=0.0),
        query_rows_computed=1,
        key_length=4,
    )
    a["check_features"](stats)
    with pytest.raises(ValueError):
        a["check_features"]({**stats, "features": {**stats["features"], "evidence_mass": 0.8}})
    with pytest.raises(ValueError):
        a["check_token"](
            dict(
                token_id=3,
                argmax_id=2,
                top_ids=[2, 1],
                selected_logit=1.0,
                top_logits=[2.0, 1.0],
                probability=0.6,
                entropy=0.5,
            )
        )


def test_feature_audit_tolerates_roundoff_but_rejects_boolean_statistics():
    import math

    a = load("analyze")
    stats = dict(
        head_source_mass=[[0.25, 0.25], [0.25, 0.25]],
        features=dict(
            evidence_mass=0.5, source_entropy=math.nextafter(1.0, 0.0), head_disagreement=0.0
        ),
        query_rows_computed=1,
        key_length=4,
    )
    a["check_features"](stats)
    with pytest.raises(ValueError):
        a["check_features"]({**stats, "features": {**stats["features"], "source_entropy": True}})
