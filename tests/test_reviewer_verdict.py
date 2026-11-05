"""reviewer_verdict.py — the one owner of the implement-queue reviewer's
pass threshold (ADR-0123).

`derive` is pure: a score 0 to 10 gives `pass` or `flag`, anything
unusable gives an `error` problem string. `main` is the queue profile's
`verdict` hook: one line, exit 0 pass, 1 flag, 2 error.
"""
import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import reviewer_verdict  # noqa: E402


def run(argv):
    out = io.StringIO()
    with redirect_stdout(out):
        code = reviewer_verdict.main(argv)
    return code, out.getvalue()


class DeriveTest(unittest.TestCase):
    def test_whole_scores(self):
        for score in range(0, 11):
            with self.subTest(score=score):
                want = "flag" if score <= 6 else "pass"
                self.assertEqual(reviewer_verdict.derive(score),
                                 (want, score))

    def test_fraction_below_the_line_flags(self):
        self.assertEqual(reviewer_verdict.derive(6.5), ("flag", 6.5))

    def test_numeric_string_derives_like_the_number(self):
        self.assertEqual(reviewer_verdict.derive("8"), ("pass", 8))
        self.assertEqual(reviewer_verdict.derive("5"), ("flag", 5))

    def test_unusable_scores_are_errors(self):
        for bad in (None, "", "high", float("nan"), float("inf"),
                    float("-inf"), -1, 10.5, 11, 10 ** 400, True, False, [], {}):
            with self.subTest(score=bad):
                verdict, detail = reviewer_verdict.derive(bad)
                self.assertEqual(verdict, "error")
                self.assertTrue(detail.startswith("reviewer-verdict:"),
                                detail)


class MainTest(unittest.TestCase):
    def test_pass(self):
        self.assertEqual(run(["8"]),
                         (0, "reviewer-verdict: pass (score 8/10)\n"))

    def test_flag(self):
        self.assertEqual(run(["5"]),
                         (1, "reviewer-verdict: flag (score 5/10)\n"))

    def test_error(self):
        code, out = run(["nope"])
        self.assertEqual(code, 2)
        self.assertTrue(out.startswith("reviewer-verdict: error ("), out)
        self.assertEqual(len(out.splitlines()), 1)

    def test_wrong_argument_count_is_usage(self):
        for argv in ([], ["7", "8"]):
            with self.subTest(argv=argv):
                code, out = run(argv)
                self.assertEqual(code, 2)
                self.assertTrue(out.startswith("usage: python3 "
                                               "reviewer_verdict.py"), out)


if __name__ == "__main__":
    unittest.main()
