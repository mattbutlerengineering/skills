"""implement-queue's profile check (#1697).

Phase 0 tells a consumer which hooks its queue profile lacks, and what
each absence costs, from references/profile-migration.md. That file is a
second list of the skill's keys and hooks, so it can silently fall behind
the one place a hook is added (the skill's tables): a new hook with no
row would be exactly the stale-profile case the check exists to report.
These tests hold the two lists equal, by name and order, against the real
files.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "implement-queue" / "SKILL.md"
MIGRATION = (ROOT / "skills" / "implement-queue" / "references"
             / "profile-migration.md")

ROW = re.compile(r"^\|\s*`([a-z][a-z-_]*)`\s*\|", re.M)


def names(text, start, end):
    """Backticked first-column names of the table rows between two
    markers."""
    body = text.split(start, 1)[1].split(end, 1)[0]
    return ROW.findall(body)


class TestMigrationNamesEveryRow(unittest.TestCase):
    def setUp(self):
        self.skill = SKILL.read_text(encoding="utf-8")
        self.migration = MIGRATION.read_text(encoding="utf-8")

    def test_every_frontmatter_key_has_a_row_in_the_skills_order(self):
        skill_keys = names(self.skill, "Frontmatter keys (all optional):",
                           "Hooks (each")
        self.assertTrue(skill_keys)
        self.assertEqual(
            names(self.migration, "## Frontmatter keys", "## Hooks"),
            skill_keys)

    def test_every_hook_has_a_row_in_the_skills_order(self):
        skill_hooks = names(self.skill, "Hooks (each", "**Cloud sessions.**")
        self.assertIn("verdict", skill_hooks)
        self.assertEqual(
            names(self.migration, "## Hooks", "## What the check reports"),
            skill_hooks)


def flat(text):
    return " ".join(text.split())


def phase0(skill):
    return flat(skill.split("## Phase 0: Pre-flight", 1)[1]
                .split("## Phase 1", 1)[0])


def row(text, hook):
    """One table row's text, from its backticked name to the line end."""
    line = next(l for l in text.splitlines()
                if l.startswith(f"| `{hook}`"))
    return flat(line)


class TestPreflightJudgesTheHeadOfMain(unittest.TestCase):
    """#1710: the last five runs of anything read a red main as green
    (event-driven workflows crowd the window; a cancelled run whose gate
    job failed passes a failure-only filter). The default judges the head
    SHA of origin/main by the gate's own definition."""

    def setUp(self):
        self.skill = SKILL.read_text(encoding="utf-8")
        self.migration = MIGRATION.read_text(encoding="utf-8")
        self.step = phase0(self.skill)

    def test_the_default_is_no_longer_a_run_list_window(self):
        self.assertNotIn("--limit 5", row(self.skill, "preflight"))
        self.assertNotIn("--limit 5", row(self.migration, "preflight"))

    def test_the_step_judges_the_head_sha_of_origin_main(self):
        self.assertIn("head SHA of `origin/main`", self.step)
        self.assertIn("commits/<sha>/check-runs", self.step)

    def test_the_step_uses_the_gates_definition_of_green(self):
        self.assertIn("present and successful", self.step)
        for state in ("failure", "cancelled", "timed_out", "missing"):
            self.assertIn(state, self.step)

    def test_without_a_required_check_it_reads_push_runs_of_the_head(self):
        self.assertIn("--commit <sha> --event push", self.step)

    def test_pending_waits_and_never_claims_on_an_unproven_main(self):
        self.assertIn("pending", self.step)
        self.assertIn("unproven", self.step)

    def test_the_cloud_twins_follow_the_default(self):
        twins = flat(self.skill.split("**Cloud sessions.**", 1)[1]
                     .split("Tool names are", 1)[0])
        self.assertIn("commits/<sha>/check-runs", twins)
        self.assertIn("rerun-failed-jobs", twins)

    def test_the_migration_row_names_the_two_blind_spots(self):
        text = row(self.migration, "preflight")
        self.assertIn("crowded out", text)
        self.assertIn("event-driven", text)
        self.assertIn("cancelled run whose gate job failed", text)


class TestRedMainReRunsOnceBeforeClaiming(unittest.TestCase):
    def setUp(self):
        self.step = phase0(SKILL.read_text(encoding="utf-8"))

    def test_a_no_repo_cause_failure_is_rerun_once(self):
        self.assertIn("gh run rerun <run-id> --failed", self.step)
        self.assertLess(self.step.index("gh run rerun"),
                        self.step.index("claim or file the CI-fix issue"))

    def test_a_second_failure_claims_the_ci_fix_issue(self):
        self.assertIn("second failure", self.step)
        self.assertIn("claim or file the CI-fix issue", self.step)

    def test_a_rerun_never_declares_main_green(self):
        self.assertIn("never a way to skip CI or to declare main green", self.step)


if __name__ == "__main__":
    unittest.main()
