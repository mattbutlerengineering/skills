"""eval_trends.py render and main — the printed view, line by line.

Companion to tests/test_eval_trends.py (core and adapters; split to keep
each file under the size limit). Every number in an expected line is
recomputed here from the fixture files the test wrote, with a Wilson
closed form that is deliberately not the tool's centre-and-half-width
form. Fixture trees are temp directories; no test calls a model, the
claude CLI or the network.
"""
import contextlib
import hashlib
import io
import math
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import eval_trends  # noqa: E402
import eval_trends_fixture as fx  # noqa: E402

Z = 1.96
SOURCE = Path(eval_trends.__file__)
HEADER = ("eval-trends: descriptive only; a REFUSED line means the records "
          "cannot support a trend claim, not that nothing changed")
NOT_COMPUTED = (
    "eval-trends: not computed from any record: judge drift, contamination,"
    " saturation, flake rate; see docs/research/"
    "eval-quality-metrics-2026-10-21.md")
SIGNALS_REFUSED = ("eval-trends: REFUSED decompose-signals: not an eval run:"
                   " records re-measure one git history; no trend claim")


def interval(h, n):
    """Wilson 95 percent as fractions: the closed form
    (2h + z*z -/+ z*sqrt(z*z + 4h(1 - h/n))) / (2(n + z*z))."""
    root = Z * math.sqrt(Z * Z + 4 * h * (1 - h / n))
    return ((2 * h + Z * Z - root) / (2 * (n + Z * Z)),
            (2 * h + Z * Z + root) / (2 * (n + Z * Z)))


def pct(x):
    return f"{x * 100:.1f}"


def one_day(h, n):
    lo, hi = interval(h, n)
    return f"{h}/{n} ({pct(h / n)}%, 95% {pct(lo)}-{pct(hi)}%)"


def hex_of(case_set):
    return hashlib.sha256(
        repr(tuple(sorted(case_set))).encode("utf-8")).hexdigest()[:8]


def trigger_set(count, prefix="c"):
    return tuple((f"{prefix}{i}", "idea", f"query {prefix}{i}")
                 for i in range(count))


class RenderCase(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="eval-trends-render-"))
        self.addCleanup(shutil.rmtree, self.root)

    def trigger(self, date, count, passed, suffix="", prefix="c", **kw):
        name = f"trigger-{date}{suffix}.json"
        fx.write_json(self.root, f"evals/results/{name}",
                      fx.trigger_record(
                          date, fx.numbered_cases(count, passed, prefix),
                          **kw))
        return name

    def plugin(self, name, started, count, passed, cost, tags=("next",)):
        cases = [(f"case{i}", "prompt", [("g", "md")]) for i in range(count)]
        fx.write_json(self.root, f"plugin-evals/records/{name}",
                      fx.plugin_record(started, cases, tags=tags, cost=cost,
                                       passed=passed))
        return name

    def run_main(self, argv=None):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = eval_trends.main([str(self.root)] if argv is None
                                    else argv)
        return code, out.getvalue().splitlines()

    def refused(self, lines, surface):
        return [ln for ln in lines
                if ln.startswith(f"eval-trends: REFUSED {surface}:")]


