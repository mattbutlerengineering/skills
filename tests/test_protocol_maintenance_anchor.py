"""Audit defect #1855: is_maintenance_run is anchored to the docs/fixes layout."""
import tempfile
import unittest
from pathlib import Path

import protocol


class TestMaintenanceAnchor(unittest.TestCase):
    def test_checkout_named_fixes_is_not_maintenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "fixes" / "docs"
            docs.mkdir(parents=True)
            self.assertFalse(protocol.is_maintenance_run(docs))

    def test_docs_fixes_slug_is_maintenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / "docs" / "fixes" / "bug"
            run.mkdir(parents=True)
            self.assertTrue(protocol.is_maintenance_run(run))

if __name__ == "__main__":
    unittest.main()
