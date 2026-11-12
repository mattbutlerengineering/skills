"""implement-queue's worker brief and outcome table (#1716).

Four workers exposed gaps: a machine-wide kill and shared-git commands,
"no repo fix exists" recorded as a failure, no line saying an evidence
comment is a valid result, no wall-clock bound, empty worktrees never
reclaimed, and "gates green" covering only local checks. Each promise is
pinned to its own sentence, the state of the evidence outcome to its own
row, and each clause of a two-clause rule to its own remedy.
"""
import re
import unittest

from tests.test_implement_queue_head_pin import ROOT, SKILL, section
from tests.test_implement_queue_no_verdict import sentence

WORK_ORDERS = ROOT / "skills" / "implement-queue" / "references" / "work-orders.md"


def phase2():
    return section(SKILL, "Phase 2: Implement, then gate")


def brief_item(number, text=None):
    """The flattened text of one numbered item of the Worker brief."""
    if text is None:
        text = phase2().split("### Worker brief", 1)[1].split(
            "When a worker finishes", 1)[0]
    m = re.search(rf"(?:^| ){number}\. (.*?)(?= \d+\. |\Z)", text)
    return m.group(1) if m else ""


def outcome_rows():
    rows = {}
    block = phase2().split("When a worker finishes", 1)[1].split(
        "Then run the `telemetry`", 1)[0]
    for cell in re.findall(r"\| ([^|]+?) +\| (`[^`]+`) +\|", block):
        rows[cell[0].strip()] = cell[1]
    return rows


def after_table():
    return phase2().split("Then run the `telemetry`", 1)[1]


def phase4():
    return section(SKILL, "Phase 4: Loop or stop")


class TestTheBriefKeepsAWorkerInsideItsWorktree(unittest.TestCase):
    def test_processes_are_stopped_by_pid_only(self):
        s = sentence(brief_item(8), "Stop only processes you started")
        self.assertIn("by PID", s)
        self.assertIn("`pkill -f`", s)
        self.assertIn("`killall`", s)

    def test_shared_git_commands_are_forbidden(self):
        s = sentence(brief_item(8), "Never run `git stash`")
        for cmd in ("`git gc`", "`git worktree prune`"):
            self.assertIn(cmd, s)
        self.assertIn("shared by every worktree", s)

    def test_an_investigative_checkout_is_restored_and_reported(self):
        s = sentence(brief_item(8), "investigative checkout")
        self.assertIn("restore the worktree to a clean state", s)
        self.assertIn("`git status --porcelain`", s)
        self.assertIn("say so in the result", s)


class TestEvidenceWithNoPrIsAValidResult(unittest.TestCase):
    def test_the_brief_says_so(self):
        s = sentence(brief_item(9), "evidence comment")
        self.assertIn("valid result", s)
        self.assertIn("outside the repo", s)
        self.assertIn("open no PR", s)

    def test_a_worker_never_invents_a_change(self):
        s = sentence(brief_item(9), "Never invent")
        self.assertIn("change", s)

    def test_item_five_still_opens_a_pr(self):
        self.assertIn("open a PR with `Closes #<N>`", brief_item(5))


class TestTheResultListsWhatItDidNotVerify(unittest.TestCase):
    def test_every_unrun_ci_check_is_listed_with_its_reason(self):
        s = sentence(brief_item(10), "not verified locally")
        self.assertIn("every CI check", s)
        self.assertIn("did not or could not run", s)
        self.assertIn("reason", s)

    def test_green_gates_mean_local_gates_only(self):
        s = sentence(brief_item(10), "`has-pr`")
        self.assertIn("local gates", s)
        self.assertIn("watch", s)

    def test_a_profile_may_name_ci_only_checks_as_a_hint(self):
        s = sentence(brief_item(10), "profile")
        self.assertIn("commonly fail only in CI", s)
        self.assertIn("secret scan", s)


