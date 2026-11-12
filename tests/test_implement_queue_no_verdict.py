"""implement-queue's `error` verdict has one remedy per cause (#1711).

Four causes used to share one remedy (re-dispatch the reviewer once).
A second review cannot change a missing hook, so the remedy splits by
cause; the comment's first line is defined when no hook printed one;
and the gate says whether it pays for a review when Phase 0 already
knows no verdict can be derived. Each promise is pinned to its own
sentence.
"""
import unittest

from tests.test_implement_queue_head_pin import (
    CONTRACT, MIGRATION, ROOT, SKILL, gate_step, section)
import re


def sentence(text, needle):
    """The period-delimited sentence holding `needle` (the gate's
    sentences carry colons and semicolons, so only a full stop ends one)."""
    for s in re.split(r"(?<=\.) ", text):
        if needle in s:
            return s
    return ""

REASONS = ("no verdict hook", "hook did not run", "hook exit 2",
           "reviewer timed out", "no usable score")


def flat_skill():
    return " ".join(SKILL.read_text(encoding="utf-8").split())


def migration_row(name):
    text = MIGRATION.read_text(encoding="utf-8")
    hooks = text.split("## Hooks", 1)[1].split("## What the check reports", 1)[0]
    for line in hooks.splitlines():
        if line.startswith(f"| `{name}`"):
            return " ".join(line.split())
    return ""


class TestRemedySplitsByCause(unittest.TestCase):
    def test_a_reviewer_side_error_gets_one_redispatch(self):
        s = sentence(gate_step(5), "A reviewer-side error")
        self.assertIn("timed out", s)
        self.assertIn("score is not usable", s)
        self.assertIn("one re-dispatch", s)
        self.assertIn("hold", s)

    def test_a_usable_score_is_defined_and_checked_before_the_hook(self):
        s = sentence(gate_step(5), "usable score, a bare finite number")
        self.assertIn("from 0 to 10", s)
        self.assertIn("never reaches the hook", s)

    def test_exit_two_is_hook_side_only_on_a_usable_score(self):
        s = sentence(gate_step(5), "A hook-side error")
        self.assertIn("exit 2 on a usable score", s)
        self.assertIn("wrong argument count", s)

    def test_a_hook_side_error_is_held_at_once(self):
        s = sentence(gate_step(5), "A hook-side error")
        for cause in ("missing hook", "did not run", "exit 2"):
            self.assertIn(cause, s)
        self.assertIn("no re-dispatch", s)
        self.assertIn("hold the PR for a human at once", s)

    def test_no_single_remedy_covers_every_error(self):
        step = gate_step(5)
        self.assertNotIn("is `error`: re-dispatch the reviewer once", step)

    def test_an_error_never_merges_under_auto(self):
        s = sentence(gate_step(5), "`merge: auto` an")
        self.assertIn("an `error` never merges", s)


class TestTheErrorCommentsFirstLine(unittest.TestCase):
    def test_the_form_is_defined_with_every_reason(self):
        step = gate_step(5)
        s = sentence(step, "`reviewer-verdict: error (<reason>)`")
        self.assertIn("When the hook printed no `reviewer-verdict:` line", s)
        for reason in REASONS:
            self.assertIn(f"`{reason}`", step)

    def test_the_hooks_own_line_is_still_posted_verbatim(self):
        s = sentence(gate_step(5), "first line is the line the hook printed")
        self.assertIn("verbatim", s)

    def test_the_head_line_stays_second_and_the_score_is_kept(self):
        step = gate_step(5)
        self.assertIn("second line is `Head: <sha>`", step)
        s = sentence(step, "findings")
        self.assertIn("score", s)


