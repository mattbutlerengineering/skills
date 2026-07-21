"""Orientation-protocol seam: the artifacts-are-the-state decision table
(docs/pipeline-protocol.md) verified against fixture docs trees, pinning
the protocol module's next_stage directly — the one implementation that
must agree with the spec in docs/pipeline-protocol.md.

Each fixture under tests/fixtures/orientation/ is one row of the table:
a `run/` directory holding a run's artifacts, and an `expected` file naming
the stage orientation must return for that tree.

TestCli pins the orientation.py adapter itself: the exit-code contract
(0 stage / 2 unusable input) that skills and scripts consume when they
shell out to it.
"""
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import orientation  # noqa: E402
from protocol import next_stage  # noqa: E402

# discover puts tests/ on sys.path; selective package-style runs need it
# added for the sibling cli_contract import
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cli_contract  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures" / "orientation"


def fixture_cases():
    return sorted(p for p in FIXTURES.iterdir() if p.is_dir())


class TestFixtureTrees(unittest.TestCase):
    def test_fixtures_exist(self):
        self.assertTrue(fixture_cases(), f"no fixture trees in {FIXTURES}")

    def test_decision_table(self):
        for case in fixture_cases():
            with self.subTest(fixture=case.name):
                expected = (case / "expected").read_text(encoding="utf-8").strip()
                self.assertEqual(next_stage(case / "run"), expected)


def run_cli(argv):
    """(exit code, stdout + stderr) — orientation reports problems on
    stderr and the stage on stdout, so the contract reads both."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = orientation.main(["orientation.py", *argv])
    return code, out.getvalue() + err.getvalue()


class TestCli(cli_contract.CliContract, unittest.TestCase):
    usage_fragment = "usage: orientation.py <run-directory>"
    bad_argv = ("docs", "extra")  # wrong arity, not a bogus subcommand

    def run_cli(self, argv):
        return run_cli(argv)

    def test_no_argument_prints_usage_and_exits_2(self):
        code, text = run_cli([])
        self.assertEqual(code, 2)
        self.assertIn(self.usage_fragment, text)

    def test_a_missing_directory_exits_2(self):
        code, text = run_cli(["no/such/run-dir"])
        self.assertEqual(code, 2)
        self.assertIn("orientation: not a directory: no/such/run-dir", text)

    def test_a_run_directory_prints_its_next_stage_and_exits_0(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, text = run_cli([tmp])
        self.assertEqual(code, 0)
        # an empty run has produced nothing, so the pipeline starts at idea
        self.assertEqual(text, "idea\n")


if __name__ == "__main__":
    unittest.main()
