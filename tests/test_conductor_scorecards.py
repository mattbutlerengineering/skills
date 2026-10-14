"""conductor_close.history and `conductor.py scorecards [N]` (#797): the
reader of docs/factory/scorecards.jsonl, so one batch's scorecard can be
compared with the last. Tests assert the EXACT rows, problem strings and
printed lines.
"""
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import conductor
import conductor_close as close

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cli_contract  # noqa: E402

NOW = datetime(2026, 10, 13, 16, 0, tzinfo=timezone.utc)

# Two batches, the older written before #798 added ran_estimate_usd: the
# reader reads both shapes.
OLDER = {"batch": "b1", "at": "2026-10-12T16:00:00Z", "merged": 0,
         "blocked": 2, "metered_usd": 9.33, "estimate_usd": 30,
         "estimate_error_pct": -68.9, "stalls": 3,
         "metered_usd_per_merged": None, "conductor_session": "unmetered"}
NEWER = {"batch": "b2", "at": "2026-10-13T16:00:00Z", "merged": 1,
         "blocked": 1, "metered_usd": 21.64, "estimate_usd": 30,
         "ran_estimate_usd": 20, "estimate_error_pct": 8.2, "stalls": 1,
         "metered_usd_per_merged": 21.64, "conductor_session": "unmetered"}


def write(root, rows, extra=""):
    path = Path(root) / close.SCORECARDS
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows) + extra,
                    encoding="utf-8")


class TestHistory(unittest.TestCase):
    def test_reads_every_row_in_file_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, [OLDER, NEWER])
            self.assertEqual(close.history(tmp), ([OLDER, NEWER], []))

    def test_no_file_is_no_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(close.history(tmp), ([], []))

    def test_a_line_that_does_not_parse_fails_naming_file_and_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, [OLDER], "{nope\n")
            self.assertEqual(close.history(tmp), (None, [
                f"cd: {close.SCORECARDS}:2 is not valid JSON: Expecting"
                " property name enclosed in double quotes: line 1 column 2"
                " (char 1)"]))

    def test_a_line_that_is_not_an_object_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, [OLDER], "[1]\n")
            self.assertEqual(close.history(tmp), (None, [
                f"cd: {close.SCORECARDS}:2 is not a scorecard row (a JSON"
                " object with a batch)"]))

    def test_an_appended_scorecard_reads_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(close.append_scorecard(tmp, OLDER), [])
            self.assertEqual(close.append_scorecard(tmp, NEWER), [])
            self.assertEqual(close.append_scorecard(tmp, NEWER), [])
            self.assertEqual(close.history(tmp), ([OLDER, NEWER], []))


class TestScorecardsCli(unittest.TestCase):
    def main(self, root, argv):
        return cli_contract.capture(conductor.main, argv, env={},
                                    clock=lambda: NOW, root=root)

    def test_prints_each_metric_across_batches_with_its_delta(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, [OLDER, NEWER])
            self.assertEqual(self.main(tmp, ["scorecards"]), (0, (
                "scorecards: the last 2 of 2 batch(es): b1 -> b2\n"
                "  merged: 0 -> 1 (+1)\n"
                "  blocked: 2 -> 1 (-1)\n"
                "  metered_usd: 9.33 -> 21.64 (+12.31)\n"
                "  estimate_usd: 30 -> 30 (+0)\n"
                "  ran_estimate_usd: - -> 20 (n/a)\n"
                "  estimate_error_pct: -68.9 -> 8.2 (+77.1)\n"
                "  stalls: 3 -> 1 (-2)\n"
                "  metered_usd_per_merged: - -> 21.64 (n/a)\n"
                "cd: 0 problem(s)\n")))

    def test_n_limits_the_window_to_the_latest_batches(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, [OLDER, NEWER])
            code, out = self.main(tmp, ["scorecards", "1"])
            self.assertEqual(code, 0)
            self.assertEqual(out.splitlines()[:3], [
                "scorecards: the last 1 of 2 batch(es): b2",
                "  merged: 1", "  blocked: 1"])

    def test_no_history_says_so(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.main(tmp, ["scorecards"]), (0, (
                f"scorecards: no batch scored yet in {close.SCORECARDS}\n"
                "cd: 0 problem(s)\n")))

    def test_a_malformed_history_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, [OLDER], "[1]\n")
            self.assertEqual(self.main(tmp, ["scorecards"]), (1, (
                f"cd: {close.SCORECARDS}:2 is not a scorecard row (a JSON"
                " object with a batch)\ncd: 1 problem(s)\n")))

    def test_a_count_that_is_not_a_positive_number_prints_usage(self):
        with tempfile.TemporaryDirectory() as tmp:
            for argv in (["scorecards", "0"], ["scorecards", "x"],
                         ["scorecards", "1", "2"]):
                code, out = self.main(tmp, argv)
                self.assertEqual(code, 2, argv)
                self.assertIn("python3 conductor.py scorecards [N]", out)


class TestConductClosesWithARetro(unittest.TestCase):
    """#818: the scorecards and calibrate verbs need a reader, so the
    conduct skill's Close ends by reading them in the session that ran
    the batch. The skill prose is the runtime interface (it ships in the
    plugin), so the retro step is pinned here."""

    def text(self):
        path = Path(__file__).resolve().parents[1] / "skills" / "conduct" \
            / "SKILL.md"
        return " ".join(path.read_text(encoding="utf-8").split())

    def test_close_ends_by_reading_the_trend_and_the_calibration(self):
        text = self.text()
        self.assertIn("### 7. Read the batch back", text)
        self.assertIn("python3 conductor.py scorecards 5", text)
        self.assertIn("python3 conductor.py calibrate", text)
        self.assertIn("name the metric that moved", text)

    def test_the_retro_names_where_each_finding_goes(self):
        text = self.text()
        self.assertIn("`conductor.step_weights` and `budgets_usd`", text)
        self.assertIn("a plain issue with a `type:*` label", text)


if __name__ == "__main__":
    unittest.main()
