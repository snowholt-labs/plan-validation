#!/usr/bin/env python3
"""Check release metadata, bundled paths and local Markdown links without dependencies."""

import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]


def main():
    errors = []
    claude = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
    codex = json.loads((ROOT / ".codex-plugin/plugin.json").read_text())
    market = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
    entry = market["plugins"][0]
    if len({claude["version"], codex["version"], entry["version"]}) != 1:
        errors.append("Plugin and marketplace versions differ")
    if len({claude["name"], codex["name"], entry["name"]}) != 1:
        errors.append("Plugin and marketplace names differ")
    if not re.fullmatch(r"\d+\.\d+\.\d+", claude["version"]):
        errors.append("Expected a semantic release version")
    if (ROOT / entry["source"]).resolve() != ROOT:
        errors.append("Marketplace source must point to the package root")
    if (ROOT / codex["skills"]).resolve() != ROOT / "skills":
        errors.append("Codex skills path does not resolve to the bundled skills")
    for name in ("validate-plan", "validation-args"):
        path = ROOT / "skills" / name / "SKILL.md"
        content = path.read_text()
        if not content.startswith("---\n") or "\n---\n" not in content[4:]:
            errors.append(f"{name}: missing frontmatter")
            continue
        front = content.split("---\n", 2)[1]
        if f"name: {name}\n" not in front:
            errors.append(f"{name}: name and directory mismatch")
        description = re.search(r"^description: (.+)$", front, re.M)
        if not description or not 1 <= len(description[1]) <= 1024:
            errors.append(f"{name}: invalid description")
        if not (path.parent / "agents/openai.yaml").is_file():
            errors.append(f"{name}: missing Codex metadata")
    files = [ROOT / name for name in ("README.md", "CONTRIBUTING.md", "SECURITY.md", "CHANGELOG.md")]
    for directory in ("skills", "docs", "examples", ".github"):
        files.extend((ROOT / directory).rglob("*.md"))
    for path in files:
        content = path.read_text()
        if re.search(r"/(?:home|Users)/[^/\s]+/|plan-document-reviewer-prompt", content):
            errors.append(f"{path.relative_to(ROOT)}: private or obsolete instruction leaked")
        # Only real Markdown links, not the illustrative paths inside fenced code.
        prose = re.sub(r"```[^\n]*\n.*?```", "", content, flags=re.S)
        for target in re.findall(r"\]\(([^)]+)\)", prose):
            parsed = urlsplit(target.strip("<>"))
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            resolved = (path.parent / unquote(parsed.path)).resolve()
            if not resolved.is_relative_to(ROOT) or not resolved.exists():
                errors.append(f"{path.relative_to(ROOT)}: broken local link {target}")
    for directory in ("skills", "scripts", "docs", "examples", ".github", ".claude-plugin", ".codex-plugin"):
        for path in (ROOT / directory).rglob("*"):
            if path.is_symlink():
                errors.append(f"Unexpected symlink in release: {path.relative_to(ROOT)}")
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"Package {claude['version']}: manifests, two skills and {len(files)} Markdown files checked.")


if __name__ == "__main__":
    main()
