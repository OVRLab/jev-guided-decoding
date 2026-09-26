import hashlib
import io
import json
import runpy
import tarfile
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1] / "research/iterations/musr_transfer"


def fixture(tmp_path):
    def dump(name, value):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))

    raw, selected = {}, {}
    for condition in (
        "contextual-scalar",
        "embedding-scalar",
        "contextual-constant",
        "embedding-constant",
    ):
        for seed in (3101, 3102):
            name = f"{condition}-{seed}-epoch2.safetensors"
            raw[name] = name.encode()
            selected[f"{condition}/{seed}"] = dict(
                file=name,
                sha256=hashlib.sha256(raw[name]).hexdigest(),
                epoch=2,
                scores=[0.1, 0.2],
                memory=condition.split("-")[0],
                feedback=condition.split("-")[1],
            )
    raw["selection.json"] = json.dumps(dict(models=selected)).encode()
    archives = {}
    for archive, names in (
        ("recorded-run.tar.gz", ["selection.json"]),
        ("adapters.tar.gz", list(raw)[:-1]),
    ):
        path = tmp_path / "artifacts" / archive
        path.parent.mkdir(exist_ok=True)
        with tarfile.open(path, "w:gz") as t:
            for name in names:
                info = tarfile.TarInfo(name)
                info.size = len(raw[name])
                t.addfile(info, io.BytesIO(raw[name]))
        archives[archive] = hashlib.sha256(path.read_bytes()).hexdigest()
    dump(
        "analysis.json",
        dict(
            passed=True,
            outputs=11840,
            requests=832,
            training_steps=12288,
            optimizer_updates=1536,
            test_cases=256,
        ),
    )
    dump(
        "cost-and-cleanup.json",
        dict(
            cumulative_cap_usd=175,
            cumulative_conservative_usd=130,
            instance_terminated=True,
            owned_disk_deleted=True,
            owned_security_group_deleted=True,
            owned_subnet_deleted=True,
        ),
    )
    dump(
        "provenance.json",
        dict(
            public_archives=archives,
            original_backup_inventory={n: hashlib.sha256(v).hexdigest() for n, v in raw.items()},
        ),
    )
    return selected


def test_checkpoint_lineage_requires_complete_cleanup_and_exact_development_epoch(tmp_path):
    c = runpy.run_path(str(HERE / "contract.py"))
    selected = fixture(tmp_path)
    bundle = c["upstream"](tmp_path)
    assert bundle["selection"] == selected and len(bundle["checkpoint_bytes"]) == 8
    assert bundle["lineage"]["prior_conservative_usd"] == 130
    cost = tmp_path / "cost-and-cleanup.json"
    original = cost.read_text()
    changed = json.loads(original)
    changed["owned_disk_deleted"] = False
    cost.write_text(json.dumps(changed))
    with pytest.raises(ValueError, match="cleanup"):
        c["upstream"](tmp_path)
    cost.write_text(original)
    with (tmp_path / "artifacts/adapters.tar.gz").open("ab") as f:
        f.write(b"changed")
    with pytest.raises(ValueError, match="archive"):
        c["upstream"](tmp_path)


def test_admission_budget_and_input_inventory_fail_closed(tmp_path):
    c = runpy.run_path(str(HERE / "contract.py"))
    assert c["budget_ok"](dict(prior_conservative_usd=169.5, cumulative_cap_usd=175)) is None
    for value in (169.51, float("nan"), -1, True):
        with pytest.raises(ValueError, match="budget"):
            c["budget_ok"](dict(prior_conservative_usd=value, cumulative_cap_usd=175))
    folder = tmp_path / "input"
    folder.mkdir()
    (folder / "case.json").write_text("{}")
    initial = c["inventory"](folder)
    assert initial == {"case.json": hashlib.sha256(b"{}").hexdigest()}
    (folder / "link").symlink_to(tmp_path / "outside")
    with pytest.raises(ValueError, match="symlink"):
        c["inventory"](folder)


def test_freeze_carries_upstream_notices_and_rejects_changed_notice_bytes(tmp_path, monkeypatch):
    c = runpy.run_path(str(HERE / "contract.py"))
    report = tmp_path / "upstream"
    report.mkdir()
    fixture(report)
    prior = c["upstream"](report)
    dataset = tmp_path / "dataset"
    dataset.mkdir()
    (dataset / "source.csv").write_text("fixture")
    notice = tmp_path / "notice.md"
    notice.write_text("Upstream fixture attribution")
    data = dict(
        cases=[],
        references={},
        groups={},
        admission={},
        sources={"source.csv": hashlib.sha256(b"fixture").hexdigest()},
    )
    ns = c["prepare"].__globals__
    monkeypatch.setitem(ns, "upstream", lambda: prior)
    monkeypatch.setitem(ns, "expected_data", lambda folder: data)
    monkeypatch.setitem(ns, "sources", lambda: {"fixture": "bound"})
    monkeypatch.setitem(ns, "NOTICES", {"NOTICE.md": notice})
    monkeypatch.setattr(
        ns["subprocess"],
        "check_output",
        lambda args, **kwargs: "a" * 40 if "rev-parse" in args else "",
    )
    frozen = tmp_path / "frozen"
    c["prepare"](frozen, dataset)
    copy = frozen / "licenses/NOTICE.md"
    assert copy.read_bytes() == notice.read_bytes()
    copy.write_text("changed attribution")
    manifest = json.loads((frozen / "manifest.json").read_text())
    manifest["files"] = c["inventory"](frozen)
    (frozen / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="notice|license"):
        c["verify"](frozen)
