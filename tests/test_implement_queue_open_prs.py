"""implement-queue's Phase 0 step 3 states whose PRs it owns (#1712).

The queue meets PRs it did not open: bot, release and revert PRs, PRs
with no linked issue, held PRs, PRs another session is still pushing to.
Each promise is pinned to its own sentence so a swapped remedy fails.
"""
import re
import unittest

from tests.test_implement_queue_head_pin import SKILL, section


def step3():
    text = section(SKILL, "Phase 0: Pre-flight")
    m = re.search(r"(?:^| )3\. Read every open PR(.*)", text)
    return m.group(0) if m else ""


def sentence(text, needle):
    for s in re.split(r"(?<=\.) ", text):
        if needle in s:
            return s
    return ""


class TestOpenPrScope(unittest.TestCase):
    def test_scope_is_the_state_labelled_issue_or_the_profile(self):
        s = sentence(step3(), "belongs to this queue")
        for w in ("closes an issue", "`in-progress`", "`has-pr`",
                  "`needs-review`", "`agent-failed`", "`stealable`"):
            self.assertIn(w, s)
        self.assertNotIn("profile", s)

    def test_every_open_pr_is_read(self):
        self.assertIn("Read every open PR", step3())

    def test_a_foreign_green_pr_still_goes_to_the_gate(self):
        s = sentence(step3(), "foreign green PR")
        self.assertIn("goes to the Phase 2 gate unchanged", s)

    def test_a_foreign_failed_pr_is_reported_not_fixed(self):
        s = sentence(step3(), "foreign failed PR")
        self.assertIn("never fixed", s)
        self.assertIn("reported", s)
        self.assertIn("does not block claiming", s)


class TestFailedPrDispositions(unittest.TestCase):
    def test_a_failed_queue_pr_blocks_claiming(self):
        s = sentence(step3(), "Claim nothing new")
        self.assertIn("failed PR of this queue", s)
        self.assertIn("matches none of the causes below", s)

    def test_the_causes_are_checked_first_and_the_first_match_wins(self):
        s = sentence(step3(), "first match wins")
        self.assertIn("before it can block", s)

    def test_a_failed_queue_pr_is_fixed_or_marked_agent_failed(self):
        s = sentence(step3(), "failed ones of this queue")
        self.assertIn("get fixed", s)
        self.assertIn("`agent-failed`", s)

    def test_no_linked_issue_is_reported_and_does_not_block(self):
        s = sentence(step3(), "no linked issue")
        self.assertIn("nothing to label", s)
        self.assertIn("reported", s)
        self.assertIn("does not block claiming", s)
        self.assertNotIn("re-run", s)

    def test_a_held_failed_pr_is_handed_off_and_does_not_block(self):
        s = sentence(step3(), "failed PR that carries a `hold_labels`")
        self.assertIn("handed to a human", s)
        self.assertIn("does not block claiming", s)

    def test_a_pr_that_must_not_merge_is_never_pushed_to_green(self):
        s = sentence(step3(), "must not merge")
        for w in ("never fixed, re-run or updated", "reported",
                  "does not block claiming"):
            self.assertIn(w, s)

    def test_an_infrastructure_failure_is_rerun_once_per_head(self):
        s = sentence(step3(), "no repo cause")
        self.assertIn("once per head SHA", s)
        self.assertIn("step 2", s)
        self.assertIn("judged again", s)


class TestSettled(unittest.TestCase):
    def test_settled_needs_the_recorded_head_and_fifteen_minutes(self):
        s = sentence(step3(), "is settled when")
        self.assertIn("equals the head this session recorded", s)
        self.assertIn("earlier iteration", s)
        self.assertIn("at least 15 minutes old", s)

    def test_a_first_seen_pr_waits_exactly_one_iteration(self):
        s = sentence(step3(), "first seen")
        self.assertIn("records every open PR's head SHA", s)
        self.assertIn("waits exactly one iteration", s)
        self.assertIn("goes to the gate", s)

    def test_a_worker_named_head_is_settled_at_once(self):
        s = sentence(step3(), "this session's own worker result")
        self.assertIn("counts as settled at once", s)

    def test_the_date_is_read_from_the_head_commit_itself(self):
        s = sentence(step3(), "commits/<headRefOid>")
        self.assertIn("--jq .commit.committer.date", s)

    def test_a_date_from_another_commit_is_not_settled(self):
        s = sentence(step3(), "any commit other than")
        self.assertIn("current head SHA", s)
        self.assertIn("not settled", s)

    def test_the_proxy_failure_mode_is_a_late_push(self):
        s = sentence(step3(), "git rebase")
        self.assertIn("pushed later", s)
        self.assertIn("recorded-head comparison", s)
        self.assertIn("from the second iteration on", s)

    def test_an_unreadable_date_is_unsettled(self):
        s = sentence(step3(), "cannot be read")
        self.assertIn("not settled", s)

    def test_an_unsettled_green_pr_waits_unreviewed_and_reported(self):
        s = sentence(step3(), "unsettled green PR")
        for w in ("waits", "not reviewed", "reported"):
            self.assertIn(w, s)


class TestTheListIsComplete(unittest.TestCase):
    def test_the_list_command_carries_a_limit(self):
        self.assertIn("gh pr list --state open --limit 1000", step3())

    def test_the_rest_twin_is_paged(self):
        s = sentence(step3(), "REST twin")
        self.assertIn("per_page=100", s)
        self.assertIn("every page", s)
        self.assertIn("`.head.sha` is the head", s)

    def test_a_possibly_truncated_list_fails_closed(self):
        s = sentence(step3(), "may be truncated")
        self.assertIn("count equals the limit", s)
        self.assertIn("claim nothing", s)


if __name__ == "__main__":
    unittest.main()
