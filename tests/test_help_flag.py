"""-h/--help prints usage and exits 0 for the root tools that took it as
an unknown argument (exit 2, usage as an error). Same contract as
gates.py and lint.py (#2066)."""
import contextlib
import importlib
import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

TOOLS = ("run_tests", "kb", "reap_worktrees", "md_claims", "svg_check",
         "fast_path", "one_owner", "eval_trends", "decompose_signals",
         "decompose_lessons", "size_band_calibration", "decompose_grade")


class HelpFlag(unittest.TestCase):
    def test_help_prints_usage_and_exits_zero(self):
        for name in TOOLS:
            for flag in ("-h", "--help"):
                with self.subTest(tool=name, flag=flag):
                    out = io.StringIO()
                    with contextlib.redirect_stdout(out):
                        rc = importlib.import_module(name).main([flag])
                    self.assertEqual(rc, 0)
                    self.assertIn("usage", out.getvalue().lower())


if __name__ == "__main__":
    unittest.main()
