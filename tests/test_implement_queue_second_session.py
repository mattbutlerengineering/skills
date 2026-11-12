"""implement-queue detects a second queue session and re-entry (#1714).

The Rules say one queue session per repo at a time, and a `lock` hook
that keeps its lock in the local checkout cannot see a cloud session.
The skill pins four things, each in its own sentence:

- Phase 0 step 4 lists the `in-progress` issues this session did not
  claim, with their claim times, and recently pushed PRs, and reports
  them before claiming;
- the label claim is the mutex: the session proceeds, a hard stop is
  not used, and what was found narrows what is touched;
- Phase 1 makes the claim an operation with one winner: `ready` is
  removed first and the claim is held only on a 200, `in-progress` is
  added after it, and the timeline's single `in-progress` event, taken
  at GitHub's clock, is a secondary check. A lost race or an unproven
  claim skips the issue and never releases it, and a skipped issue is
  not claimed by this session;
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
        text = SKILL.read_text(encoding="utf-8")
        m = re.search(r"^## Phase 0: Pre-flight\n(.*?)(?=^## )", text,
                      re.S | re.M)
        numbers = [int(n) for n in re.findall(r"^(\d+)\. ", m.group(1),
                                              re.M)]
        self.assertEqual(numbers, [1, 2, 3, 4])
        self.assertTrue(phase0_step(4).startswith(
            "Look for another queue session"))

    def test_it_lists_issues_this_session_did_not_claim(self):
        s = sentence(phase0_step(4), "gh issue list --label in-progress")
        self.assertIn("did not claim", s)
        self.assertIn("--state open", s)

    def test_a_fresh_and_a_looping_session_are_told_apart(self):
        s = sentence(phase0_step(4), "A fresh session")
        self.assertIn("every one counts", s)
        self.assertIn("subtracts", s)
        self.assertIn("never one Phase 1 skipped", s)

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
        self.assertIn("Phase 3 step 1's head comparison", s)
        self.assertIn("`--disable-auto` still run", s)
        self.assertIn("they only tighten", s)
        self.assertIn("post-claim check", s)

    def test_the_lock_hook_is_not_the_detection(self):
        s = sentence(phase0_step(4), "`lock` hook")
        self.assertIn("cloud session", s)
        self.assertIn("One queue session per repo", s)


NEVER = "Never move the issue back to `ready`"


class TestPhaseOnePostClaimCheck(unittest.TestCase):
    def setUp(self):
        self.phase = section("Phase 1: Claim a batch")

    def test_the_removal_of_ready_comes_first_for_the_claim_only(self):
        s = sentence(self.phase, "For the claim transition only")
        self.assertIn("removal of `ready` comes first", s)
        self.assertIn("every other transition keeps", s)

    def test_the_labels_and_the_date_are_read_before_the_claim(self):
        s = sentence(self.phase, "issues/<N>` just before the claim")
        self.assertIn("gh api -i", s)
        self.assertIn("skip the issue and never touch its labels", s)
        s = sentence(self.phase, "`Date` header")
        self.assertIn("whole-second", s)

    def test_the_timeline_is_read_before_claiming(self):
        s = sentence(self.phase, "cannot be read")
        self.assertIn("claim nothing for it", s)

    def test_no_ready_event_means_no_claim(self):
        s = sentence(self.phase, "holds no `ready` labeled event")
        self.assertIn("claim nothing for it", s)

    def test_the_claim_is_held_only_on_a_200(self):
        s = sentence(self.phase, "only on a 200")
        self.assertIn("Hold the claim", s)
        self.assertNotIn("404", s)

    def test_a_404_or_other_status_skips_and_touches_no_label(self):
        s = sentence(self.phase, "a 404 included")
        self.assertIn("any other status", s)
        self.assertIn("another session removed `ready` first", s)
        self.assertIn("skip the issue", s)
        self.assertIn("never touch its labels", s)
        self.assertIn("report it", s)
        self.assertNotIn("hold the claim", s.lower())

    def test_the_removal_is_a_delete_of_ready_and_runs_before_the_add(self):
        cmd = "gh api -X DELETE repos/{owner}/{repo}/issues/<N>/labels/ready"
        self.assertIn(cmd, self.phase)
        add = self.phase.index("add `in-progress`")
        self.assertLess(self.phase.index(cmd), add)

    def test_no_worker_is_dispatched_before_the_200_and_the_add(self):
        s = sentence(self.phase, "Dispatch no worker before")
        self.assertIn("that 200", s)
        self.assertIn("add of `in-progress`", s)
        cmd = "labels/ready"
        self.assertLess(self.phase.index("Dispatch no worker before"),
                        len(self.phase))
        self.assertLess(self.phase.index(cmd),
                        self.phase.index("Dispatch no worker before"))

    def test_a_failed_add_is_repaired_by_reconcile(self):
        s = sentence(self.phase, "A failed add")
        self.assertIn("dispatch nothing", s)
        self.assertIn("Reconcile before Phase 4", s)

    def test_the_documentation_wording_is_not_overstated(self):
        s = sentence(self.phase, "a 404 included")
        self.assertIn("documentation gives it for a label that does not exist",
                      s)

    def test_exactly_one_event_and_it_is_this_sessions(self):
        s = sentence(self.phase, "exactly one")
        self.assertIn("secondary check", s)
        self.assertIn("`in-progress` labeled event", s)
        self.assertIn("last `ready` labeled event", s)
        self.assertIn("at or after the time noted", s)
        self.assertIn("whole seconds", s)
        self.assertIn("this session's", s)
        self.assertIn("/timeline --paginate", self.phase)

    def test_no_mcp_twin_so_the_check_fails_closed(self):
        s = sentence(self.phase, "no MCP twin")
        self.assertIn("removal", s)
        self.assertIn("timeline", s)
        self.assertIn("claim nothing", s)

    def test_an_unreadable_timeline_after_the_claim_fails_closed(self):
        s = sentence(self.phase, "unreadable timeline after the add")
        self.assertIn("skip the issue", s)
        self.assertIn("dispatch no worker", s)
        self.assertIn("leave the label", s)
        self.assertIn("report it", s)

    def test_zero_events_after_the_claim_skip_and_leave_the_label(self):
        s = sentence(self.phase, "no `in-progress` labeled event after")
        self.assertIn("skip the issue", s)
        self.assertIn("dispatch no worker", s)
        self.assertIn("leave the label", s)
        self.assertIn("report it", s)

    def test_two_events_or_an_earlier_one_lose_the_race(self):
        s = sentence(self.phase, "two or more")
        self.assertIn("lost the race", s)
        self.assertIn("earlier than the time noted", s)
        self.assertIn("skip the issue", s)
        self.assertIn("dispatch no worker", s)
        self.assertIn("leave the label", s)
        self.assertIn("report it", s)

    def test_a_lost_race_never_releases_the_issue(self):
        s = sentence(self.phase, NEVER)
        self.assertIn("lost race", s)
        self.assertIn("already have dispatched a worker", s)

    def test_a_skipped_issue_is_not_claimed_by_this_session(self):
        s = sentence(self.phase, "An issue skipped in this phase")
        self.assertIn("not claimed by this session", s)
        self.assertIn("Reconcile before Phase 4 leaves it alone", s)
        self.assertIn("Phase 0 step 4 does not subtract it", s)

    def test_no_loosening_sentence_hides_elsewhere_in_the_phase(self):
        rest = self.phase.replace(sentence(self.phase, NEVER), "")
        lower = rest.lower()
        for word in ("release", "back to `ready`", "put `ready` back",
                     "restore", "dispatch it", "dispatch the worker",
                     "dispatch a worker", "dispatch anyway",
                     "dispatch the issue"):
            self.assertNotIn(word, lower, word)


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
        self.assertIn("recently pushed PRs", s)
        self.assertIn("leaves alone", s)
        self.assertNotIn("cannot tell, and Phase 0 step 4 shows it the issues",
                         s)


class TestTheRuleIsKept(unittest.TestCase):
    def test_the_rule_bullet_is_unchanged(self):
        rules = section("Rules")
        self.assertIn("- One queue session per repo at a time.", rules)


if __name__ == "__main__":
    unittest.main()
