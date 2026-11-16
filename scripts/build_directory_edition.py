"""Generate the directory edition of the plugin from the full edition's skills.

The build copies the Markdown skill files, drops what the directory edition
cannot ship, and swaps in whole-file overrides from editions/directory/overrides/.
Each override is pinned to the SHA-256 of the full-edition file it replaces,
and of any other full-edition file it was written from, so a change to one of
those files fails the build until the override is reviewed.

Usage: build_directory_edition.py [--check] [--root <repository>]
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path, PurePosixPath

EDITION = "directory-edition"
SOURCES = "editions/directory"
DROPPED_DIRS = ("agents", "scripts", "assets")
DROPPED_FILES = ("skills/validate-plan/references/html-report.md",)
MANIFEST_KEYS = ("name", "version", "description", "author", "homepage", "repository", "license", "keywords", "icon")
HASH_HINT = (
    "review the override against the changed file, then record the new hash; "
    "the copy it was reviewed against is in the commit that "
    "`git log -1 -- editions/directory/overrides.json` shows"
)
SHA256 = re.compile(r"[0-9a-f]{64}")


class BuildError(Exception):
    """The edition cannot be built from the current sources."""


def no_symlink(root: Path, rel: str) -> Path:
    """Return `root / rel` when neither it nor a folder between it and `root` is a symbolic link."""
    path = root
    for part in PurePosixPath(rel).parts:
        path = path / part
        if path.is_symlink():
            raise BuildError(f"{rel}: symbolic links are not read ({path.relative_to(root).as_posix()})")
    return root / rel


def read_input(root: Path, rel: str) -> bytes:
    path = no_symlink(root, rel)
    if not path.exists():
        raise BuildError(f"{rel}: input file missing")
    if not path.is_file():
        raise BuildError(f"{rel}: not a regular file")
    return read_file(path, rel)


def read_file(path: Path, rel: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise BuildError(f"{rel}: cannot be read ({exc.strerror})") from exc


def sha256(root: Path, rel: str) -> str:
    return hashlib.sha256(read_input(root, rel)).hexdigest()


def read_text(root: Path, rel: str) -> str:
    try:
        return read_input(root, rel).decode("utf-8")
    except UnicodeDecodeError:
        raise BuildError(f"{rel}: not valid UTF-8") from None


def is_dropped(rel: str) -> bool:
    parts = rel.split("/")
    return (len(parts) >= 4 and parts[2] in DROPPED_DIRS) or rel in DROPPED_FILES


def load_json(root: Path, rel: str):
    try:
        return json.loads(read_input(root, rel).decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise BuildError(f"{rel}: not valid JSON ({exc.__class__.__name__})") from None


def check_key(key, out: Path) -> str:
    """Return `key` when it is a normalized POSIX path under skills/ that stays inside `out`."""
    if not isinstance(key, str) or "\\" in key or key.startswith("/"):
        raise BuildError(f"{key}: outside skills")
    parts = key.split("/")
    if len(parts) < 2 or parts[0] != "skills" or any(part in ("", ".", "..") for part in parts):
        raise BuildError(f"{key}: outside skills")
    if not (out / key).resolve().is_relative_to(out.resolve()):
        raise BuildError(f"{key}: outside skills")
    return key


def load_overrides(root: Path, out: Path) -> dict:
    """Validate overrides.json and return {path: override bytes}."""
    record = f"{SOURCES}/overrides.json"
    entries = load_json(root, record)
    if not isinstance(entries, dict):
        raise BuildError(f"{record}: must be a JSON object")
    overrides = {}
    for key in sorted(entries):
        entry = entries[key]
        check_key(key, out)
        if not isinstance(entry, dict) or set(entry) - {"source_sha256", "derived_from"} or "source_sha256" not in entry:
            raise BuildError(f"{key}: entry needs source_sha256 and may have derived_from only")
        source = entry["source_sha256"]
        derived = entry.get("derived_from", {})
        if not isinstance(derived, dict):
            raise BuildError(f"{key}: derived_from must be an object")
        for path in sorted(derived):
            check_key(path, out)
        if not key.endswith(".md"):
            raise BuildError(f"{key}: overrides must be Markdown files")
        if is_dropped(key):
            raise BuildError(f"{key}: path is dropped from the edition and cannot be overridden")

        source_path = no_symlink(root, key)
        if source is None:
            if os.path.lexists(source_path):
                raise BuildError(f"{key}: has a source; record its source_sha256 instead of null")
        elif not source_path.exists():
            raise BuildError(f"{key}: source missing")
        for path in sorted(derived):
            if not no_symlink(root, path).exists():
                raise BuildError(f"{path}: source missing (derived_from of {key})")

        pins = ([(key, source)] if source is not None else []) + sorted(derived.items())
        for path, recorded in pins:
            if not isinstance(recorded, str) or not SHA256.fullmatch(recorded):
                raise BuildError(f"{path}: recorded hash must be 64 lowercase hex characters (entry {key})")
            if sha256(root, path) != recorded:
                raise BuildError(f"{path}: source changed since the override of {key} was reviewed; {HASH_HINT}")

        override = f"{SOURCES}/overrides/{key}"
        if not os.path.lexists(no_symlink(root, override)):
            raise BuildError(f"{key}: override file missing at {override}")
        overrides[key] = read_input(root, override)

    folder = no_symlink(root, f"{SOURCES}/overrides")
    if folder.is_dir():
        for path in walk(root, folder):
            rel = path.relative_to(folder).as_posix()
            if path.is_symlink():
                raise BuildError(f"{rel}: symbolic link in {SOURCES}/overrides")
            if path.is_dir():
                continue
            if rel not in entries:
                raise BuildError(f"{rel}: override file has no entry in {record}")
    return overrides


def walk(root: Path, folder: Path, prune=lambda rel: False):
    """Yield every entry under `folder` in sorted order, without following symbolic links."""

    def fail(error: OSError):
        name = Path(error.filename).relative_to(root).as_posix() if error.filename else folder.name
        raise BuildError(f"{name}: cannot be read ({error.strerror})")

    for dirpath, dirnames, filenames in os.walk(folder, onerror=fail, followlinks=False):
        here = Path(dirpath)
        dirnames[:] = sorted(d for d in dirnames if not prune((here / d).relative_to(root).as_posix()))
        for name in sorted(dirnames + filenames):
            yield here / name


def skill_files(root: Path) -> dict:
    """Return {path: bytes} for every skill file the edition copies."""
    files = {}
    skills = no_symlink(root, "skills")
    if not skills.is_dir():
        raise BuildError("skills: folder missing")
    for path in walk(root, skills, prune=lambda rel: is_dropped(rel + "/-")):
        rel = path.relative_to(root).as_posix()
        if is_dropped(rel):
            continue
        if path.is_symlink():
            raise BuildError(f"{rel}: symbolic links are not copied")
        if path.is_dir():
            continue
        if not path.is_file():
            raise BuildError(f"{rel}: not a regular file")
        if not path.name.endswith(".md"):
            raise BuildError(f"{rel}: not Markdown and not in the drop list; add it to the drop list or convert it")
        files[rel] = read_file(path, rel)
    return files


def manifest(root: Path) -> bytes:
    full = load_json(root, ".claude-plugin/plugin.json")
    template = load_json(root, f"{SOURCES}/plugin.json")
    if not isinstance(template, dict) or set(template) != {"description"} or not isinstance(template["description"], str):
        raise BuildError(f"{SOURCES}/plugin.json: must hold only a description string")
    if not isinstance(full, dict):
        raise BuildError(".claude-plugin/plugin.json: must be a JSON object")
    result = {}
    for key in MANIFEST_KEYS:
        if key == "description":
            result[key] = template["description"]
            continue
        if key not in full:
            raise BuildError(f".claude-plugin/plugin.json: missing {key}")
        result[key] = full[key]
    if result["icon"] != "./.claude-plugin/icon.png":
        raise BuildError(".claude-plugin/plugin.json: icon must be ./.claude-plugin/icon.png, the only icon the edition ships")
    if not isinstance(result["keywords"], list):
        raise BuildError(".claude-plugin/plugin.json: keywords must be a list")
    result["keywords"] = [word for word in result["keywords"] if word != "codex"]
    return (json.dumps(result, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def readme(root: Path) -> bytes:
    text = read_text(root, f"{SOURCES}/README.md")
    root_lines = {line.strip() for line in read_text(root, "README.md").splitlines()}
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("claude plugin ") and line not in root_lines:
            raise BuildError(f"README.md: install line not in the root README.md: {line}")
    return text.encode("utf-8")


def collect(root: Path, out: Path) -> dict:
    """Return {path: bytes} for the edition that would be written to `out`."""
    overrides = load_overrides(root, out)
    files = skill_files(root)
    files.update(overrides)
    files[".claude-plugin/plugin.json"] = manifest(root)
    files[".claude-plugin/icon.png"] = read_input(root, ".claude-plugin/icon.png")
    files["README.md"] = readme(root)
    files["LICENSE"] = read_input(root, "LICENSE")
    files["NOTICE.txt"] = read_input(root, "NOTICE")
    return files


def build(root: Path, out: Path) -> list[str]:
    """Write the edition into `out`, which must not exist, and return the sorted paths written."""
    root, out = Path(root), Path(out)
    if os.path.lexists(out):
        raise BuildError(f"{out}: output folder already exists")
    files = collect(root, out)
    out.mkdir(parents=True)
    for rel in sorted(files):
        path = out / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(files[rel])
    return sorted(files)


def edition_files(folder: Path) -> dict:
    """Return {path: bytes} for the committed edition, with None for a symbolic link."""
    files = {}
    for path in walk(folder.parent, folder):
        rel = path.relative_to(folder).as_posix()
        name = path.relative_to(folder.parent).as_posix()
        if path.is_symlink():
            files[rel] = None
        elif path.is_dir():
            continue
        elif not path.is_file():
            raise BuildError(f"{name}: not a regular file")
        else:
            try:
                files[rel] = path.read_bytes()
            except OSError as exc:
                raise BuildError(f"{name}: cannot be read ({exc.strerror})") from exc
    return files


def check(root: Path, edition: Path) -> list[str]:
    """Build the edition in memory and return sorted missing, extra and differs lines."""
    root = Path(root)
    expected = collect(root, root / EDITION)
    actual = edition_files(Path(edition)) if Path(edition).is_dir() else {}
    lines = [f"missing: {p}" for p in expected if p not in actual]
    lines += [f"extra: {p}" for p in actual if p not in expected]
    lines += [f"differs: {p}" for p in expected if p in actual and actual[p] != expected[p]]
    return sorted(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate or check the directory edition.")
    parser.add_argument("--check", action="store_true", help="report differences instead of writing")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]), help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    root = Path(args.root)
    target = root / EDITION

    if args.check:
        try:
            lines = check(root, target)
        except BuildError as exc:
            print(f"Build failed: {exc}")
            return 1
        if lines:
            print(f"{EDITION}/ is out of date; run python3 scripts/build_directory_edition.py")
            for line in lines:
                print(line)
            return 1
        print("Directory edition is up to date.")
        return 0

    tmp = Path(tempfile.mkdtemp(dir=root, prefix=".directory-edition-"))
    previous = tmp / "previous"
    try:
        written = build(root, tmp / EDITION)
        if os.path.lexists(target):
            os.replace(target, previous)
        os.replace(tmp / EDITION, target)
    except BuildError as exc:
        print(f"Build failed: {exc}")
        return 1
    finally:
        if os.path.lexists(previous) and not os.path.lexists(target):
            os.replace(previous, target)
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"Directory edition: wrote {len(written)} files to {EDITION}/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
