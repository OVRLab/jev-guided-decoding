"""The guidance checker must catch unusable imported instructions offline."""

import runpy
from pathlib import Path

import pytest

CHECKER = Path(__file__).parents[1] / "scripts/check_ai_docs.py"


def fixture_repo(tmp_path):
    for name in (
        "AGENTS.md",
        "CLAUDE.md",
        "GEMINI.md",
        "README.md",
        "Project.md",
        "FEATURE.md",
        "LAUNCH.md",
        "LIVE.md",
        "flows.md",
        "CONTRIBUTING.md",
        "SECURITY.md",
    ):
        (tmp_path / name).write_text(
            "# Guide\n\n[Authority](AGENTS.md)\n"
            "[Workflow](docs/development-workflow.md)\n"
            "[Rules](.claude/rules/)\n"
        )
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/development-workflow.md").write_text("# Workflow\n")
    (tmp_path / ".claude/rules").mkdir(parents=True)
    return tmp_path


def check(root):
    return runpy.run_path(str(CHECKER))["check_repository"](root)


def test_valid_portable_guidance_needs_no_network_or_personal_tools(tmp_path):
    root = fixture_repo(tmp_path)
    assert check(root) == []


def test_missing_agent_link_is_reported_at_its_source(tmp_path):
    root = fixture_repo(tmp_path)
    (root / ".claude/rules/review.md").write_text("[Review](../../agents/missing.md)\n")
    errors = check(root)
    assert any(".claude/rules/review.md:1" in e and "missing.md" in e for e in errors)


def test_missing_entrypoint_is_an_error_instead_of_silent_skip(tmp_path):
    root = fixture_repo(tmp_path)
    (root / "GEMINI.md").unlink()
    assert any("GEMINI.md" in e and "missing" in e for e in check(root))


@pytest.mark.parametrize(
    "command",
    [
        "npm run check:ai-docs",
        'sandbox_mode = "danger-full-access"',
        "python /Users/example/private-tool.py",
    ],
)
def test_nonportable_operating_instructions_are_rejected(tmp_path, command):
    root = fixture_repo(tmp_path)
    (root / ".claude/rules/copied.md").write_text(f"Run `{command}`.\n")
    assert any(".claude/rules/copied.md" in e and "nonportable" in e for e in check(root))


def test_local_links_cannot_escape_the_repository(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    fixture_repo(root)
    (tmp_path / "private.md").write_text("Private material\n")
    (root / ".claude/rules/escape.md").write_text("[Outside](../../../private.md)\n")
    assert any("outside repository" in e for e in check(root))


def test_missing_documented_python_script_is_detected(tmp_path):
    root = fixture_repo(tmp_path)
    (root / "docs/development-workflow.md").write_text(
        "Run `uv run --no-sync python scripts/nonexistent.py`.\n"
    )
    assert any("scripts/nonexistent.py" in e for e in check(root))


def test_historical_reports_are_not_rewritten_or_scanned_as_active_rules(tmp_path):
    root = fixture_repo(tmp_path)
    (root / "reports/archive").mkdir(parents=True)
    (root / "reports/archive/README.md").write_text("An old command: `npm run test`.\n")
    assert check(root) == []
