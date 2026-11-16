"""Tests for the directory edition parts of check_package.py."""

import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_package  # noqa: E402


class EditionManifestTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)

    def run_main(self, edition: Path) -> str:
        with mock.patch.object(check_package, "EDITION", edition), \
                self.assertRaises(SystemExit) as raised:
            check_package.main()
        return str(raised.exception)

    def test_missing_edition_manifest_is_reported(self):
        message = self.run_main(self.tmp / "directory-edition")
        self.assertIn("directory-edition/.claude-plugin/plugin.json is missing", message)

    def test_edition_name_or_version_mismatch_names_the_edition(self):
        for key in ("version", "name"):
            with self.subTest(key=key):
                edition = self.tmp / key / "directory-edition"
                shutil.copytree(check_package.EDITION, edition)
                manifest = edition / ".claude-plugin/plugin.json"
                data = json.loads(manifest.read_text())
                data[key] = "0.0.0"
                manifest.write_text(json.dumps(data))
                message = self.run_main(edition)
                self.assertIn(f"Directory edition {key} differs from the root manifest", message)

    def copy_edition(self, case: str = "copy") -> Path:
        edition = self.tmp / case / "directory-edition"
        shutil.copytree(check_package.EDITION, edition)
        return edition

    def test_copied_edition_passes(self):
        # Also under a symlinked parent folder, so the edition's links resolve elsewhere.
        (self.tmp / "real").mkdir()
        (self.tmp / "linked").symlink_to(self.tmp / "real", target_is_directory=True)
        shutil.copytree(check_package.EDITION, self.tmp / "real/directory-edition")
        for edition in (self.copy_edition(), self.tmp / "linked/directory-edition"):
            with self.subTest(edition=edition.parent.name):
                with mock.patch.object(check_package, "EDITION", edition), \
                        contextlib.redirect_stdout(io.StringIO()) as out:
                    check_package.main()
                self.assertIn("directory edition files checked", out.getvalue())

    def test_malformed_edition_manifest_is_reported(self):
        for text in ("{not json", "[]", "null"):
            with self.subTest(text=text):
                edition = self.copy_edition(text)
                (edition / ".claude-plugin/plugin.json").write_text(text)
                self.assertEqual(self.run_main(edition).splitlines(), [
                    "directory-edition/.claude-plugin/plugin.json must be a JSON object"
                    "; run python3 scripts/build_directory_edition.py",
                ])

    def test_edition_must_keep_the_no_publish_line(self):
        expected = ("directory-edition validate-plan SKILL.md must keep the no-publish line word for word"
                    "; run python3 scripts/build_directory_edition.py")
        for case in ("dropped", "no manifest"):
            with self.subTest(case=case):
                edition = self.copy_edition(case)
                skill = edition / "skills/validate-plan/SKILL.md"
                text = skill.read_text().replace(check_package.EDITION_NO_PUBLISH, "")
                skill.write_text(text)
                if case == "no manifest":
                    (edition / ".claude-plugin/plugin.json").unlink()
                lines = self.run_main(edition).splitlines()
                self.assertIn(expected, lines)
                self.assertEqual(len(lines), 2 if case == "no manifest" else 1, lines)

    def test_link_leaving_the_edition_is_reported(self):
        edition = self.copy_edition()
        readme = edition / "README.md"
        readme.write_text(readme.read_text() + "\nSee [the root](../README.md).\n")
        self.assertEqual(self.run_main(edition).splitlines(),
                         ["directory-edition/README.md: link leaves the edition ../README.md"])

if __name__ == "__main__":
    unittest.main()
