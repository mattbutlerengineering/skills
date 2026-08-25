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

from protocol import checkbox_progress, run_ref  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
