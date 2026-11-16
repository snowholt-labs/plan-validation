"""Tests for the directory edition parts of check_package.py."""

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

    def copy_edition(self) -> Path:
        edition = self.tmp / "directory-edition"
        shutil.copytree(check_package.EDITION, edition)
        return edition

    def test_malformed_edition_manifest_is_reported(self):
        edition = self.copy_edition()
        (edition / ".claude-plugin/plugin.json").write_text("{not json")
        message = self.run_main(edition)
        self.assertIn("directory-edition/.claude-plugin/plugin.json is not valid JSON", message)

    def test_edition_must_keep_the_no_publish_line(self):
        edition = self.copy_edition()
        skill = edition / "skills/validate-plan/SKILL.md"
        skill.write_text(skill.read_text().replace(check_package.EDITION_NO_PUBLISH, ""))
        message = self.run_main(edition)
        self.assertIn("directory-edition validate-plan SKILL.md must keep the no-publish line", message)

    def test_link_leaving_the_edition_is_reported(self):
        edition = self.copy_edition()
        readme = edition / "README.md"
        readme.write_text(readme.read_text() + "\nSee [the root](../README.md).\n")
        message = self.run_main(edition)
        self.assertIn("directory-edition/README.md: link leaves the edition ../README.md", message)


if __name__ == "__main__":
    unittest.main()
