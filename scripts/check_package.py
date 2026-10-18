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
    icons = [claude.get("icon")] + [codex.get("interface", {}).get(key) for key in ("composerIcon", "logo", "logoDark")]
    for icon in filter(None, icons):
        path = (ROOT / icon).resolve()
        if not icon.startswith("./") or not path.is_relative_to(ROOT) or not path.is_file():
            errors.append(f"Manifest icon is missing or outside the package: {icon}")
    svgs = sorted((ROOT / "assets").glob("*.svg")) + sorted((ROOT / "skills").glob("*/assets/*.svg"))
    for path in svgs:
        svg = path.read_text().lower().replace('xmlns="http://www.w3.org/2000/svg"', "")
        if re.search(r"<script|foreignobject|href|url\(|@import|javascript:|https?:|\son[a-z]+\s*=|/home/|/users/", svg):
            errors.append(f"{path.relative_to(ROOT)}: SVG contains active, linked or local-path content")
    if (ROOT / "skills/validate-plan/assets/favicon.svg").read_bytes() != (ROOT / "assets/plan-validation.svg").read_bytes():
        errors.append("Report favicon and assets/plan-validation.svg differ")
    for name in ("validate-plan", "validation-args", "revise-prompt"):
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
    files = [ROOT / name for name in ("README.md", "CONTRIBUTING.md", "SECURITY.md", "CHANGELOG.md", "AGENTS.md", "CLAUDE.md")]
    for directory in ("skills", "docs", "examples", ".github"):
        files.extend((ROOT / directory).rglob("*.md"))
    # Site pages get the leak check only; the link resolver does not understand site links.
    site_pages = [path for pattern in ("*.md", "*.mdx") for path in (ROOT / "site/src/content").rglob(pattern)]
    for path in files + site_pages:
        content = path.read_text()
        if re.search(r"/(?:home|Users)/[^/\s]+/|plan-document-reviewer-prompt", content):
            errors.append(f"{path.relative_to(ROOT)}: private or obsolete instruction leaked")
        if path in site_pages:
            continue
        # Only real Markdown links, not the illustrative paths inside fenced code.
        prose = re.sub(r"```[^\n]*\n.*?```", "", content, flags=re.S)
        for target in re.findall(r"\]\(([^)]+)\)", prose):
            parsed = urlsplit(target.strip("<>"))
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            resolved = (path.parent / unquote(parsed.path)).resolve()
            if not resolved.is_relative_to(ROOT) or not resolved.exists():
                errors.append(f"{path.relative_to(ROOT)}: broken local link {target}")
    for directory in ("assets", "skills", "scripts", "docs", "examples", ".github", ".claude-plugin", ".codex-plugin"):
        for path in (ROOT / directory).rglob("*"):
            if path.is_symlink():
                errors.append(f"Unexpected symlink in release: {path.relative_to(ROOT)}")
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"Package {claude['version']}: manifests, three skills, {len(svgs)} SVG icons and {len(files) + len(site_pages)} Markdown files checked.")


if __name__ == "__main__":
    main()
