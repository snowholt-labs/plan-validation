"""Tests for the directory edition policy checker and generator."""

import contextlib
import hashlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_directory_edition  # noqa: E402
import check_directory_edition  # noqa: E402
from build_directory_edition import BuildError, build, check  # noqa: E402
from check_directory_edition import check_edition  # noqa: E402

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8

MANIFEST = {
    "name": "plan-validation",
    "version": "1.2.3",
    "description": "Directory edition.",
    "author": {"name": "Example", "url": "https://example.invalid"},
    "homepage": "https://example.invalid",
    "repository": "https://example.invalid/repo",
    "license": "Apache-2.0",
    "keywords": ["plans"],
    "icon": "./.claude-plugin/icon.png",
}

SKILL = (
    "---\n"
    "name: validate-plan\n"
    "description: Validate a plan.\n"
    "disable-model-invocation: true\n"
    "---\n"
    "\n"
    "# Validate\n"
)


def write(path: Path, data) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, bytes):
        path.write_bytes(data)
    else:
        path.write_text(data, encoding="utf-8")
    return path


def make_edition(tmp: Path) -> Path:
    root = tmp / "edition"
    write(root / ".claude-plugin/plugin.json", json.dumps(MANIFEST, indent=2) + "\n")
    write(root / ".claude-plugin/icon.png", PNG)
    write(root / "README.md", "# Directory edition\n")
    write(root / "LICENSE", "License text.\n")
    write(root / "skills/validate-plan/SKILL.md", SKILL)
    return root


class CheckEditionTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.root = make_edition(self.tmp)

    def tearDown(self):
        self._tmp.cleanup()

    def assert_one(self, rule: str, path: str):
        errors = check_edition(self.root)
        matching = [e for e in errors if e.startswith(f"{rule}: ")]
        self.assertEqual(len(matching), 1, errors)
        self.assertTrue(matching[0].startswith(f"{rule}: {path}: "), matching)
        self.assertEqual(errors, matching, "a mutation should trip only its own rule")

    def set_manifest(self, **changes):
        manifest = dict(MANIFEST, **changes)
        write(self.root / ".claude-plugin/plugin.json", json.dumps(manifest))

    def test_valid_edition_passes(self):
        self.assertEqual(check_edition(self.root), [])

    def test_errors_are_sorted(self):
        write(self.root / "z.py", "x = 1\n")
        write(self.root / "a.py", "x = 1\n")
        errors = check_edition(self.root)
        self.assertEqual(errors, sorted(errors))
        self.assertEqual(len(errors), 2)

    def test_allowed_type(self):
        write(self.root / "x.py", "print('x')\n")
        self.assert_one("allowed-type", "x.py")

    def test_allowed_type_judges_images_by_content(self):
        write(self.root / ".claude-plugin/icon.png", "not an image\n")
        self.assert_one("allowed-type", ".claude-plugin/icon.png")

    def test_allowed_type_accepts_each_image_format(self):
        images = {
            "a.png": PNG,
            "b.jpg": b"\xff\xd8\xff\xe0rest",
            "c.jpeg": b"\xff\xd8\xff\xdbrest",
            "d.gif": b"GIF89a\x00\x00",
            "e.gif": b"GIF87a\x00\x00",
            "f.webp": b"RIFF\x00\x00\x00\x00WEBPVP8 ",
            "g.ico": b"\x00\x00\x01\x00\x01\x00",
        }
        for name, data in images.items():
            write(self.root / "images" / name, data)
        self.assertEqual(check_edition(self.root), [])

    def test_allowed_type_rejects_webp_without_marker(self):
        write(self.root / "f.webp", b"RIFFxxxxAVI LIST")
        self.assert_one("allowed-type", "f.webp")

    def test_shebang(self):
        write(self.root / "README.md", "#!/bin/sh\necho hi\n")
        self.assert_one("shebang", "README.md")

    def test_text_encoding_invalid_utf8(self):
        write(self.root / "notes.txt", b"caf\xe9\n")
        self.assert_one("text-encoding", "notes.txt")

    def test_text_encoding_nul_byte(self):
        write(self.root / "notes.txt", b"a\x00b\n")
        self.assert_one("text-encoding", "notes.txt")

    def test_package_config(self):
        write(self.root / "skills/validate-plan/package.json", "{}\n")
        self.assert_one("package-config", "skills/validate-plan/package.json")

    def test_claude_folder(self):
        write(self.root / ".claude/notes.md", "# Notes\n")
        self.assert_one("claude-folder", ".claude")

    def test_plugin_folder_extra_file(self):
        write(self.root / ".claude-plugin/marketplace.json", "{}\n")
        self.assert_one("plugin-folder", ".claude-plugin/marketplace.json")

    def test_plugin_folder_not_at_root(self):
        write(self.root / "skills/validate-plan/.claude-plugin/notes.md", "# Notes\n")
        self.assert_one("plugin-folder", "skills/validate-plan/.claude-plugin")

    def test_unread_config(self):
        write(self.root / ".mcp.json", "{}\n")
        self.assert_one("unread-config", ".mcp.json")

    def test_unread_config_top_level_folder(self):
        write(self.root / "commands/run.md", "# Run\n")
        self.assert_one("unread-config", "commands")

    def test_codex_metadata(self):
        write(self.root / "skills/validate-plan/agents/openai.yaml", "interface: {}\n")
        self.assert_one("codex-metadata", "skills/validate-plan/agents/openai.yaml")

    def test_manifest_fields(self):
        self.set_manifest(userConfig={})
        self.assert_one("manifest-fields", ".claude-plugin/plugin.json")

    def test_manifest_fields_author(self):
        self.set_manifest(author="Example")
        self.assert_one("manifest-fields", ".claude-plugin/plugin.json")
        self.set_manifest(author={"name": "Example", "twitter": "x"})
        self.assert_one("manifest-fields", ".claude-plugin/plugin.json")

    def test_manifest_fields_missing_manifest(self):
        (self.root / ".claude-plugin/plugin.json").unlink()
        self.assert_one("manifest-fields", ".claude-plugin/plugin.json")

    def test_manifest_fields_requires_name(self):
        manifest = dict(MANIFEST)
        del manifest["name"]
        write(self.root / ".claude-plugin/plugin.json", json.dumps(manifest))
        self.assert_one("manifest-fields", ".claude-plugin/plugin.json")

    def test_manifest_fields_icon_is_the_shipped_icon(self):
        self.set_manifest(icon="./assets/plan-validation.png")
        self.assert_one("manifest-fields", ".claude-plugin/plugin.json")

    def test_manifest_fields_icon_file_must_exist(self):
        (self.root / ".claude-plugin/icon.png").unlink()
        self.assert_one("manifest-fields", ".claude-plugin/icon.png")

    def test_undecodable_manifest_reports_once(self):
        write(self.root / ".claude-plugin/plugin.json", b'{"name": "caf\xe9"}')
        self.assert_one("text-encoding", ".claude-plugin/plugin.json")

    def test_frontmatter_fields_requires_description(self):
        write(self.root / "skills/validate-plan/SKILL.md", SKILL.replace("description: Validate a plan.\n", ""))
        self.assert_one("frontmatter-fields", "skills/validate-plan/SKILL.md")

    def test_frontmatter_fields_rejects_block_scalar_description(self):
        for marker in (">-", "|", ">", "> Markdown report", "|x|"):
            with self.subTest(marker=marker):
                text = SKILL.replace("description: Validate a plan.\n", f"description: {marker}\n  Validate a plan.\n")
                write(self.root / "skills/validate-plan/SKILL.md", text)
                self.assert_one("frontmatter-fields", "skills/validate-plan/SKILL.md")

    def test_frontmatter_accepts_quoted_description_starting_with_marker(self):
        for value in ('"> Markdown report"', "'|x|'", '"|"', "'>'"):
            with self.subTest(value=value):
                text = SKILL.replace("description: Validate a plan.\n", f"description: {value}\n")
                write(self.root / "skills/validate-plan/SKILL.md", text)
                self.assertEqual(check_edition(self.root), [])

    def test_frontmatter_fields_duplicate_key(self):
        write(self.root / "skills/validate-plan/SKILL.md", SKILL.replace("---\n\n", "name: validate-plan\n---\n\n"))
        self.assert_one("frontmatter-fields", "skills/validate-plan/SKILL.md")

    def test_frontmatter_accepts_quoted_values(self):
        write(
            self.root / "skills/validate-plan/SKILL.md",
            SKILL.replace("name: validate-plan", 'name: "validate-plan"').replace(": true", ": 'true'"),
        )
        self.assertEqual(check_edition(self.root), [])

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root can read any folder")
    def test_unreadable_folder_fails(self):
        folder = self.root / "skills/validate-plan/references"
        write(folder / "a.md", "# A\n")
        folder.chmod(0)
        try:
            with self.assertRaises(OSError):
                check_edition(self.root)
            self.assertEqual(self.run_main(str(self.root))[0], 1)
        finally:
            folder.chmod(0o755)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "needs named pipes")
    def test_special_file_is_not_read(self):
        os.mkfifo(self.root / "pipe.md")
        self.assert_one("allowed-type", "pipe.md")

    def test_frontmatter_fields(self):
        write(
            self.root / "skills/validate-plan/SKILL.md",
            SKILL.replace("disable-model-invocation: true\n", "disable-model-invocation: true\nallowed-tools: Bash\n"),
        )
        self.assert_one("frontmatter-fields", "skills/validate-plan/SKILL.md")

    def test_frontmatter_fields_validate_plan_needs_flag(self):
        write(self.root / "skills/validate-plan/SKILL.md", SKILL.replace("disable-model-invocation: true\n", ""))
        self.assert_one("frontmatter-fields", "skills/validate-plan/SKILL.md")

    def test_frontmatter_fields_name_matches_directory(self):
        write(self.root / "skills/revise-prompt/SKILL.md", "---\nname: other\ndescription: x\n---\n")
        self.assert_one("frontmatter-fields", "skills/revise-prompt/SKILL.md")

    def test_frontmatter_fields_missing_frontmatter(self):
        write(self.root / "skills/revise-prompt/SKILL.md", "# Revise\n")
        self.assert_one("frontmatter-fields", "skills/revise-prompt/SKILL.md")

    def test_path_characters(self):
        write(self.root / "skills/validate-plan/a b.md", "# A\n")
        self.assert_one("path-characters", "skills/validate-plan/a b.md")

    def test_dropped_reference(self):
        write(self.root / "README.md", "# Edition\n\nNo context.json here.\n")
        self.assert_one("dropped-reference", "README.md")

    def test_dropped_field(self):
        write(self.root / "skills/validate-plan/SKILL.md", SKILL + "\nSet `waits_for`.\n")
        self.assert_one("dropped-field", "skills/validate-plan/SKILL.md")

    def test_dropped_field_only_under_skills(self):
        write(self.root / "README.md", "# Edition\n\nThe `waits_for` field.\n")
        self.assertEqual(check_edition(self.root), [])

    def test_dropped_field_names_publishing_and_renderer_options(self):
        for term in ("artifact.json", "publish_artifact", "handoff_held", "--context", "--report", "--output"):
            with self.subTest(term=term):
                write(self.root / "skills/validate-plan/SKILL.md", SKILL + f"\nUse `{term}`.\n")
                self.assert_one("dropped-field", "skills/validate-plan/SKILL.md")

    def test_symlink(self):
        os.symlink("README.md", self.root / "link.md")
        self.assert_one("symlink", "link.md")

    def test_symlinked_folder_is_not_followed(self):
        os.symlink(self.tmp, self.root / "outside")
        write(self.tmp / "evil.py", "x = 1\n")
        self.assert_one("symlink", "outside")

    def run_main(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            code = check_directory_edition.main(list(argv))
        return code, out.getvalue()

    def test_main_exit_codes(self):
        code, out = self.run_main(str(self.root))
        self.assertEqual(code, 0)
        self.assertIn("Directory edition: 5 files checked.", out)
        write(self.root / "x.py", "x = 1\n")
        code, out = self.run_main(str(self.root))
        self.assertEqual(code, 1)
        self.assertIn("allowed-type: x.py: ", out)

    def test_main_missing_folder_fails(self):
        code, _ = self.run_main(str(self.tmp / "absent"))
        self.assertEqual(code, 1)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


ROOT_MANIFEST = {
    "name": "plan-validation",
    "version": "9.9.9",
    "description": "Full edition.",
    "author": {"name": "Example", "url": "https://example.invalid"},
    "homepage": "https://example.invalid",
    "repository": "https://example.invalid/repo",
    "license": "Apache-2.0",
    "keywords": ["k", "codex"],
    "icon": "./.claude-plugin/icon.png",
    "userConfig": {"publish_artifact": {"type": "boolean", "default": False}},
}
FULL_SKILL = "---\nname: validate-plan\ndescription: Full.\n---\n\n# Full\n"
OVERRIDE_SKILL = "---\nname: validate-plan\ndescription: Edition.\n---\n\n# Edition\n"
INSTALL = "claude plugin install plan-validation@m\n"


def make_source(tmp: Path) -> Path:
    root = tmp
    skill = root / "skills/validate-plan"
    write(skill / "SKILL.md", FULL_SKILL)
    write(skill / "references/a.md", "# A\n")
    write(skill / "references/html-report.md", "# HTML report\n")
    write(skill / "scripts/x.py", "x = 1\n")
    write(skill / "assets/y.css", "body {}\n")
    write(skill / "agents/openai.yaml", "interface: {}\n")
    write(root / ".claude-plugin/plugin.json", json.dumps(ROOT_MANIFEST, indent=2) + "\n")
    write(root / ".claude-plugin/icon.png", PNG)
    write(root / "LICENSE", "License.\n")
    write(root / "NOTICE", "Notice.\n")
    write(root / "README.md", "# Full\n\n" + INSTALL)
    sources = root / "editions/directory"
    write(sources / "plugin.json", json.dumps({"description": "Edition description."}) + "\n")
    write(sources / "README.md", "# Edition\n\n" + INSTALL)
    write(sources / "overrides/skills/validate-plan/SKILL.md", OVERRIDE_SKILL)
    set_overrides(root, {"skills/validate-plan/SKILL.md": {"source_sha256": sha(skill / "SKILL.md")}})
    return root


def set_overrides(root: Path, entries: dict):
    write(root / "editions/directory/overrides.json", json.dumps(entries, indent=2) + "\n")


def overrides(root: Path) -> dict:
    return json.loads((root / "editions/directory/overrides.json").read_text())


def tree(folder: Path) -> dict:
    return {
        p.relative_to(folder).as_posix(): p.read_bytes()
        for p in sorted(folder.rglob("*"))
        if p.is_file()
    }


class BuildEditionTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.root = make_source(self.tmp)
        self.out = self.tmp / "out"

    def tearDown(self):
        self._tmp.cleanup()

    def assert_build_error(self, *parts):
        with self.assertRaises(BuildError) as caught:
            build(self.root, self.out)
        for part in parts:
            self.assertIn(part, str(caught.exception))
        return str(caught.exception)

    def run_main(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            code = build_directory_edition.main(list(argv))
        return code, out.getvalue()

    def leftovers(self):
        return sorted(p.name for p in self.root.glob(".directory-edition-*"))

    def test_build_copies_markdown_and_drops_excluded(self):
        written = build(self.root, self.out)
        self.assertEqual(written, sorted(written))
        self.assertIn("skills/validate-plan/references/a.md", written)
        self.assertTrue((self.out / "skills/validate-plan/references/a.md").is_file())
        for dropped in (
            "skills/validate-plan/references/html-report.md",
            "skills/validate-plan/scripts/x.py",
            "skills/validate-plan/assets/y.css",
            "skills/validate-plan/agents/openai.yaml",
        ):
            self.assertNotIn(dropped, written)
            self.assertFalse((self.out / dropped).exists(), dropped)
        self.assertEqual(sorted(tree(self.out)), written)
        for name in (".claude-plugin/plugin.json", ".claude-plugin/icon.png", "README.md", "LICENSE", "NOTICE.txt"):
            self.assertIn(name, written)
        self.assertEqual((self.out / "NOTICE.txt").read_bytes(), b"Notice.\n")
        self.assertEqual((self.out / ".claude-plugin/icon.png").read_bytes(), PNG)
        self.assertEqual((self.out / "README.md").read_bytes(), (self.root / "editions/directory/README.md").read_bytes())

    def test_override_replaces_file(self):
        build(self.root, self.out)
        self.assertEqual((self.out / "skills/validate-plan/SKILL.md").read_text(), OVERRIDE_SKILL)

    def test_stale_override_hash_fails(self):
        write(self.root / "skills/validate-plan/SKILL.md", FULL_SKILL + "\nChanged.\n")
        self.assert_build_error(
            "skills/validate-plan/SKILL.md", "source changed", "git log -1 -- editions/directory/overrides.json"
        )
        self.assertFalse(self.out.exists())

    def test_stale_derived_hash_fails(self):
        html = self.root / "skills/validate-plan/references/html-report.md"
        entries = overrides(self.root)
        entries["skills/validate-plan/SKILL.md"]["derived_from"] = {
            "skills/validate-plan/references/html-report.md": sha(html)
        }
        set_overrides(self.root, entries)
        build(self.root, self.tmp / "first")
        write(html, "# HTML report, changed\n")
        self.assert_build_error("skills/validate-plan/references/html-report.md", "source changed")

    def test_new_file_override(self):
        entries = overrides(self.root)
        entries["skills/validate-plan/references/new.md"] = {"source_sha256": None}
        set_overrides(self.root, entries)
        write(self.root / "editions/directory/overrides/skills/validate-plan/references/new.md", "# New\n")
        build(self.root, self.out)
        self.assertEqual((self.out / "skills/validate-plan/references/new.md").read_text(), "# New\n")

        entries["skills/validate-plan/references/a.md"] = {"source_sha256": None}
        set_overrides(self.root, entries)
        write(self.root / "editions/directory/overrides/skills/validate-plan/references/a.md", "# A2\n")
        self.out = self.tmp / "out2"
        self.assert_build_error("skills/validate-plan/references/a.md", "has a source")

    def test_missing_override_file_fails(self):
        (self.root / "editions/directory/overrides/skills/validate-plan/SKILL.md").unlink()
        self.assert_build_error("skills/validate-plan/SKILL.md", "override file missing")
        self.assertFalse(self.out.exists())

    def test_nested_dropped_name_is_kept(self):
        write(self.root / "skills/validate-plan/references/scripts/usage.md", "# Usage\n")
        build(self.root, self.out)
        self.assertTrue((self.out / "skills/validate-plan/references/scripts/usage.md").is_file())

    def test_override_problems_fail(self):
        original = overrides(self.root)
        write(self.root / "editions/directory/overrides/skills/validate-plan/references/extra.md", "# Extra\n")
        self.assert_build_error("skills/validate-plan/references/extra.md", "no entry")
        (self.root / "editions/directory/overrides/skills/validate-plan/references/extra.md").unlink()

        skill = self.root / "skills/validate-plan/SKILL.md"
        skill.unlink()
        self.assert_build_error("skills/validate-plan/SKILL.md", "source missing")
        write(skill, FULL_SKILL)

        entries = json.loads(json.dumps(original))
        entries["skills/validate-plan/SKILL.md"]["derived_from"] = {"skills/validate-plan/references/gone.md": "0" * 64}
        set_overrides(self.root, entries)
        self.assert_build_error("skills/validate-plan/references/gone.md", "source missing")

        for key in ("skills/../x.md", "skills/a/../../.github/x.yml"):
            entries = json.loads(json.dumps(original))
            entries[key] = {"source_sha256": None}
            set_overrides(self.root, entries)
            self.assert_build_error(key, "outside skills")

        entries = json.loads(json.dumps(original))
        entries["skills/validate-plan/SKILL.md"]["derived_from"] = {"../README.md": "0" * 64}
        set_overrides(self.root, entries)
        self.assert_build_error("../README.md", "outside skills")

        self.assertFalse(self.out.exists())
        self.assertFalse((self.tmp / "x.md").exists())
        self.assertFalse((self.root / ".github").exists())

    def test_symlinked_inputs_fail(self):
        outside = self.tmp / "outside"
        write(outside / "secret.txt", "secret\n")
        write(outside / "skills/validate-plan/SKILL.md", FULL_SKILL)
        write(outside / "overrides/skills/validate-plan/SKILL.md", OVERRIDE_SKILL)
        cases = {
            "LICENSE": "secret.txt",
            "editions/directory/README.md": "secret.txt",
            "editions/directory/overrides": "overrides",
            "skills": "skills",
        }
        for rel, target in cases.items():
            with self.subTest(rel=rel):
                self.root = make_source(self.tmp / ("case-" + rel.replace("/", "-")))
                self.out = self.root / "out"
                link = self.root / rel
                if link.is_dir():
                    shutil.rmtree(link)
                else:
                    link.unlink()
                os.symlink(outside / target, link)
                self.assert_build_error(rel, "symbolic link")
                self.assertFalse(self.out.exists())

    def test_symlink_inside_overrides_fails(self):
        folder = self.root / "editions/directory/overrides/skills/validate-plan"
        os.symlink(self.tmp, folder / "references")
        self.assert_build_error("symbolic link")

    def test_symlinked_skills_without_overrides_fails(self):
        set_overrides(self.root, {})
        shutil.rmtree(self.root / "editions/directory/overrides")
        (self.root / "editions/directory/overrides").mkdir()
        outside = self.tmp / "outside"
        write(outside / "skills/validate-plan/SKILL.md", FULL_SKILL)
        shutil.rmtree(self.root / "skills")
        os.symlink(outside / "skills", self.root / "skills")
        self.assert_build_error("skills", "symbolic link")
        self.assertFalse(self.out.exists())

    def test_readme_not_utf8_fails(self):
        write(self.root / "editions/directory/README.md", b"# Edition caf\xe9\n")
        self.assert_build_error("README.md", "not valid UTF-8")

    def test_readme_indented_install_line_is_checked(self):
        write(self.root / "editions/directory/README.md", "# Edition\n\n- Run:\n  claude plugin install other@m\n")
        self.assert_build_error("README.md", "install line")

    def test_override_of_dropped_path_fails(self):
        html = self.root / "skills/validate-plan/references/html-report.md"
        entries = overrides(self.root)
        entries["skills/validate-plan/references/html-report.md"] = {"source_sha256": sha(html)}
        set_overrides(self.root, entries)
        write(self.root / "editions/directory/overrides/skills/validate-plan/references/html-report.md", "# Back\n")
        self.assert_build_error("skills/validate-plan/references/html-report.md", "dropped")

    def test_symlinked_dropped_folder_is_ignored(self):
        assets = self.root / "skills/validate-plan/assets"
        shutil.rmtree(assets)
        os.symlink(self.tmp, assets)
        build(self.root, self.out)
        self.assertFalse((self.out / "skills/validate-plan/assets").exists())

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root can read any folder")
    def test_unreadable_skills_folder_fails(self):
        folder = self.root / "skills/validate-plan/references"
        folder.chmod(0)
        try:
            self.assert_build_error("skills/validate-plan/references", "cannot be read")
        finally:
            folder.chmod(0o755)

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root can read any file")
    def test_unreadable_skill_file_fails(self):
        path = self.root / "skills/validate-plan/references/a.md"
        path.chmod(0)
        try:
            self.assert_build_error("skills/validate-plan/references/a.md", "cannot be read")
        finally:
            path.chmod(0o644)

    def test_read_error_without_strerror_names_the_error(self):
        with mock.patch.object(Path, "read_bytes", side_effect=OSError("disk gone")):
            message = self.assert_build_error("cannot be read", "disk gone")
        self.assertNotIn("None", message)

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root can read any file")
    def test_unreadable_committed_edition_file_fails(self):
        build(self.root, self.out)
        path = self.out / "README.md"
        path.chmod(0)
        try:
            with self.assertRaises(BuildError) as caught:
                check(self.root, self.out)
            self.assertIn("README.md: cannot be read", str(caught.exception))
        finally:
            path.chmod(0o644)

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root can read any file")
    def test_unreadable_input_file_fails(self):
        path = self.root / "editions/directory/plugin.json"
        path.chmod(0)
        try:
            self.assert_build_error("editions/directory/plugin.json", "cannot be read")
        finally:
            path.chmod(0o644)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "needs named pipes")
    def test_special_file_fails(self):
        os.mkfifo(self.root / "skills/validate-plan/pipe.md")
        self.assert_build_error("skills/validate-plan/pipe.md", "not a regular file")

    def test_readme_install_lines_match_root(self):
        write(self.root / "editions/directory/README.md", "# Edition\n\nclaude plugin install other@m\n")
        self.assert_build_error("README.md", "install line")

    def test_unexpected_file_type_fails(self):
        write(self.root / "skills/validate-plan/run.sh", "echo hi\n")
        self.assert_build_error("skills/validate-plan/run.sh")
        self.assertFalse(self.out.exists())

    def test_root_icon_must_be_the_shipped_icon(self):
        manifest_path = self.root / ".claude-plugin/plugin.json"
        data = json.loads(manifest_path.read_text())
        data["icon"] = "./assets/icon.png"
        manifest_path.write_text(json.dumps(data))
        self.assert_build_error(".claude-plugin/plugin.json", "icon")

    def test_manifest_version_and_no_user_config(self):
        build(self.root, self.out)
        text = (self.out / ".claude-plugin/plugin.json").read_text()
        manifest = json.loads(text)
        self.assertEqual(manifest["version"], "9.9.9")
        self.assertEqual(list(manifest)[1], "version")
        self.assertEqual(manifest["author"], ROOT_MANIFEST["author"])
        self.assertEqual(manifest["description"], "Edition description.")
        self.assertEqual(manifest["keywords"], ["k"])
        self.assertNotIn("userConfig", manifest)
        self.assertEqual(
            list(manifest),
            ["name", "version", "description", "author", "homepage", "repository", "license", "keywords", "icon"],
        )
        self.assertEqual(text, json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

    def test_build_is_deterministic(self):
        build(self.root, self.tmp / "a")
        build(self.root, self.tmp / "b")
        self.assertEqual(tree(self.tmp / "a"), tree(self.tmp / "b"))

    def test_build_refuses_existing_output(self):
        self.out.mkdir()
        with self.assertRaises(BuildError):
            build(self.root, self.out)

    def test_check_reports_extra_missing_and_differing(self):
        edition = self.root / "directory-edition"
        build(self.root, edition)
        self.assertEqual(check(self.root, edition), [])
        write(edition / "skills/extra.md", "# Extra\n")
        (edition / "LICENSE").unlink()
        write(edition / "README.md", "# Changed\n")
        self.assertEqual(
            check(self.root, edition),
            ["differs: README.md", "extra: skills/extra.md", "missing: LICENSE"],
        )

    def test_main_check_exit_codes(self):
        self.assertEqual(self.run_main("--root", str(self.root))[0], 0)
        self.assertEqual(self.run_main("--root", str(self.root), "--check")[0], 0)
        write(self.root / "directory-edition/README.md", "# Changed\n")
        code, out = self.run_main("--root", str(self.root), "--check")
        self.assertEqual(code, 1)
        self.assertIn("differs: README.md", out)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "needs named pipes")
    def test_check_reports_special_file_in_edition(self):
        build(self.root, self.root / "directory-edition")
        os.mkfifo(self.root / "directory-edition/pipe.md")
        code, out = self.run_main("--root", str(self.root), "--check")
        self.assertEqual(code, 1)
        self.assertIn("directory-edition/pipe.md: not a regular file", out)

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root can read any file")
    def test_check_reports_unreadable_edition_paths(self):
        build(self.root, self.root / "directory-edition")
        for rel in ("directory-edition/skills", "directory-edition/README.md"):
            with self.subTest(rel=rel):
                path = self.root / rel
                path.chmod(0)
                try:
                    code, out = self.run_main("--root", str(self.root), "--check")
                finally:
                    path.chmod(0o755 if path.is_dir() else 0o644)
                self.assertEqual(code, 1)
                self.assertIn("Build failed", out)
                self.assertIn("cannot be read", out)

    def test_main_failure_keeps_previous_output(self):
        kept = self.root / "directory-edition/kept.md"
        write(kept, "# Kept\n")
        skill = self.root / "skills/validate-plan/SKILL.md"
        write(skill, FULL_SKILL + "\nChanged.\n")
        code, out = self.run_main("--root", str(self.root))
        self.assertEqual(code, 1)
        self.assertIn("source changed", out)
        self.assertTrue(kept.is_file())
        self.assertEqual(self.leftovers(), [])

        (self.root / "directory-edition/kept.md").unlink()
        (self.root / "directory-edition").rmdir()
        self.assertEqual(self.run_main("--root", str(self.root))[0], 1)
        self.assertFalse((self.root / "directory-edition").exists())
        self.assertEqual(self.leftovers(), [])

        write(skill, FULL_SKILL)
        write(kept, "# Kept\n")
        real_replace = os.replace
        target = self.root / "directory-edition"

        def failing_replace(src, dst, *args, **kwargs):
            if Path(dst) == target and Path(src).name != "previous":
                raise OSError("simulated move failure")
            return real_replace(src, dst, *args, **kwargs)

        with mock.patch.object(build_directory_edition.os, "replace", failing_replace):
            with self.assertRaises(OSError):
                self.run_main("--root", str(self.root))
        self.assertTrue(kept.is_file())
        self.assertEqual(self.leftovers(), [])

    def test_main_replaces_previous_output(self):
        stale = self.root / "directory-edition/stale.md"
        write(stale, "# Stale\n")
        code, _ = self.run_main("--root", str(self.root))
        self.assertEqual(code, 0)
        self.assertFalse(stale.exists())
        self.assertTrue((self.root / "directory-edition/skills/validate-plan/SKILL.md").is_file())
        self.assertEqual(self.leftovers(), [])


if __name__ == "__main__":
    unittest.main()
