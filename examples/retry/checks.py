"""Run the same acceptance assertions against either bundled fixture."""

import argparse
import importlib.util
import sys
import unittest
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("implementation", choices=("uncapped", "corrected"))
    args = parser.parse_args()
    path = Path(__file__).with_name(args.implementation + ".py")
    spec = importlib.util.spec_from_file_location("fixture", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    class AcceptanceTests(unittest.TestCase):
        def test_first_attempt(self):
            self.assertEqual(module.retry_delay(0), 1)

        def test_growth(self):
            self.assertEqual(module.retry_delay(3), 8)

        def test_maximum_delay(self):
            self.assertEqual(module.retry_delay(6), 30)

    result = unittest.TextTestRunner(verbosity=1).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(AcceptanceTests)
    )
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
