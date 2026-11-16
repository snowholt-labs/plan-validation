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

    def test_edition_version_mismatch_names_the_edition(self):
        edition = self.tmp / "directory-edition"
        shutil.copytree(check_package.EDITION, edition)
        manifest = edition / ".claude-plugin/plugin.json"
        data = json.loads(manifest.read_text())
        data["version"] = "0.0.0"
        manifest.write_text(json.dumps(data))
        message = self.run_main(edition)
        self.assertIn("Directory edition version differs from the root manifest", message)


if __name__ == "__main__":
    unittest.main()
