"""The Operate population (issue #944, ADR-0102): a retro counts the
people it observed, and a run is complete only once it has.

Three consumer retros closed their runs with no one observed and no
line saying so; one graded eleven of its own Review deferrals as
post-ship feedback. Now retro.md frontmatter carries a population line
— `users-observed: <N>` (0 is a valid count) and `signal-source:` —
and Operate completes on it, the way Ship completes on `outcome:`
(ADR-0101): a retro with the line counts, a retro with a placeholder,
a bad count or a count without a source leaves Operate pending, and a
retro with neither field predates the line and still counts.

Two halves. The predicate, pinned through next_stage, stage_states and
the board on temp run directories (the fixture trees under
tests/fixtures/ pin the new rows of both tables the way every other
row is pinned). And the recitals: the protocol doc owns the line, the
zero-user vocabulary and the run's-own-debt test once; operate, next
and autorun point at it.
"""
import tempfile
import unittest
from pathlib import Path

import board
import protocol
from protocol import RETRO_POPULATION_FIELDS, next_stage, stage_states

REPO_ROOT = Path(__file__).resolve().parent.parent
PROTOCOL_DOC = REPO_ROOT / "docs" / "pipeline-protocol.md"

HEADING = "The Operate population"
UPSTREAM = ("idea.md", "prd.md", "architecture.md", "verification.md",
            "review.md", "release.md")


def feature_run(tmp, retro_frontmatter, upstream=UPSTREAM):
    """A feature run with the given artifacts through Ship, a checked
    breakdown, and a retro.md carrying the extra frontmatter lines
    (None for no retro.md)."""
    run = Path(tmp)
    for name in upstream:
        (run / name).write_text(
            f"---\nstage: x\nrun: feature:t\ndate: 2026-07-01\n"
            f"{'ux: not-applicable' if name == 'prd.md' else ''}\n---\n",
            encoding="utf-8")
    if "architecture.md" in upstream:
        (run / "breakdown.md").write_text("- [x] one\n", encoding="utf-8")
    if retro_frontmatter is not None:
        (run / "retro.md").write_text(
            "---\nstage: operate\nrun: feature:t\ndate: 2026-07-09\n"
            + retro_frontmatter + "---\n\n# Retro\n", encoding="utf-8")
    return run