class TestDemo(RenderCase):
    """The PRD demo: one surface with a comparable pair, one without."""

    def setUp(self):
        super().setUp()
        self.t1 = self.trigger("2026-07-01", 30, 12)
        self.t2 = self.trigger("2026-07-05", 30, 24)
        self.p1 = self.plugin("2026-07-01.json", "2026-07-01T10:00:00Z",
                              30, 15, 3.0)
        self.p2 = self.plugin("2026-07-05.json", "2026-07-05T10:00:00Z",
                              30, 24, 3.6)
        fx.write_json(self.root, "evals/results/charter-2026-09-28.json",
                      fx.charter_record("2026-09-28",
                                        [("a", "swe", "sensitive")] * 4))
        self.code, self.lines = self.run_main()

    def test_exit_zero_and_the_line_order(self):
        self.assertEqual(self.code, 0)
        self.assertEqual(self.lines[0], HEADER)
        self.assertEqual(self.lines[-2], NOT_COMPUTED)
        self.assertEqual(self.lines[-1], "eval-trends: 0 problem(s)")
        inventory = [i for i, ln in enumerate(self.lines)
                     if re.match(r"eval-trends: [a-z-]+: \d+ record", ln)]
        self.assertEqual(inventory, [1, 2, 3, 4, 5])

    def test_inventory_lines(self):
        self.assertEqual(self.lines[1:6], [
            "eval-trends: trigger: 2 record(s), 2026-07-01..2026-07-05, "
            "2 day(s), cases 30-30 per record",
            "eval-trends: charter: 1 record(s), 2026-09-28..2026-09-28, "
            "1 day(s), cases 4-4 per record",
            "eval-trends: output: 0 record(s)",
            "eval-trends: plugin: 2 record(s), 2026-07-01..2026-07-05, "
            "2 day(s), cases 30-30 per record",
            "eval-trends: decompose-signals: 0 record(s)"])

    def test_the_trend_line_recomputes_from_the_fixture_files(self):
        suite = "claude,m,3,0.5"
        want = (f"eval-trends: trigger trend set "
                f"{hex_of(trigger_set(30))} suite {suite}: "
                f"2026-07-01 {one_day(12, 30)} -> 2026-07-05 "
                f"{one_day(24, 30)}; intervals do not overlap "
                f"({self.t1}, {self.t2})")
        self.assertIn(want, self.lines)

    def test_the_cost_per_pass_line(self):
        # 3.0 / 15 passed = 0.2000; 3.6 / 24 passed = 0.1500
        self.assertIn(
            f"eval-trends: plugin cost per pass: 2026-07-01 $0.2000 -> "
            f"2026-07-05 $0.1500 ({self.p1}, {self.p2})", self.lines)

    def test_the_trigger_cost_line_is_refused_because_no_field_exists(self):
        self.assertIn("eval-trends: trigger cost: REFUSED cost field absent"
                      " from 2 of 2 record(s); no trend claim", self.lines)

    def test_the_surface_without_a_pair_is_refused_with_need_and_have(self):
        self.assertEqual(self.refused(self.lines, "charter"), [
            "eval-trends: REFUSED charter: too few records: need 2, "
            "have 1; no trend claim"])
        self.assertEqual(self.refused(self.lines, "output"), [
            "eval-trends: REFUSED output: too few records: need 2, "
            "have 0; no trend claim"])

    def test_signals_are_always_refused_as_not_an_eval_run(self):
        self.assertIn(SIGNALS_REFUSED, self.lines)


class TestVerdictWording(RenderCase):
    def verdict_of(self, first, second):
        self.trigger("2026-07-01", 30, first)
        self.trigger("2026-07-05", 30, second)
        _, lines = self.run_main()
        (trend,) = [ln for ln in lines if " trigger trend set " in ln]
        return trend

    def test_separating_intervals(self):
        self.assertIn("; intervals do not overlap (", self.verdict_of(6, 27))

    def test_overlapping_intervals(self):
        trend = self.verdict_of(15, 18)
        self.assertIn("; intervals overlap: not distinguishable "
                      "(descriptive, not a significance test) (", trend)

    def test_the_words_improved_and_regressed_never_print(self):
        for first, second in ((6, 27), (27, 6), (15, 18)):
            for ln in self.run_fresh(first, second):
                self.assertNotRegex(ln.lower(), r"improved|regressed")

    def run_fresh(self, first, second):
        shutil.rmtree(self.root / "evals", ignore_errors=True)
        self.trigger("2026-07-01", 30, first)
        self.trigger("2026-07-05", 30, second)
        return self.run_main()[1]