class TestNoVerdictHookSkipsTheReview(unittest.TestCase):
    def test_step_four_does_not_run_without_a_hook(self):
        s = sentence(gate_step(4), "no `verdict` hook")
        self.assertIn("Phase 0", s)
        self.assertIn("not on the fast path", s)
        self.assertIn("dispatch no reviewer", s)
        self.assertIn("unreviewed", s)
        self.assertIn("held for a human", s)

    def test_the_skipped_pr_never_merges(self):
        s = sentence(gate_step(4), "That PR never merges")
        self.assertIn("under any `merge` setting", s)
        self.assertIn("no `verdict` hook", gate_step(4))

    def test_the_fast_path_is_unaffected(self):
        s = sentence(gate_step(4), "A fast-path PR")
        self.assertIn("unaffected", s)

    def test_phase_zero_points_at_the_gate_rule(self):
        s = sentence(section(SKILL, "Phase 0: Pre-flight"), "predates `verdict`")
        self.assertIn("unreviewed", s)
        self.assertIn("gate step 4", s)


class TestMigrationRowAgrees(unittest.TestCase):
    def test_the_row_says_no_review_runs_and_nothing_merges(self):
        row = migration_row("verdict")
        self.assertIn("unreviewed", row)
        self.assertIn("nothing merges", row)
        self.assertIn("even under `merge: auto`", row)
        self.assertNotIn("An `error` verdict on every reviewed PR", row)

    def test_the_contract_splits_the_remedy_too(self):
        s = sentence(CONTRACT.read_text(encoding="utf-8").replace("\n", " "),
                     "Errors are not passes")
        self.assertNotIn("re-dispatch once, then hold", s)


class TestRestatements(unittest.TestCase):
    def _flat(self, *parts):
        return " ".join(ROOT.joinpath(*parts).read_text(encoding="utf-8").split())

    def _split(self, text):
        hook = sentence(text, "hook-side")
        rev = sentence(text, "reviewer-side")
        self.assertIn("held", hook)
        self.assertTrue("at once" in hook, hook)
        self.assertIn("no re-dispatch", hook)
        self.assertIn("exit 2 on a usable score", hook)
        self.assertIn("re-dispatched once", rev)
        self.assertIn("from 0 to 10", rev)

    def test_the_repo_profile_splits_the_remedy(self):
        self._split(self._flat(".claude", "implement-queue.md"))

    def test_the_contract_splits_the_remedy(self):
        self._split(self._flat("skills", "implement-queue", "references",
                               "reviewer-contract.md"))

    def test_the_hourly_routine_splits_the_remedy(self):
        text = self._flat("docs", "factory", "hourly-improvement-routine.md")
        rev = sentence(text, "A reviewer-side error")
        self.assertIn("re-dispatched once and then held", rev)
        self.assertIn("from 0 to 10", rev)
        hook = sentence(text, "a hook-side one")
        self.assertIn("is held at once", hook)
        self.assertIn("exit 2 on a usable score", hook)
        self.assertNotIn("An error or timeout is `error`", text)


class TestFastPathStaysOpenAndTheReportSaysSo(unittest.TestCase):
    def test_the_fast_path_stays_open_without_a_hook(self):
        s = sentence(gate_step(4), "A fast-path PR")
        self.assertIn("fast path stays open", s)
        self.assertIn("ADR-0088", s)
        self.assertIn("can still merge", s)

    def test_the_report_says_every_merge_was_unreviewed(self):
        s = sentence(section(SKILL, "Phase 4: Loop or stop"),
                     "with no `verdict` hook under `merge: auto`")
        self.assertIn("every merge in the run took the fast path unreviewed", s)

    def test_the_fast_path_statement_is_made_once(self):
        self.assertEqual(flat_skill().count("fast path stays open"), 1)


class TestNoCopyStillClaimsEveryPrIsReviewed(unittest.TestCase):
    def test_the_hook_table_row_is_qualified(self):
        line = next(l for l in SKILL.read_text(encoding="utf-8").splitlines()
                    if l.startswith("| `fast-path`"))
        self.assertIn("no `verdict` hook", line)
        self.assertIn("unreviewed", line)

    def test_the_migration_row_is_qualified(self):
        row = migration_row("fast-path")
        self.assertIn("no `verdict` hook", row)
        self.assertIn("held unreviewed", row)

    def test_the_description_is_qualified(self):
        desc = next(l for l in SKILL.read_text(encoding="utf-8").splitlines()
                    if l.startswith("description:"))
        s = sentence(desc, "a review by a distinct agent")
        self.assertIn("held unreviewed when the profile has no `verdict` hook", s)


if __name__ == "__main__":
    unittest.main()
