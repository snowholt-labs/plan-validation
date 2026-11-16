"""Check the generated directory edition against the plugin directory's policy.

Each rule ID encodes one rule of the directory's refusal text, as restated in
the directory edition design (Constraints):

- allowed-type: "only allowed file types (judged by content, not name)".
  Markdown, text, JSON, YAML, the extensionless LICENSE, and PNG, JPEG, GIF,
  WebP or ICO images that start with their format's magic bytes.
- shebang: "no file starting with `#!`".
- text-encoding: "UTF-8 with no NUL bytes", for every file except an allowed
  image.
- package-config: "no package manager configuration and no `package.json`".
- claude-folder: "no `.claude/skills` folder" (any `.claude/` folder).
- plugin-folder: "`.claude-plugin/` holds only `plugin.json` and the icon
  image", and only at the root.
- manifest-fields, frontmatter-fields, unread-config, codex-metadata: "only
  manifest and frontmatter fields that Claude Code reads".

Repository additions, not in the refusal text:

- path-characters: path segments use only letters, digits, `.`, `_` and `-`.
- dropped-reference: no file names the renderer or its files.
- dropped-field: no skill file names a field, run file or option of the full
  edition's report data.
- symlink: no symbolic links.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EDITION = "directory-edition"

TEXT_SUFFIXES = {".md", ".txt", ".json", ".yaml", ".yml"}
EXTENSIONLESS = {"LICENSE"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico"}

PACKAGE_CONFIG = {
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "pnpm-workspace.yaml",
    "yarn.lock",
    ".npmrc",
    ".yarnrc",
    ".yarnrc.yml",
    "bun.lockb",
    "pyproject.toml",
    "requirements.txt",
    "Pipfile",
    "poetry.lock",
    "uv.lock",
}
UNREAD_FILES = {"hooks.json", ".mcp.json", ".lsp.json", "monitors.json"}
UNREAD_TOP_FOLDERS = {"commands", "agents", "output-styles", "hooks"}
PLUGIN_FOLDER_FILES = {"plugin.json", "icon.png"}

MANIFEST_KEYS = {"name", "version", "description", "author", "homepage", "repository", "license", "keywords", "icon"}
AUTHOR_KEYS = {"name", "email", "url"}
FRONTMATTER_KEYS = {"name", "description", "disable-model-invocation"}
SHIPPED_ICON = "./.claude-plugin/icon.png"

SAFE_SEGMENT = re.compile(r"[A-Za-z0-9._-]+")
DROPPED_REFERENCES = ("render_report", "context.json", "report.html", "html-report.md")
DROPPED_FIELD = re.compile(
    r"open_decisions|watch_list|review_status|handoff_status|task_inventory|waits_for|security_review"
    r"|security_reason|docs_only|holds_back|decisions_without_reply|format_version|validation_run"
    r"|phase_handoffs|title_accent|published_at|html_sha256|rerun\.txt|kind: (new|saved)|--open|user_config"
    r"|artifact\.json|publish_artifact|handoff_held|--context\b|--report\b|--output\b"
)
FRONTMATTER_LINE = re.compile(r"([A-Za-z0-9_-]+):(?:\s(.*))?")


def is_image(suffix: str, data: bytes) -> bool:
    if suffix == ".png":
        return data.startswith(b"\x89PNG\r\n\x1a\n")
    if suffix in (".jpg", ".jpeg"):
        return data.startswith(b"\xff\xd8\xff")
    if suffix == ".gif":
        return data.startswith((b"GIF87a", b"GIF89a"))
    if suffix == ".webp":
        return data.startswith(b"RIFF") and data[8:12] == b"WEBP"
    if suffix == ".ico":
        return data.startswith(b"\x00\x00\x01\x00")
    return False


def frontmatter(text: str, unquote: bool = True):
    """Return {key: [values]} for the `key: value` lines between the first two `---` lines, or None.

    Unparsed lines are collected under the empty key; indented lines are skipped, so a value
    must fit on its key's line. With unquote, one pair of surrounding quotes is removed.
    """
    lines = text.split("\n")
    if not lines or lines[0].rstrip("\r") != "---":
        return None
    fields = {}
    for line in lines[1:]:
        line = line.rstrip("\r")
        if line == "---":
            return fields
        if not line.strip() or line[0] in " \t":
            continue
        match = FRONTMATTER_LINE.fullmatch(line)
        key = match.group(1) if match else ""
        value = (match.group(2) or "").strip() if match else ""
        if unquote and len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        fields.setdefault(key, []).append(value)
    return None


def check_manifest(text: str, errors: list, rel: str):
    try:
        manifest = json.loads(text)
    except ValueError as exc:
        errors.append(f"manifest-fields: {rel}: cannot be read as JSON ({exc.__class__.__name__})")
        return
    if not isinstance(manifest, dict):
        errors.append(f"manifest-fields: {rel}: must be a JSON object")
        return
    extra = sorted(set(manifest) - MANIFEST_KEYS)
    if extra:
        errors.append(f"manifest-fields: {rel}: keys not allowed: {', '.join(extra)}")
    if not isinstance(manifest.get("name"), str) or not manifest["name"].strip():
        errors.append(f"manifest-fields: {rel}: name is required")
    if "icon" in manifest and manifest["icon"] != SHIPPED_ICON:
        errors.append(f"manifest-fields: {rel}: icon must be {SHIPPED_ICON}, the only icon the edition ships")
    if "author" in manifest:
        author = manifest["author"]
        if not isinstance(author, dict):
            errors.append(f"manifest-fields: {rel}: author must be an object")
        elif set(author) - AUTHOR_KEYS:
            keys = ", ".join(sorted(set(author) - AUTHOR_KEYS))
            errors.append(f"manifest-fields: {rel}: author keys not allowed: {keys}")


def check_skill(rel_parts: tuple, text: str, errors: list, rel: str):
    fields = frontmatter(text)
    if fields is None:
        errors.append(f"frontmatter-fields: {rel}: must start with frontmatter between two --- lines")
        return
    problems = []
    extra = sorted(set(fields) - FRONTMATTER_KEYS)
    if extra:
        problems.append("keys not allowed: " + ", ".join(k or "<unparsed line>" for k in extra))
    repeated = sorted(k for k, values in fields.items() if k and len(values) > 1)
    if repeated:
        problems.append("repeated keys: " + ", ".join(repeated))
    value = {k: values[-1] for k, values in fields.items()}
    if value.get("name") != rel_parts[1]:
        problems.append(f"name must be {rel_parts[1]}")
    if not value.get("description"):
        problems.append("description is required")
    elif frontmatter(text, unquote=False)["description"][-1][0] in ">|":
        # Unquoted, `>` or `|` starts a block scalar (or is invalid YAML); quote such a value.
        problems.append("description must be on its key's line, not a block scalar")
    if rel_parts[1] == "validate-plan" and value.get("disable-model-invocation") != "true":
        problems.append("validate-plan needs disable-model-invocation: true")
    if problems:
        errors.append(f"frontmatter-fields: {rel}: {'; '.join(problems)}")


def check_file(root: Path, path: Path, errors: list):
    rel_path = path.relative_to(root)
    rel = rel_path.as_posix()
    parts = rel_path.parts
    name = path.name
    if not path.is_file():
        errors.append(f"allowed-type: {rel}: not a regular file")
        return
    data = path.read_bytes()
    suffix = path.suffix.lower()

    image = suffix in IMAGE_SUFFIXES and is_image(suffix, data)
    if not (suffix in TEXT_SUFFIXES or name in EXTENSIONLESS or image):
        if suffix in IMAGE_SUFFIXES:
            errors.append(f"allowed-type: {rel}: content does not match the {suffix} image format")
        else:
            errors.append(f"allowed-type: {rel}: file type not allowed")
    if data.startswith(b"#!"):
        errors.append(f"shebang: {rel}: starts with #!")
    text = None
    if not image:
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            errors.append(f"text-encoding: {rel}: not valid UTF-8")
        else:
            if "\x00" in text:
                errors.append(f"text-encoding: {rel}: contains a NUL byte")
                text = None
    if name in PACKAGE_CONFIG:
        errors.append(f"package-config: {rel}: package manager configuration")
    if name in UNREAD_FILES:
        errors.append(f"unread-config: {rel}: configuration the directory edition does not ship")
    if name == "openai.yaml" and len(parts) >= 2 and parts[-2] == "agents":
        errors.append(f"codex-metadata: {rel}: Codex metadata")
    if len(parts) == 2 and parts[0] == ".claude-plugin" and name not in PLUGIN_FOLDER_FILES:
        errors.append(f"plugin-folder: {rel}: .claude-plugin holds only plugin.json and icon.png")
    if text is None:
        return
    if parts == (".claude-plugin", "plugin.json"):
        check_manifest(text, errors, rel)
    if len(parts) == 3 and parts[0] == "skills" and name == "SKILL.md":
        check_skill(parts, text, errors, rel)
    found = [term for term in DROPPED_REFERENCES if term in text]
    if found:
        errors.append(f"dropped-reference: {rel}: names {', '.join(found)}")
    if parts[0] == "skills":
        fields = sorted({m.group(0) for m in DROPPED_FIELD.finditer(text)})
        if fields:
            errors.append(f"dropped-field: {rel}: names {', '.join(fields)}")


def check_edition(root: Path) -> list[str]:
    """Return sorted `<rule-id>: <path>: <message>` errors for the edition at `root`."""
    root = Path(root)
    errors = []
    for dirpath, dirnames, filenames in os.walk(root, onerror=raise_error, followlinks=False):
        here = Path(dirpath)
        dirnames.sort()
        for entry in sorted(dirnames + filenames):
            path = here / entry
            rel_path = path.relative_to(root)
            rel = rel_path.as_posix()
            if not SAFE_SEGMENT.fullmatch(entry):
                errors.append(f"path-characters: {rel}: use only letters, digits, '.', '_' and '-'")
            if path.is_symlink():
                errors.append(f"symlink: {rel}: symbolic links are not allowed")
                continue
            if entry in dirnames:
                if entry == ".claude":
                    errors.append(f"claude-folder: {rel}: .claude folders are not allowed")
                if entry == ".claude-plugin" and here != root:
                    errors.append(f"plugin-folder: {rel}: .claude-plugin is allowed only at the root")
                if len(rel_path.parts) == 2 and rel_path.parts[0] == ".claude-plugin":
                    errors.append(f"plugin-folder: {rel}: .claude-plugin holds only plugin.json and icon.png")
                if here == root and entry in UNREAD_TOP_FOLDERS:
                    errors.append(f"unread-config: {rel}: folder the directory edition does not ship")
            else:
                check_file(root, path, errors)
    manifest = root / ".claude-plugin/plugin.json"
    if not manifest.is_symlink() and not manifest.is_file():
        errors.append("manifest-fields: .claude-plugin/plugin.json: missing")
    elif manifest.is_file() and not manifest.is_symlink():
        try:
            names_icon = json.loads(manifest.read_text()).get("icon") == SHIPPED_ICON
        except (OSError, ValueError, AttributeError):
            names_icon = False
        if names_icon and not (root / ".claude-plugin/icon.png").is_file():
            errors.append("manifest-fields: .claude-plugin/icon.png: the manifest names it, but it is missing")
    return sorted(errors)


def raise_error(error: OSError):
    raise error


def count_files(root: Path) -> int:
    return sum(len(files) for _, _, files in os.walk(root, onerror=raise_error, followlinks=False))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check the directory edition against the directory policy.")
    parser.add_argument("edition", nargs="?", default=str(ROOT / EDITION), help="edition folder to check")
    args = parser.parse_args(argv)
    root = Path(args.edition)
    if not root.is_dir() or root.is_symlink():
        print(f"Directory edition not found: {root}")
        return 1
    try:
        errors = check_edition(root)
        count = count_files(root)
    except OSError as exc:
        print(f"Directory edition cannot be read: {exc}")
        return 1
    if errors:
        for error in errors:
            print(error)
        return 1
    print(f"Directory edition: {count} files checked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