class TestRefusalStates(RenderCase):
    def test_different_suites(self):
        self.trigger("2026-07-01", 30, 10, model="m1")
        self.trigger("2026-07-05", 30, 20, model="m2")
        _, lines = self.run_main()
        self.assertEqual(self.refused(lines, "trigger"), [
            "eval-trends: REFUSED trigger: different suites: 2 record(s) "
            "share no suite with another record; no trend claim"])
        self.assertFalse([ln for ln in lines if "trend set" in ln])

    def test_case_sets_differ(self):
        self.trigger("2026-07-01", 30, 10, prefix="a")
        self.trigger("2026-07-05", 30, 20, prefix="b")
        _, lines = self.run_main()
        self.assertEqual(self.refused(lines, "trigger"), [
            "eval-trends: REFUSED trigger: case sets differ: 2 record(s) "
            "share a suite with another record but not its case set; no "
            "trend claim"])

    def test_only_same_day_records_with_a_rerun_spread(self):
        a = self.trigger("2026-07-05", 30, 12)
        b = self.trigger("2026-07-05", 30, 15, suffix="-2")
        _, lines = self.run_main()
        self.assertEqual(self.refused(lines, "trigger"), [
            "eval-trends: REFUSED trigger: only same-day records: 2 "
            "record(s) in 1 group(s), each on one day; no trend claim"])
        self.assertIn(
            f"eval-trends: trigger rerun spread 2026-07-05 set "
            f"{hex_of(trigger_set(30))}: passed 12..15 of 30 over 2 "
            f"run(s) ({a}, {b})", lines)
        self.assertFalse([ln for ln in lines if "trend set" in ln])

    def test_too_few_cases(self):
        self.trigger("2026-07-01", 29, 10)
        self.trigger("2026-07-05", 29, 20)
        _, lines = self.run_main()
        self.assertEqual(self.refused(lines, "trigger"), [
            "eval-trends: REFUSED trigger: too few cases: need 30, have 29"
            " in 2 record(s) over 2+ days; no trend claim"])

    def test_the_cost_refusal_names_the_records_that_lack_it(self):
        self.plugin("2026-07-01.json", "2026-07-01T10:00:00Z", 30, 15, 3.0)
        data = fx.plugin_record(
            "2026-07-05T10:00:00Z",
            [(f"case{i}", "prompt", [("g", "md")]) for i in range(30)],
            passed=20)
        del data["costUsd"]
        fx.write_json(self.root, "plugin-evals/records/2026-07-05.json", data)
        _, lines = self.run_main()
        self.assertIn("eval-trends: plugin cost: REFUSED cost field absent"
                      " from 1 of 2 record(s); no trend claim", lines)

    def test_refused_counts_sum_to_the_inventory_count(self):
        self.trigger("2026-07-01", 4, 1)
        self.trigger("2026-07-02", 4, 2)
        self.trigger("2026-07-05", 30, 12)
        self.trigger("2026-07-05", 30, 15, suffix="-2")
        self.trigger("2026-07-06", 5, 5, prefix="z", model="other")
        self.trigger("2026-07-07", 5, 5, prefix="y")
        _, lines = self.run_main()
        counts = [int(m.group(1)) for ln in self.refused(lines, "trigger")
                  for m in [re.search(r"(?:: | in )(\d+) record\(s\)", ln)]
                  if m]
        self.assertEqual(sum(counts), 6)
        (inv,) = [ln for ln in lines if ln.startswith("eval-trends: trigger:")]
        self.assertIn("6 record(s)", inv)


class TestRerunsBesideAnotherDay(RenderCase):
    def test_days_are_compared_by_hull_with_the_rate_range(self):
        a = self.trigger("2026-07-01", 30, 12)
        b = self.trigger("2026-07-05", 30, 24)
        c = self.trigger("2026-07-05", 30, 27, suffix="-2")
        _, lines = self.run_main()
        lo = interval(24, 30)[0]
        hi = interval(27, 30)[1]
        day2 = (f"24..27/30 ({pct(24 / 30)}..{pct(27 / 30)}%, "
                f"95% {pct(lo)}-{pct(hi)}%)")
        self.assertIn(
            f"eval-trends: trigger trend set {hex_of(trigger_set(30))} "
            f"suite claude,m,3,0.5: 2026-07-01 {one_day(12, 30)} -> "
            f"2026-07-05 {day2}; intervals do not overlap ({a}, {b}, {c})",
            lines)
        self.assertIn(
            f"eval-trends: trigger rerun spread 2026-07-05 set "
            f"{hex_of(trigger_set(30))}: passed 24..27 of 30 over 2 "
            f"run(s) ({b}, {c})", lines)


class TestCharterMetricLabel(RenderCase):
    """A charter's metric is `sensitive` verdicts, never a pass rate."""

    def charter(self, date, count, sensitive, suffix=""):
        results = [(f"id{i}", "swe",
                    "sensitive" if i < sensitive else "insensitive")
                   for i in range(count)]
        name = f"charter-{date}{suffix}.json"
        fx.write_json(self.root, f"evals/results/{name}",
                      fx.charter_record(date, results))
        return name

    def test_the_spread_line_says_sensitive_not_passed(self):
        a = self.charter("2026-09-28", 4, 1)
        b = self.charter("2026-09-28", 4, 3, suffix="-2")
        _, lines = self.run_main()
        case_set = tuple((f"id{i}", "swe") for i in range(4))
        self.assertIn(
            f"eval-trends: charter rerun spread 2026-09-28 set "
            f"{hex_of(case_set)}: sensitive 1..3 of 4 over 2 run(s) "
            f"({a}, {b})", lines)

    def test_the_trend_line_says_sensitive_not_passed(self):
        a = self.charter("2026-09-28", 30, 10)
        b = self.charter("2026-10-02", 30, 25)
        _, lines = self.run_main()
        (trend,) = [ln for ln in lines if " charter trend set " in ln]
        want = (f"2026-09-28 10/30 sensitive ({pct(10 / 30)}%, 95% "
                f"{pct(interval(10, 30)[0])}-{pct(interval(10, 30)[1])}%)")
        self.assertIn(want, trend)
        self.assertNotIn("passed", trend)


