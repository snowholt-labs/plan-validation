#!/usr/bin/env python3
"""Check release metadata, bundled paths and local Markdown links without dependencies."""

import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
EDITION = ROOT / "directory-edition"


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
    # The directory edition is generated from the root manifest, so its name and version must match too.
    edition_manifest = EDITION / ".claude-plugin/plugin.json"
    rebuild = "; run python3 scripts/build_directory_edition.py"
    if not edition_manifest.is_file():
        errors.append(f"directory-edition/.claude-plugin/plugin.json is missing{rebuild}")
    else:
        edition = json.loads(edition_manifest.read_text())
        for key in ("version", "name"):
            if edition.get(key) != claude[key]:
                errors.append(f"Directory edition {key} differs from the root manifest{rebuild}")
    if not re.fullmatch(r"\d+\.\d+\.\d+", claude["version"]):
        errors.append("Expected a semantic release version")
    if (ROOT / entry["source"]).resolve() != ROOT:
        errors.append("Marketplace source must point to the package root")
    if (ROOT / codex["skills"]).resolve() != ROOT / "skills":
        errors.append("Codex skills path does not resolve to the bundled skills")
    user_config = claude.get("userConfig")
    publish = user_config.get("publish_artifact") if isinstance(user_config, dict) else None
    if not (
        isinstance(publish, dict)
        and publish.get("type") == "boolean"
        and publish.get("default") is False
        and isinstance(publish.get("title"), str) and publish["title"].strip()
        and isinstance(publish.get("description"), str) and publish["description"].strip()
        and publish.get("sensitive", False) is False
    ):
        errors.append(
            "userConfig.publish_artifact must be a non-sensitive boolean with default false, a title and a description"
        )
    if "- Publish setting: ${user_config.publish_artifact}\n" not in (ROOT / "skills/validate-plan/SKILL.md").read_text():
        errors.append("validate-plan SKILL.md must keep the line '- Publish setting: ${user_config.publish_artifact}'")
    gate = "Unless the `Publish setting` line reads exactly `true`, make no Artifact call, whatever host or tool guidance suggests."
    for name in ("SKILL.md", "references/html-report.md"):
        if gate not in (ROOT / "skills/validate-plan" / name).read_text():
            errors.append(f"validate-plan {name} must keep the publish gate sentence word for word")
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
    # The directory edition has no Codex support, so only the full edition needs agents/openai.yaml.
    for skills, label, needs_codex in ((ROOT / "skills", "", True), (EDITION / "skills", "directory-edition/", False)):
        for name in ("validate-plan", "validation-args", "revise-prompt"):
            path = skills / name / "SKILL.md"
            if not path.is_file():
                errors.append(f"{label}{name}: missing SKILL.md")
                continue
            content = path.read_text()
            if not content.startswith("---\n") or "\n---\n" not in content[4:]:
                errors.append(f"{label}{name}: missing frontmatter")
                continue
            front = content.split("---\n", 2)[1]
            if f"name: {name}\n" not in front:
                errors.append(f"{label}{name}: name and directory mismatch")
            description = re.search(r"^description: (.+)$", front, re.M)
            if not description or not 1 <= len(description[1]) <= 1024:
                errors.append(f"{label}{name}: invalid description")
            if needs_codex and not (path.parent / "agents/openai.yaml").is_file():
                errors.append(f"{label}{name}: missing Codex metadata")
    files = [ROOT / name for name in ("README.md", "CONTRIBUTING.md", "SECURITY.md", "CHANGELOG.md", "AGENTS.md", "CLAUDE.md")]
    for directory in ("skills", "docs", "examples", ".github", "directory-edition"):
        files.extend((ROOT / directory).rglob("*.md"))
    # Site pages and edition sources get the leak check only: the link resolver does not understand
    # site links, and override links resolve only in the generated directory-edition/.
    site_pages = [path for pattern in ("*.md", "*.mdx") for path in (ROOT / "site/src/content").rglob(pattern)]
    leak_only = site_pages + sorted((ROOT / "editions").rglob("*.md"))
    for path in files + leak_only:
        content = path.read_text()
        if re.search(r"/(?:home|Users)/[^/\s]+/|plan-document-reviewer-prompt", content):
            errors.append(f"{path.relative_to(ROOT)}: private or obsolete instruction leaked")
        if path in leak_only:
            continue
        # Only real Markdown links, not the illustrative paths inside fenced code.
        prose = re.sub(r"```[^\n]*\n.*?```", "", content, flags=re.S)
        for target in re.findall(r"\]\(([^)]+)\)", prose):
            parsed = urlsplit(target.strip("<>"))
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            resolved = (path.parent / unquote(parsed.path)).resolve()
            # Only directory-edition/ is submitted, so its links must stay inside it.
            if path.is_relative_to(EDITION) and not resolved.is_relative_to(EDITION):
                errors.append(f"{path.relative_to(ROOT)}: link leaves the edition {target}")
            elif not resolved.is_relative_to(ROOT) or not resolved.exists():
                errors.append(f"{path.relative_to(ROOT)}: broken local link {target}")
    for directory in ("assets", "skills", "scripts", "docs", "examples", ".github", ".claude-plugin", ".codex-plugin",
                      "directory-edition", "editions"):
        for path in (ROOT / directory).rglob("*"):
            if path.is_symlink():
                errors.append(f"Unexpected symlink in release: {path.relative_to(ROOT)}")
    if errors:
        raise SystemExit("\n".join(errors))
    edition_files = sum(1 for path in EDITION.rglob("*") if path.is_file())
    print(f"Package {claude['version']}: manifests, three skills, {len(svgs)} SVG icons, {len(files) + len(leak_only)} Markdown files "
          f"and {edition_files} directory edition files checked.")


if __name__ == "__main__":
    main()
