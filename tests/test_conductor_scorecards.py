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

# Two batches, the older written before #808 added ran_estimate_usd,
# the newer between #808 and #814, when estimate_error_pct meant the
# steps that ran: the reader reads both shapes, each by its meaning.
OLDER = {"batch": "b1", "at": "2026-10-12T16:00:00Z", "merged": 0,
         "blocked": 2, "metered_usd": 9.33, "estimate_usd": 30,
         "estimate_error_pct": -68.9, "stalls": 3,
         "metered_usd_per_merged": None, "conductor_session": "unmetered"}
NEWER = {"batch": "b2", "at": "2026-10-13T16:00:00Z", "merged": 1,
         "blocked": 1, "metered_usd": 21.64, "estimate_usd": 30,
         "ran_estimate_usd": 20, "estimate_error_pct": 8.2, "stalls": 1,
         "metered_usd_per_merged": 21.64, "conductor_session": "unmetered"}
# NEWER as history reads it (#814): its ran-steps error under its own
# key, and estimate_error_pct the whole plan's, from the row's figures.
NEWER_READ = dict(NEWER, estimate_error_pct=-27.8667,
                  ran_estimate_error_pct=8.2)
# A row as today's writer writes it.
CURRENT = {"batch": "b3", "at": "2026-10-14T16:00:00Z", "merged": 1,
           "merged_outside": 0, "metered_usd": 12.0, "estimate_usd": 10,
           "estimate_error_pct": 20.0, "ran_estimate_usd": 12,
           "ran_estimate_error_pct": 0.0, "stalls": 1,
           "stalls_by_cause": {"ceiling": 1}, "blocked_by_cause": {},
           "conductor_session": "unmetered"}
# The first two real batches' rows, verbatim from a consumer's
# docs/factory/scorecards.jsonl: estimate_error_pct over the whole plan.
REAL = (
    '{"batch": "b20261012", "at": "2026-10-12T05:25:26Z", "items": 2,'
    ' "merged": 0, "blocked": 2, "owner_touches_per_merged": null,'
    ' "metered_usd": 9.3279, "metered_usd_per_merged": null,'
    ' "estimate_usd": 30, "estimate_error_pct": -68.907, "collisions": 0,'
    ' "stalls": 3, "escalations": 4, "review_changes_per_item": 0.0,'
    ' "start_to_last_merge_s": null, "merged_per_owner_wait_hour": 0.0,'
    ' "policy_compliance": 1.0, "conductor_session": "unmetered"}\n'
    '{"batch": "b20261013", "at": "2026-10-14T02:06:23Z", "items": 1,'
    ' "merged": 0, "blocked": 1, "owner_touches_per_merged": null,'
    ' "metered_usd": 21.6394, "metered_usd_per_merged": null,'
    ' "estimate_usd": 15, "estimate_error_pct": 44.2627, "collisions": 0,'
    ' "stalls": 3, "escalations": 3, "review_changes_per_item": 0.0,'
    ' "start_to_last_merge_s": null, "merged_per_owner_wait_hour": 0.0,'
    ' "policy_compliance": 1.0, "conductor_session": "unmetered"}\n')


def write(root, rows, extra=""):
    path = Path(root) / close.SCORECARDS
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows) + extra,
                    encoding="utf-8")


class TestHistory(unittest.TestCase):
    def test_reads_every_row_in_file_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, [OLDER, NEWER, CURRENT])
            self.assertEqual(close.history(tmp),
                             ([OLDER, NEWER_READ, CURRENT], []))

    def test_the_real_old_meaning_rows_read_as_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, [], REAL)
            rows, problems = close.history(tmp)
        self.assertEqual(problems, [])
        self.assertEqual(rows, [json.loads(line)
                                for line in REAL.splitlines()])

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
            self.assertEqual(close.append_scorecard(tmp, CURRENT), [])
            self.assertEqual(close.append_scorecard(tmp, CURRENT), [])
            self.assertEqual(close.history(tmp), ([OLDER, CURRENT], []))

    def test_a_row_of_the_wrong_shape_is_never_appended(self):
        # #814: the writer checks the shape the reader checks.
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(close.append_scorecard(
                tmp, dict(CURRENT, metered_usd=float("nan"))), [
                f"cd: not appended to {close.SCORECARDS}: metered_usd nan"
                " is not a finite number or null"])
            self.assertFalse((Path(tmp) / close.SCORECARDS).exists())

    def test_a_line_of_the_wrong_shape_fails_naming_its_line(self):
        # #814: a non-string batch crashed `scorecards` with a TypeError,
        # and NaN printed as a metric; each now fails the read.
        for line, suffix in (
                ('{"batch": 12, "merged": 1}', "batch 12 is not a non-empty"
                 " string"),
                ('{"batch": "b2", "merged": NaN}', "merged nan is not a"
                 " finite number or null")):
            with tempfile.TemporaryDirectory() as tmp:
                write(tmp, [OLDER], line + "\n")
                self.assertEqual(close.history(tmp), (None, [
                    f"cd: {close.SCORECARDS}:2 {suffix}"]), line)


class TestScorecardShape(unittest.TestCase):
    """#814: one validator for a scorecard row, which append_scorecard
    and history both apply."""

    def test_every_shape_the_file_has_held_is_clean(self):
        for row in (OLDER, NEWER, CURRENT, *map(json.loads,
                                                 REAL.splitlines())):
            self.assertEqual(close.scorecard_problems(row), [], row)

    def test_each_field_kind_is_checked(self):
        cases = [
            ([1], ["is not a scorecard row (a JSON object with a batch)"]),
            ({"merged": 1}, ["is not a scorecard row (a JSON object with a"
                             " batch)"]),
            ({"batch": ""}, ["batch '' is not a non-empty string"]),
            ({"batch": "b", "at": 3}, ["at 3 is not a non-empty string"]),
            ({"batch": "b", "merged": True},
             ["merged True is not a finite number or null"]),
            ({"batch": "b", "merged": "1"},
             ["merged '1' is not a finite number or null"]),
            ({"batch": "b", "metered_usd": float("inf")},
             ["metered_usd inf is not a finite number or null"]),
            ({"batch": "b", "stalls_by_cause": {"ceiling": -1}},
             ["stalls_by_cause {'ceiling': -1} is not a map of cause to"
              " count"]),
            ({"batch": "b", "blocked_by_cause": [1]},
             ["blocked_by_cause [1] is not a map of cause to count"])]
        for row, problems in cases:
            self.assertEqual(close.scorecard_problems(row), problems, row)


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
                "  estimate_error_pct: -68.9 -> -27.8667 (+41.0333)\n"
                "  stalls: 3 -> 1 (-2)\n"
                "  metered_usd_per_merged: - -> 21.64 (n/a)\n"
                "  ran_estimate_error_pct: - -> 8.2 (n/a)\n"
                "cd: 0 problem(s)\n")))

    def test_the_real_rows_trend_their_whole_plan_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, [], REAL)
            code, out = self.main(tmp, ["scorecards"])
        self.assertEqual(code, 0)
        self.assertIn("  estimate_error_pct: -68.907 -> 44.2627 (+113.1697)",
                      out.splitlines())

    def test_a_non_string_batch_exits_nonzero_not_a_traceback(self):
        # #814, reproduced on main: TypeError: sequence item 0: expected
        # str instance, int found.
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, [{"batch": 12, "merged": 1}])
            self.assertEqual(self.main(tmp, ["scorecards"]), (1, (
                f"cd: {close.SCORECARDS}:1 batch 12 is not a non-empty"
                " string\ncd: 1 problem(s)\n")))

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