class TestProblemsAndExitCodes(RenderCase):
    def test_a_malformed_record_prints_before_the_summary_and_exits_one(self):
        self.trigger("2026-07-01", 30, 12)
        bad = fx.trigger_record("2026-07-05", fx.numbered_cases(3, 1))
        bad["summary"]["passed"] = 3
        fx.write_json(self.root, "evals/results/trigger-2026-07-05.json",
                      bad)
        code, lines = self.run_main()
        self.assertEqual(code, 1)
        problem = ("eval-trends: evals/results/trigger-2026-07-05.json "
                   "summary disagrees with its results")
        self.assertEqual(lines[-2:], [problem, "eval-trends: 1 problem(s)"])
        self.assertIn("eval-trends: trigger: 1 record(s), 2026-07-01.."
                      "2026-07-01, 1 day(s), cases 30-30 per record", lines)

    def test_a_malformed_record_on_every_surface_is_a_problem_each(self):
        fx.write_json(self.root, "evals/results/trigger-2026-07-05.json", [])
        fx.write_json(self.root, "evals/results/charter-2026-07-05.json", [])
        fx.write_json(self.root, "evals/results/output/x-2026-07-05/"
                      "grading.json", [])
        fx.write_json(self.root, "plugin-evals/records/a.json", [])
        fx.write_json(self.root, "evals/results/decompose-signals-"
                      "2026-07-05.json", [])
        code, lines = self.run_main()
        self.assertEqual(code, 1)
        self.assertEqual(lines[-1], "eval-trends: 5 problem(s)")

    def test_usage_errors_exit_two(self):
        for argv in (["a", "b"], ["--record"], [str(self.root / "nope")]):
            with self.subTest(argv=argv):
                code, lines = self.run_main(argv)
                self.assertEqual(code, 2)
                self.assertTrue(lines[0].startswith("eval-trends: "))
                self.assertIn("python3 eval_trends.py [<repo-root>]",
                              "\n".join(lines))

    def test_a_refusal_alone_exits_zero(self):
        self.trigger("2026-07-01", 4, 1)
        code, _ = self.run_main()
        self.assertEqual(code, 0)


class TestFactoryVerb(RenderCase):
    def test_the_verb_prints_what_the_module_prints(self):
        import factory
        self.trigger("2026-07-01", 30, 12)
        self.trigger("2026-07-05", 30, 24)
        _, direct = self.run_main()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = factory.main(["eval-trends", str(self.root)])
        self.assertEqual((code, out.getvalue().splitlines()), (0, direct))


class TestReadOnly(RenderCase):
    def snapshot(self):
        return {p.relative_to(self.root).as_posix(): p.read_bytes()
                for p in sorted(self.root.rglob("*")) if p.is_file()} | {
                    p.relative_to(self.root).as_posix() + "/": b""
                    for p in sorted(self.root.rglob("*")) if p.is_dir()}

    def test_main_leaves_the_tree_byte_for_byte_identical(self):
        self.trigger("2026-07-01", 30, 12)
        self.trigger("2026-07-05", 30, 24)
        self.plugin("2026-07-01.json", "2026-07-01T10:00:00Z", 3, 2, 1.0)
        fx.write_json(self.root, "evals/results/charter-2026-09-28.json",
                      fx.charter_record("2026-09-28", [("a", "swe", "x")]))
        before = self.snapshot()
        self.run_main()
        self.assertEqual(self.snapshot(), before)

    def test_the_source_has_no_write_model_or_network_call(self):
        source = SOURCE.read_text(encoding="utf-8")
        for token in ("open(", "write_text", "write_bytes", ".mkdir",
                      "os.replace", "claude", "socket", "urllib",
                      "subprocess", "unlink", "rmtree"):
            with self.subTest(token=token):
                self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
