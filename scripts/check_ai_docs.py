"""Offline validation of active guidance, adapted from OVRLab's AI-docs check.

Checks local inline Markdown destinations and selected operating instructions;
does not execute examples, contact URLs, or validate Markdown heading anchors.
Historical experiment reports are deliberately outside the active-guidance scope.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT_GUIDES = (
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
)
LINK = re.compile(r'!?\[[^\]\n]+\]\((<[^>]+>|[^\s)]+)(?:\s+"[^"]*")?\)')
SCRIPT = re.compile(r"\bpython3?\s+((?:scripts/|\.github/scripts/)[\w/.-]+\.py)")
NONPORTABLE = re.compile(
    r"\bnpm run\b|\bnpx wrangler\b|\btsc --noEmit\b|/Users/|/home/"
    r"|sandbox_mode\s*=\s*[\"\x27]danger-full-access"
    r"|approval_policy\s*=\s*[\"\x27]never"
    r"|\bUA-\d+\b|apps/(?:auth|sanad-auth|ui)/"
)


def guidance_files(root: Path) -> list[Path]:
    files = set(root.glob("*.md"))
    for directory in (".claude/rules", ".claude/skills", "agents", "docs"):
        files.update((root / directory).rglob("*.md"))
    template = root / ".github/pull_request_template.md"
    if template.exists():
        files.add(template)
    return sorted(files)


def check_repository(root: Path) -> list[str]:
    root = root.resolve()
    errors = [
        f"{name}: required guide is missing" for name in ROOT_GUIDES if not (root / name).is_file()
    ]
    for path in guidance_files(root):
        relative = path.relative_to(root).as_posix()
        if not path.resolve().is_relative_to(root):
            errors.append(f"{relative}: guide resolves outside repository")
            continue
        text = path.read_text(encoding="utf-8")
        # This one document records old -> new mappings; it is not operating guidance.
        provenance = relative == "docs/ai-guidance-import.md"
        fenced = False
        targets = set()
        for line_number, line in enumerate(text.splitlines(), 1):
            location = f"{relative}:{line_number}"
            if not provenance and NONPORTABLE.search(line):
                errors.append(f"{location}: nonportable operating instruction")
            for match in SCRIPT.finditer(line):
                if not (root / match[1]).is_file():
                    errors.append(f"{location}: documented script is missing: {match[1]}")
            if line.lstrip().startswith(("```", "~~~")):
                fenced = not fenced
                continue
            if fenced:
                continue
            for match in LINK.finditer(line):
                href = match[1].strip("<>")
                parts = urlsplit(href)
                if parts.scheme in ("http", "https", "mailto"):
                    continue
                if parts.scheme or parts.netloc:
                    errors.append(f"{location}: unsupported local link: {href}")
                    continue
                if not parts.path:
                    continue
                target = (path.parent / unquote(parts.path)).resolve()
                if not target.is_relative_to(root):
                    errors.append(f"{location}: link resolves outside repository: {href}")
                elif not target.exists():
                    errors.append(f"{location}: links to missing file or directory: {href}")
                else:
                    targets.add(target.relative_to(root).as_posix())
        if relative in ("AGENTS.md", "CLAUDE.md", "GEMINI.md", "README.md"):
            for required in ("AGENTS.md", "docs/development-workflow.md", ".claude/rules"):
                if required != relative and required not in targets:
                    errors.append(f"{relative}: link to {required} for guidance discoverability")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    root = parser.parse_args().root
    errors = check_repository(root)
    if errors:
        print("AI guidance check failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"AI guidance check passed for {len(guidance_files(root))} Markdown files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
