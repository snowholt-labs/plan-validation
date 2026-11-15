"""Tests for the directory edition policy checker and generator."""

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_directory_edition  # noqa: E402
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


if __name__ == "__main__":
    unittest.main()
