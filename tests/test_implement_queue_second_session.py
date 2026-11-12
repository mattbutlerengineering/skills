"""implement-queue detects a second queue session and re-entry (#1714).

The Rules say one queue session per repo at a time, and a `lock` hook
that keeps its lock in the local checkout cannot see a cloud session.
The skill pins four things, each in its own sentence:

- Phase 0 step 4 lists the `in-progress` issues this session did not
  claim, with their claim times, and recently pushed PRs, and reports
  them before claiming;
- the label claim is the mutex: the session proceeds, a hard stop is
  not used, and what was found narrows what is touched;
- Phase 1 checks after the transition that the issue's timeline holds
  exactly one `in-progress` label event since `ready`, fails closed,
  and releases only when this session's transition was the later one;
- a re-invocation while an iteration is in flight continues it, and
  the `/loop` interval is a minimum gap, not a bound on one iteration.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "implement-queue" / "SKILL.md"


def section(heading):
    text = SKILL.read_text(encoding="utf-8")
    m = re.search(r"^## " + re.escape(heading) + r"\n(.*?)(?=^## |\Z)",
                  text, re.S | re.M)
    return " ".join(m.group(1).split()) if m else ""


def sentence(text, needle):
    """The sentence (ends at a full stop and a space) holding `needle`,
    so an assertion cannot pass on words from a neighbouring one."""
    for s in re.split(r"(?<=\.) ", text):
        if needle in s:
            return s
    return ""


def phase0_step(number):
    phase = section("Phase 0: Pre-flight")
    m = re.search(rf"^.*(?:^| ){number}\. (.*?)(?= {number + 1}\. [A-Z]|\Z)",
                  phase)
    return m.group(1) if m else ""


class TestPhaseZeroDetectsAnotherSession(unittest.TestCase):
    def test_the_step_comes_after_the_existing_three(self):
        phase = section("Phase 0: Pre-flight")
        self.assertTrue(phase0_step(3).startswith("List open PRs."))
        self.assertTrue(phase0_step(4).startswith(
            "Look for another queue session"))
        self.assertEqual(phase0_step(5), "")
        self.assertLess(phase.index(" 3. List open PRs."),
                        phase.index(" 4. Look for another queue session"))

    def test_it_lists_issues_this_session_did_not_claim(self):
        s = sentence(phase0_step(4), "gh issue list --label in-progress")
        self.assertIn("did not claim", s)
        self.assertIn("--state open", s)

    def test_a_fresh_and_a_looping_session_are_told_apart(self):
        s = sentence(phase0_step(4), "A fresh session")
        self.assertIn("every one counts", s)
        self.assertIn("subtracts", s)

    def test_each_issue_carries_its_claim_time_from_the_timeline(self):
        s = sentence(phase0_step(4), "/timeline --paginate")
        self.assertIn('.event == "labeled"', s)
        self.assertIn('.label.name == "in-progress"', s)
        self.assertIn(".created_at", s)

    def test_the_mcp_session_has_no_timeline_twin(self):
        s = sentence(phase0_step(4), "no MCP twin")
        self.assertIn("timeline", s)
        self.assertIn("without a time", s)

    def test_it_lists_prs_with_a_recent_head_push(self):
        step = phase0_step(4)
        s = sentence(step, "15 minutes")
        self.assertIn("did not open", s)
        self.assertIn("head commit", s)
        self.assertIn("commit.committer.date", step)

    def test_it_reports_before_claiming(self):
        s = sentence(phase0_step(4), "Report both lists")
        self.assertIn("before Phase 1 claims anything", s)

    def test_work_orders_keep_their_own_claim(self):
        s = sentence(phase0_step(4), "source: work-orders")
        self.assertIn("wo:in-progress", s)
        self.assertIn("pull request list still applies", s)


class TestTheLabelClaimIsTheMutex(unittest.TestCase):
    def test_the_session_proceeds(self):
        s = sentence(phase0_step(4), "The label claim is the mutex")
        self.assertIn("proceeds to Phase 1", s)
        self.assertIn("never stops", s)

    def test_a_hard_stop_is_refused_for_its_reason(self):
        s = sentence(phase0_step(4), "hard stop")
        self.assertIn("stale `in-progress` label", s)
        self.assertIn("block the queue for ever", s)

    def test_what_was_found_narrows_what_is_touched(self):
        s = sentence(phase0_step(4), "never touch")
        self.assertIn("issue or PR listed here", s)
        self.assertIn("post-claim check", s)

    def test_the_lock_hook_is_not_the_detection(self):
        s = sentence(phase0_step(4), "`lock` hook")
        self.assertIn("cloud session", s)
        self.assertIn("One queue session per repo", s)


class TestPhaseOnePostClaimCheck(unittest.TestCase):
    def setUp(self):
        self.phase = section("Phase 1: Claim a batch")

    def test_the_labels_are_re_read_immediately_before_the_transition(self):
        s = sentence(self.phase, "immediately before the transition")
        self.assertIn("skip the issue", s)
        self.assertIn("`in-progress`", s)

    def test_the_timeline_is_read_before_claiming(self):
        s = sentence(self.phase, "cannot be read")
        self.assertIn("claim nothing for it", s)

    def test_exactly_one_in_progress_event_since_ready(self):
        s = sentence(self.phase, "exactly one")
        self.assertIn("`in-progress` labeled event", s)
        self.assertIn("last `ready` labeled event", s)
        self.assertIn("/timeline --paginate", self.phase)

    def test_no_mcp_twin_so_the_check_fails_closed(self):
        s = sentence(self.phase, "no MCP twin")
        self.assertIn("timeline", s)
        self.assertIn("claim nothing", s)

    def test_an_unreadable_timeline_after_the_claim_fails_closed(self):
        s = sentence(self.phase, "unreadable timeline after the transition")
        self.assertIn("skip the issue", s)
        self.assertIn("leave the label", s)

    def test_two_events_mean_the_race_was_lost_and_the_issue_skipped(self):
        s = sentence(self.phase, "two or more")
        self.assertIn("lost the race", s)
        self.assertIn("skip the issue", s)
        self.assertIn("report it", s)

    def test_release_only_when_this_sessions_transition_was_later(self):
        s = sentence(self.phase, "back to `ready`")
        self.assertIn("only when", s)
        self.assertIn("strictly later", s)

    def test_a_tie_or_doubt_leaves_the_label(self):
        s = sentence(self.phase, "On a tie")
        self.assertIn("leave the label", s)


class TestReinvocationContinuesTheIteration(unittest.TestCase):
    def setUp(self):
        self.phase = section("Phase 4: Loop or stop")

    def test_a_reinvocation_continues_the_iteration_in_flight(self):
        s = sentence(self.phase, "re-invocation")
        self.assertIn("continues that iteration", s)
        self.assertIn("never starts a second one", s)

    def test_the_loop_interval_is_a_gap_not_a_bound(self):
        s = sentence(self.phase, "minimum gap")
        self.assertIn("`/loop 30m`", self.phase)
        self.assertIn("not a bound on one iteration", s)

    def test_a_tick_during_an_iteration_joins_it(self):
        s = sentence(self.phase, "tick")
        self.assertIn("joins", s)

    def test_a_session_without_memory_is_caught_by_phase_zero(self):
        s = sentence(self.phase, "no memory")
        self.assertIn("Phase 0 step 4", s)


class TestTheRuleIsKept(unittest.TestCase):
    def test_the_rule_bullet_is_unchanged(self):
        rules = section("Rules")
        self.assertIn("- One queue session per repo at a time.", rules)


if __name__ == "__main__":
    unittest.main()
