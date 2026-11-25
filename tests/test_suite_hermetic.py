"""The suite never inherits the CI event (tests/__init__.py).

In CI the check job's environment names the real PR's event: through
GITHUB_EVENT_PATH on a pull_request run, and through FACTORY_EVENT_PATH
on a validator dispatch (the synthesize step writes it to $GITHUB_ENV,
and cli.read_event prefers it). A test that runs gates inside a temp
repo would otherwise judge that PR against a tree that never held its
base: detector P fails it. The names come from cli.py itself, so an
event variable added there is dropped here or this test fails.
"""
import os
import re
import unittest
from pathlib import Path

CLI = Path(__file__).resolve().parent.parent / "tools" / "cli.py"


class TestTheSuiteDropsTheCIEvent(unittest.TestCase):
    def test_every_event_variable_cli_reads_is_absent(self):
        names = set(re.findall(r'"([A-Z_]*EVENT_(?:PATH|NAME))"',
                               CLI.read_text(encoding="utf-8")))
        self.assertIn("FACTORY_EVENT_PATH", names)
        self.assertIn("GITHUB_EVENT_PATH", names)
        self.assertEqual(sorted(n for n in names if n in os.environ), [])


if __name__ == "__main__":
    unittest.main()
