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


class TestFolderWins(unittest.TestCase):
    """Issue #2180: a run's kind is its folder. defect.md outside
    docs/fixes/ does not put a run on the maintenance ladder, so the
    ladder agrees with run_ref's kind."""

    def test_a_feature_run_holding_defect_md_walks_the_feature_ladder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run = root / "docs" / "features" / "weird"
            run.mkdir(parents=True)
            (run / "idea.md").write_text("x", encoding="utf-8")
            (run / "defect.md").write_text("x", encoding="utf-8")
            self.assertFalse(protocol.is_maintenance_run(run))
            self.assertEqual(protocol.run_ref(root, run), "feature:weird")
            self.assertEqual(protocol.next_stage(run), "prd")
            self.assertEqual(
                [stage for stage, _ in protocol.stage_states(run)][:2],
                ["idea", "prd"])
            self.assertEqual(protocol.breakdown_path(run),
                             run / "breakdown.md")

    def test_a_product_run_holding_defect_md_is_not_maintenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            docs.mkdir()
            (docs / "defect.md").write_text("x", encoding="utf-8")
            self.assertFalse(protocol.is_maintenance_run(docs))
            self.assertEqual(protocol.next_stage(docs), "idea")


if __name__ == "__main__":
    unittest.main()
