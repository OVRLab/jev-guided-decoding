import importlib.util
import json
import re
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "research/iterations/semantic_feedback"
D = runpy.run_path(str(HERE / "data.py"))
A = runpy.run_path(str(HERE / "analyze.py"))


def test_world_truth_is_unique_and_focused_input_excludes_badge_answer():
    cases = D["worlds"](192)
    assert len({c["id"] for c in cases}) == 192
    assert len({c["parcel"] for c in cases}) == 192
    assert len({c["motif"] for c in cases}) == 6
    for c in cases:
        assert D["owner_from_events"](c["events"], c["parcel"]) == c["owner"]
        assert D["assess"](c, c["owner"])["supported"] is True
        assert D["assess"](c, c["wrong_owner"])["supported"] is False
        view = D["feedback_view"](c)
        assert set(view) == {"parcel", "evidence"}
        assert not re.search(r"\b" + c["answer"] + r"\b", json.dumps(view), re.I)
        assert "badge" not in json.dumps(view)


def test_oracle_refuses_to_supply_missing_or_ambiguous_answer():
    c = D["worlds"](6)[0]
    for text in ("", "[E02]", "The responsible courier is", c["owner"] + " or " + c["wrong_owner"]):
        assert D["assess"](c, text) is None
    assert D["assess"](c, "  " + c["owner"].upper() + ".\n")["supported"] is True
    assert D["assess"](c, c["owner"] + " is not responsible.") is None


def test_latest_asserted_assignment_wins_but_rumor_does_not():
    events = [
        {"parcel": "Box", "courier": "Mira", "kind": "assign"},
        {"parcel": "Box", "courier": "Ravi", "kind": "rumor"},
        {"parcel": "Box", "courier": "Ravi", "kind": "deny"},
    ]
    assert D["owner_from_events"](events, "Box") == "Mira"
    assert (
        D["owner_from_events"](
            events + [{"parcel": "Box", "courier": "Ravi", "kind": "assign"}], "Box"
        )
        == "Ravi"
    )


def test_missing_natural_errors_is_inconclusive_not_perfect_feedback_admission():
    c = D["worlds"](6)[0]
    rows = []
    for i in range(6):
        rows.append(
            {
                "id": str(i),
                "motif": D["MOTIFS"][i],
                "status": "complete",
                "draft_oracle": {"supported": True},
                "scores": [0.99, 0.01, 0.99],
            }
        )
    result = A["analyze"](rows, planned=6)
    assert result["constructed"]["balanced_accuracy"] == 1
    assert not result["admitted"]
    assert result["natural"]["unsupported"] == 0
    with pytest.raises(ValueError, match="Duplicate"):
        A["analyze"](rows + [rows[0]], planned=7)
    assert c["owner"]


def test_runner_freeze_binds_sources_data_and_refuses_replay(tmp_path):
    R = runpy.run_path(str(HERE / "study.py"))
    folder = tmp_path / "freeze"
    R["prepare"](folder)
    manifest = R["verify"](folder)
    assert manifest["cases"] == 192
    cases = json.loads((folder / "cases.json").read_text())
    cases[0]["owner"] = "tampered"
    (folder / "cases.json").write_text(json.dumps(cases))
    with pytest.raises(ValueError, match="freeze"):
        R["verify"](folder)
    with pytest.raises(FileExistsError):
        R["prepare"](folder)


def test_live_payload_has_no_badge_facts_or_oracle_labels():
    from jev_guided_decoding.local_claims import LocalClaimScorer

    R = runpy.run_path(str(HERE / "study.py"))
    c = D["worlds"](6)[0]
    request, candidates, order = R["feedback_inputs"](c, c["wrong_owner"])
    scorer = LocalClaimScorer("offline-test-key")
    payload = scorer._build_payload(request, "", candidates)
    encoded = json.dumps(payload)
    assert len(order) == 3 and len(set(order)) == 3
    assert "badge" not in encoded and "constructed_supported" not in encoded
    assert "wrong_owner" not in encoded and "answer" not in payload["state"]
    assert len(payload["questions"]) == 6


@pytest.mark.skipif(importlib.util.find_spec("torch") is None, reason="Optional inference extra")
def test_exact_draft_ids_survive_prompt_construction():
    R = runpy.run_path(str(HERE / "study.py"))
    assert R["trim_ids"]([4, 5, 2, 0, 0], {2}) == ([4, 5, 2], "eos")
    assert R["trim_ids"]([4, 5], {2}) == ([4, 5], "length")
