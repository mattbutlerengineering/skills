"""The small protocol accessors (WO-0046, feature:pipeline-board):
checkbox_progress counts under the seam's own checkbox grammar, and
run_ref states the protocol run-ref vocabulary — lifted here from
dashboard's private copy so the fact has one owner.
"""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from protocol import (RUN_ARTIFACTS, MAINTENANCE_STAGE_ARTIFACTS,  # noqa: E402
                      STAGE_ARTIFACTS, breakdown_path, checkbox_progress,
                      run_ref)

MAINTENANCE = ROOT / "tests" / "fixtures" / "maintenance-orientation"


class TestCheckboxProgress(unittest.TestCase):
    def write(self, tmp, text):
        path = Path(tmp) / "breakdown.md"
        path.write_text(text, encoding="utf-8")
        return path

    def test_missing_file_counts_zero_of_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(checkbox_progress(Path(tmp) / "absent.md"),
                             (0, 0))

    def test_counts_checked_of_total(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write(tmp, "- [x] one\n- [ ] two\n- [X] three\n"
                                   "- [ ] four\n- [ ] five\n")
            self.assertEqual(checkbox_progress(path), (2, 5))

    def test_upper_and_lower_x_both_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write(tmp, "- [x] a\n- [X] b\n")
            self.assertEqual(checkbox_progress(path), (2, 2))

    def test_no_checkboxes_counts_zero_of_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write(tmp, "prose only\n")
            self.assertEqual(checkbox_progress(path), (0, 0))


class TestBreakdownPath(unittest.TestCase):
    """The breakdown-placement rule, public (WO-0047 deviation): inline
    in defect.md for a re-entry: implement maintenance run, breakdown.md
    everywhere else."""

    def maintenance_run(self, case):
        fixes = MAINTENANCE / case / "docs" / "fixes"
        runs = sorted(p for p in fixes.iterdir() if p.is_dir())
        assert len(runs) == 1
        return runs[0]

    def test_feature_runs_keep_breakdown_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            self.assertEqual(breakdown_path(run), run / "breakdown.md")

    def test_implement_re_entry_keeps_boxes_in_defect_md(self):
        run = self.maintenance_run("defect-implement-unchecked")
        self.assertEqual(breakdown_path(run), run / "defect.md")

    def test_architect_re_entry_uses_breakdown_md(self):
        run = self.maintenance_run("defect-architect-no-architecture")
        self.assertEqual(breakdown_path(run), run / "breakdown.md")


class TestRunRef(unittest.TestCase):
    def test_docs_root_is_the_product_run(self):
        root = Path("/repo")
        self.assertEqual(run_ref(root, root / "docs"), "product")

    def test_features_carry_the_feature_scale(self):
        root = Path("/repo")
        self.assertEqual(run_ref(root, root / "docs" / "features" / "x"),
                         "feature:x")

    def test_fixes_carry_the_maintenance_scale(self):
        root = Path("/repo")
        self.assertEqual(run_ref(root, root / "docs" / "fixes" / "y"),
                         "maintenance:y")


class TestRunArtifacts(unittest.TestCase):
    def test_covers_every_artifact_from_both_tables(self):
        expected = {artifact for _, artifact
                    in STAGE_ARTIFACTS + MAINTENANCE_STAGE_ARTIFACTS}
        self.assertEqual(set(RUN_ARTIFACTS), expected)

    def test_sorted_and_deduplicated(self):
        self.assertEqual(RUN_ARTIFACTS, sorted(set(RUN_ARTIFACTS)))


if __name__ == "__main__":
    unittest.main()