class TestTheOutcomeTable(unittest.TestCase):
    def test_the_evidence_row_asks_for_a_human(self):
        rows = outcome_rows()
        self.assertEqual(
            rows.get("Investigated: no repo change can fix it, evidence posted"),
            "`needs-review`")

    def test_no_usable_change_stays_agent_failed(self):
        self.assertEqual(outcome_rows().get("No usable change"),
                         "`agent-failed`")

    def test_reconcile_maps_an_evidence_issue_to_needs_review(self):
        s = sentence(phase2(), "evidence outcome and posted its comment")
        self.assertIn("`needs-review`", s)
        self.assertNotIn("`agent-failed`", s)

    def test_reconcile_keeps_no_pr_at_all_as_agent_failed(self):
        s = sentence(phase2(), "or no PR at all")
        self.assertIn("`agent-failed`", s)

    def test_needs_review_label_covers_the_evidence_outcome(self):
        text = SKILL.read_text(encoding="utf-8")
        m = re.search(r"\| `needs-review` \| ([^|]+?) +\|", text)
        self.assertIn("no repo change can fix", m.group(1))
        self.assertIn("a human looks next", m.group(1))


class TestTheCircuitBreaker(unittest.TestCase):
    def test_the_evidence_outcome_is_not_a_failure(self):
        s = sentence(phase4(), "evidence outcome")
        self.assertIn("not a failure", s)
        self.assertIn("leaves the count unchanged", s)

    def test_three_consecutive_failures_still_stop(self):
        s = sentence(phase4(), "Three consecutive failures")
        self.assertIn("stop and report", s)


class TestTheWallClockBound(unittest.TestCase):
    def test_the_brief_states_the_bound(self):
        s = sentence(brief_item(11), "45 minutes")
        self.assertIn("from dispatch", s)

    def test_the_bound_sends_one_check_in(self):
        s = sentence(after_table(), "At 45 minutes")
        self.assertIn("one check-in", s)
        self.assertIn("status", s)
        self.assertIn("plan to stop", s)

    def test_a_silent_worker_is_stopped_and_counts_as_stalled(self):
        s = sentence(after_table(), "has not answered")
        self.assertIn("10 minutes", s)
        self.assertIn("is stopped", s)
        self.assertIn("counts as stalled", s)

    def test_a_worker_that_answers_ends_with_its_result(self):
        s = sentence(after_table(), "The worker answers")
        self.assertIn("draft PR", s)
        self.assertIn("evidence", s)

    def test_wall_clock_is_the_portable_bound(self):
        s = sentence(after_table(), "portable")
        self.assertIn("`telemetry` hook", s)
        self.assertIn("no spend bound", s)


class TestEmptyWorktreesAreReclaimed(unittest.TestCase):
    def bullet(self):
        m = re.search(r"- Remove (.*?)(?= - [A-Z]|\Z)", phase4())
        return m.group(0) if m else ""

    def test_only_the_orchestrators_own_worktree_without_a_pr(self):
        s = sentence(self.bullet(), "never one")
        self.assertIn("cut", s)
        self.assertIn("never one with a PR", s)

    def test_no_commit_ahead_of_origin_main(self):
        s = sentence(self.bullet(), "rev-list")
        self.assertIn("refs/remotes/origin/main..HEAD", s)
        self.assertIn("prints 0", s)

    def test_a_clean_tree(self):
        s = sentence(self.bullet(), "status --porcelain")
        self.assertIn("--untracked-files=all", s)
        self.assertIn("prints nothing", s)

    def test_no_remote_branch(self):
        s = sentence(self.bullet(), "ls-remote")
        self.assertIn("refs/heads/<branch>", s)
        self.assertIn("prints nothing", s)

    def test_no_live_process(self):
        s = sentence(self.bullet(), "lsof")
        self.assertIn("prints nothing", s)

    def test_removal_never_forces(self):
        s = sentence(self.bullet(), "git worktree remove")
        self.assertIn("never `--force`", s)
        self.assertIn("git branch -D --", s)

    def test_a_failed_check_leaves_the_worktree(self):
        s = sentence(self.bullet(), "A failed")
        self.assertIn("leaves the worktree", s)


class TestWorkOrderBriefCarriesTheSafetyItems(unittest.TestCase):
    def brief(self):
        text = WORK_ORDERS.read_text(encoding="utf-8")
        run = text.split("## Worker brief", 1)[1].split("\n## ", 1)[0]
        return " ".join(run.split())

    def test_processes_and_shared_git_state(self):
        s = brief_item(10, self.brief())
        self.assertIn("by PID", s)
        self.assertIn("`git stash`", s)
        self.assertIn("restore the worktree to a clean state", s)

    def test_not_verified_locally(self):
        s = brief_item(11, self.brief())
        self.assertIn("not verified locally", s)
        self.assertIn("every CI check", s)


if __name__ == "__main__":
    unittest.main()