class TestOperateCompletesOnThePopulationLine(unittest.TestCase):
    def test_the_two_fields_are_the_line(self):
        self.assertEqual(RETRO_POPULATION_FIELDS,
                         ("users-observed", "signal-source"))

    def test_a_counted_population_completes_the_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = feature_run(tmp, "users-observed: 7\n"
                                   "signal-source: support inbox\n")
            self.assertEqual(next_stage(run), "complete")

    def test_zero_is_a_valid_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = feature_run(tmp, "users-observed: 0\n"
                                   "signal-source: none yet\n")
            self.assertEqual(next_stage(run), "complete")

    def test_a_template_placeholder_leaves_operate_pending(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = feature_run(tmp, "users-observed: <N>\n"
                                   "signal-source: <where>\n")
            self.assertEqual(next_stage(run), "operate")

    def test_a_negative_or_non_integer_count_leaves_operate_pending(self):
        for count in ("-1", "three", "3.5", "", "²"):
            with self.subTest(count=count), \
                    tempfile.TemporaryDirectory() as tmp:
                run = feature_run(tmp, f"users-observed: {count}\n"
                                       "signal-source: analytics\n")
                self.assertEqual(next_stage(run), "operate")

    def test_a_count_without_a_source_leaves_operate_pending(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = feature_run(tmp, "users-observed: 3\n")
            self.assertEqual(next_stage(run), "operate")

    def test_a_source_without_a_count_leaves_operate_pending(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = feature_run(tmp, "signal-source: analytics\n")
            self.assertEqual(next_stage(run), "operate")

    def test_a_retro_with_neither_field_still_completes_the_run(self):
        # Every retro written before the line existed — a dozen in this
        # repo alone — would otherwise reopen as an active run and run
        # discovery would list them all. ADR-0102 keeps them complete.
        with tempfile.TemporaryDirectory() as tmp:
            run = feature_run(tmp, "")
            self.assertEqual(next_stage(run), "complete")

    def test_a_retro_with_no_frontmatter_at_all_is_legacy_too(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = feature_run(tmp, None)
            (run / "retro.md").write_text("# Retro\n", encoding="utf-8")
            self.assertEqual(next_stage(run), "complete")

    def test_an_unpopulated_retro_outranks_an_earlier_gap(self):
        # retro.md still dominates orientation: the thing to do is add
        # the line, not backfill the gap, so next is Operate.
        with tempfile.TemporaryDirectory() as tmp:
            run = feature_run(tmp, "users-observed: <N>\n",
                              upstream=("idea.md",))
            self.assertEqual(next_stage(run), "operate")
            states = dict(stage_states(run))
            self.assertEqual(states["operate"], "current")
            self.assertEqual(states["prd"], "ahead")

    def test_a_populated_retro_still_outranks_an_earlier_gap(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = feature_run(tmp, "users-observed: 2\nsignal-source: us\n",
                              upstream=("idea.md",))
            self.assertEqual(next_stage(run), "complete")
            self.assertNotIn("current", dict(stage_states(run)).values())


class TestMaintenanceOperateCompletesOnThePopulationLine(unittest.TestCase):
    def maintenance_run(self, tmp, retro_frontmatter):
        run = Path(tmp) / "docs" / "fixes" / "login-timeout"
        run.mkdir(parents=True)
        (run / "defect.md").write_text(
            "---\nstage: capture\nrun: maintenance:login-timeout\n"
            "date: 2026-07-01\nre-entry: implement\n---\n\n- [x] fix\n",
            encoding="utf-8")
        for name in ("verification.md", "review.md", "release.md"):
            (run / name).write_text("---\nstage: x\n---\n", encoding="utf-8")
        (run / "retro.md").write_text(
            "---\nstage: operate\n" + retro_frontmatter + "---\n",
            encoding="utf-8")
        return run

    def test_a_placeholder_leaves_a_maintenance_run_at_operate(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = self.maintenance_run(tmp, "users-observed: <N>\n"
                                            "signal-source: <where>\n")
            self.assertEqual(next_stage(run), "operate")

    def test_zero_completes_a_maintenance_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = self.maintenance_run(tmp, "users-observed: 0\n"
                                            "signal-source: none\n")
            self.assertEqual(next_stage(run), "complete")


class TestTheBoardFollowsOrientation(unittest.TestCase):
    """board.py decided "complete" by retro.md's existence on its own;
    it now asks orientation, so an unpopulated retro is an active run
    at Operate on the board and a populated one appears nowhere."""

    def board_runs(self, retro_frontmatter):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run = root / "docs" / "features" / "t"
            run.mkdir(parents=True)
            feature_run(run, retro_frontmatter)
            model, problems = board.gather(root, clock=lambda: _Clock())
            self.assertEqual(problems, [])
            return model["runs"]

    def test_an_unpopulated_retro_is_an_active_run_at_operate(self):
        runs = self.board_runs("users-observed: <N>\nsignal-source: <w>\n")
        self.assertEqual([run["slug"] for run in runs], ["t"])
        ladder = dict((row["stage"], row["state"])
                      for row in runs[0]["ladder"])
        self.assertEqual(ladder["operate"], "current")

    def test_a_populated_retro_appears_nowhere(self):
        self.assertEqual(self.board_runs("users-observed: 0\n"
                                         "signal-source: none\n"), [])

    def test_a_legacy_retro_appears_nowhere(self):
        self.assertEqual(self.board_runs(""), [])


class _Clock:
    def isoformat(self, timespec="seconds"):
        return "2026-07-09T00:00:00+00:00"


def flat(text):
    """Whitespace-normalized lower case: every document here is
    hard-wrapped near 72 columns, so a phrase lands across a line break
    routinely, and a raw substring test would pin the wrapping."""
    return " ".join(text.lower().split())


def section(text, heading):
    """The body of the `### heading` subsection, up to the next heading
    of the same or a higher level."""
    lines = text.splitlines()
    start = lines.index(f"### {heading}") + 1
    body = []
    for line in lines[start:]:
        if line.startswith("## ") or line.startswith("### "):
            break
        body.append(line)
    return "\n".join(body)


def skill_text(slug):
    return protocol.skill_path(REPO_ROOT, slug).read_text(encoding="utf-8")


def template_text(slug):
    return (protocol.skill_path(REPO_ROOT, slug).parent
            / "TEMPLATE.md").read_text(encoding="utf-8")


class TestProtocolStatesThePopulation(unittest.TestCase):
    def setUp(self):
        self.doc = PROTOCOL_DOC.read_text(encoding="utf-8")
        self.body = flat(section(self.doc, HEADING))

    def test_it_states_the_line_and_that_zero_is_valid(self):
        for field in RETRO_POPULATION_FIELDS:
            with self.subTest(field=field):
                self.assertIn(f"`{field}:`", self.body)
        self.assertIn("`0` is a valid count", self.body)

    def test_zero_changes_the_verdict_vocabulary(self):
        self.assertIn("`unobserved`", self.body)
        self.assertIn("nothing is landing", self.body)

    def test_it_states_the_runs_own_debt_test(self):
        self.assertIn("the run's own", self.body)
        self.assertIn("before the run's merge", self.body)
        self.assertIn("deferred from the review stage", self.body)
        self.assertIn("`review.md`", self.body)
        self.assertIn("never counted as feedback", self.body)

    def test_it_names_the_completion_rule_and_the_legacy_reading(self):
        self.assertIn("leaves operate pending", self.body)
        self.assertIn("neither field", self.body)

    def test_it_names_its_reciters(self):
        for slug in ("operate", "next", "autorun"):
            with self.subTest(skill=slug):
                self.assertIn(f"`{slug}`", self.body)

    def test_both_operate_rows_and_run_discovery_point_here(self):
        rows = [line for line in self.doc.splitlines()
                if line.startswith("| Operate |")]
        self.assertEqual(len(rows), 2)
        for row in rows:
            self.assertIn("`users-observed:`", row)
        discovery = flat(self.doc[self.doc.index("**Run discovery:**"):
                                  self.doc.index("### Work already")])
        self.assertIn("population line", discovery)


class TestSkillsRecite(unittest.TestCase):
    def test_each_reciter_names_the_section(self):
        for slug in ("operate", "next", "autorun"):
            with self.subTest(skill=slug):
                self.assertIn(HEADING.lower(), flat(skill_text(slug)))

    def test_the_operate_template_carries_the_line_and_the_debt(self):
        text = template_text("operate")
        frontmatter = text[:text.index("---", 4)]
        for field in RETRO_POPULATION_FIELDS:
            with self.subTest(field=field):
                self.assertIn(f"\n{field}:", frontmatter)
        self.assertIn("## Open debt", text)
        self.assertIn("unobserved", text)

    def test_operate_counts_first_and_lists_debt_never_feedback(self):
        text = flat(skill_text("operate"))
        self.assertIn("`users-observed:`", text)
        self.assertIn("`unobserved`", text)
        self.assertIn("open debt", text)
        self.assertIn("never counted as feedback", text)

    def test_next_treats_an_unpopulated_retro_as_operate(self):
        text = flat(skill_text("next"))
        self.assertIn("`users-observed:` field in `retro.md`", text)
        self.assertIn("population line", text)

    def test_the_autorun_brief_has_an_operate_section(self):
        text = flat(skill_text("autorun"))
        self.assertIn("`operate:`", text)
        for answer in ("`wait:", "`minimum-signal:", "`skip`"):
            with self.subTest(answer=answer):
                self.assertIn(answer, text)
        self.assertIn("never ship's authorization", text)


if __name__ == "__main__":
    unittest.main()
