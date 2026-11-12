"""implement-queue's review covers one head (#1713).

A PR reviewed at one head can gain commits before it merges, and an
`--auto` merge enabled with no head lands whatever is there when checks
go green. Four promises keep the review bound to the head it saw, each
pinned here against the real files:

- the gate records one head SHA at step 1 and uses it for the reviewer
  worktree, the file list, the verdict comment and the merge;
- the default and REST `merge-command` carry the pin (`gh` and the REST
  endpoint both take the head), and the repo's own profile restatement
  carries it too;
- Phase 3 compares each enqueued PR's head with the gated head and
  disables auto-merge on a mismatch;
- the Rules section states that a review covers one head.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "implement-queue" / "SKILL.md"
CONTRACT = ROOT / "skills" / "implement-queue" / "references" / "reviewer-contract.md"
MIGRATION = ROOT / "skills" / "implement-queue" / "references" / "profile-migration.md"
ROUTINE = ROOT / "docs" / "factory" / "merge-train-routine.md"
PROFILE = ROOT / ".claude" / "implement-queue.md"

DEFAULT_MERGE = ("gh pr merge <N> --auto --squash --delete-branch "
                 "--match-head-commit <sha>")


def flat(path):
    return " ".join(path.read_text(encoding="utf-8").split())


def section(path, heading):
    text = path.read_text(encoding="utf-8")
    m = re.search(r"^## " + re.escape(heading) + r"\n(.*?)(?=^## |\Z)",
                  text, re.S | re.M)
    return " ".join(m.group(1).split()) if m else ""


def gate_step(number):
    gate = section(SKILL, "Phase 2: Implement, then gate")
    gate = gate.split("### The gate, per PR", 1)[1]
    m = re.search(rf"(?:^| ){number}\. \*\*(.*?)(?= \d\. \*\*|\Z)", gate)
    return m.group(0) if m else ""


class TestTheGateRecordsOneHead(unittest.TestCase):
    def test_step_one_records_the_head_sha_once(self):
        step = gate_step(1)
        self.assertIn("headRefOid", step)
        self.assertIn("pulls/<N> --jq .head.sha", step)
        self.assertIn("pull_request_read", step)
        self.assertIn("Record the PR's head SHA once, here", step)

    def test_later_steps_use_the_recorded_sha(self):
        step3, step4, step5 = gate_step(3), gate_step(4), gate_step(5)
        self.assertIn("recorded head", step4)
        self.assertIn("git worktree add --detach <path> <head-sha>", step4)
        self.assertIn("recorded head", step3)
        self.assertIn("recorded head", step5)
        self.assertIn("Head: <sha>", step5)

    def test_a_moved_head_restarts_the_gate(self):
        step = gate_step(1)
        self.assertIn("differs from the recorded head", step)
        self.assertIn("restarts from step 1", step)

    def test_the_head_is_read_again_at_three_points(self):
        step = gate_step(1)
        self.assertIn(
            "Read the PR's head again before the review is dispatched, "
            "before the verdict comment and immediately before the merge; "
            "if it differs from the recorded head, the gate restarts "
            "from step 1 on the new head", step)

    def test_the_changed_file_hook_reads_the_recorded_head(self):
        text = flat(SKILL)
        self.assertIn("at the recorded head", text)

    def test_the_reviewer_input_names_the_head(self):
        text = flat(CONTRACT)
        self.assertIn("| `headSha` |", text)


class TestTheMergeCommandCarriesThePin(unittest.TestCase):
    def test_the_default_row_pins_the_head(self):
        self.assertIn(f"| `merge-command` | `{DEFAULT_MERGE}`", flat(SKILL))

    def test_the_rest_twin_pins_the_head(self):
        text = flat(SKILL)
        self.assertIn("-f merge_method=squash -f sha=<sha>", text)

    def test_the_mcp_twin_pins_the_gated_head(self):
        self.assertIn("`expectedHeadSha` set to the gated head", flat(SKILL))

    def test_the_migration_row_restates_the_pinned_default(self):
        self.assertIn(f"`{DEFAULT_MERGE}`", flat(MIGRATION))

    def test_this_repos_profile_restates_the_pinned_default(self):
        text = section(PROFILE, "merge-command")
        self.assertIn(DEFAULT_MERGE, text)


class TestPhaseThreeComparesHeads(unittest.TestCase):
    def test_a_mismatch_disables_auto_merge_and_regates(self):
        phase = section(SKILL, "Phase 3: Merge train")
        self.assertIn("headRefOid", phase)
        self.assertIn("gated head", phase)
        self.assertIn("gh pr merge <N> --disable-auto", phase)
        self.assertIn("back through the gate", phase)

    def test_the_comparison_runs_before_the_branch_is_touched(self):
        phase = section(SKILL, "Phase 3: Merge train")
        self.assertLess(phase.index("--disable-auto"),
                        phase.index("`update-branch` hook"))


def sentence(text, needle):
    """The sentence of `text` holding `needle`, so an assertion cannot
    pass on words from a neighbouring sentence."""
    for s in re.split(r"(?<=[.;:]) ", text):
        if needle in s:
            return s
    return ""


def phase3_step(number):
    phase = section(SKILL, "Phase 3: Merge train")
    m = re.search(rf"(?:^| ){number}\. (.*?)(?= \d\. [A-Z]|"
                  r" Release every lock| ?\Z)", phase)
    return m.group(1) if m else ""


class TestPhaseThreeStructure(unittest.TestCase):
    def test_the_comparison_runs_for_every_enqueued_pr_first(self):
        step = phase3_step(1)
        self.assertIn("every enqueued PR", step)
        self.assertIn("--disable-auto", step)
        self.assertNotIn("update-branch", phase3_step(1))

    def test_no_gated_head_is_a_mismatch(self):
        s = sentence(phase3_step(1), "A PR with no gated head")
        self.assertIn("is a mismatch", s)
        self.assertIn("run `gh pr merge <N> --disable-auto`", phase3_step(1))

    def test_the_gated_head_is_read_only_from_the_queues_own_verdict(self):
        step = phase3_step(1)
        self.assertIn("gh api user --jq .login", step)
        self.assertIn("user.login", step)
        self.assertIn("`reviewer-verdict:`", step)
        self.assertIn("otherwise the PR has no gated head", step)

    def test_the_locks_are_released_on_any_exit(self):
        phase = section(SKILL, "Phase 3: Merge train")
        self.assertTrue(phase.endswith(
            "Release every lock you took when the train ends, on any exit."))

    def test_the_adoption_rule_needs_a_new_two_parent_merge_commit(self):
        s = phase3_step(3)
        self.assertIn("adopt the head after the hook as the gated head "
                      "only when the hook exited 0", s)
        self.assertIn("new commit", s)
        self.assertIn("exactly two parents", s)
        self.assertIn("the head read just before the hook first", s)
        self.assertIn("`refs/remotes/origin/main` second", s)
        self.assertIn("is a mismatch", sentence(s, "any other head"))
        self.assertIn("up-to-date", s)

    def test_the_rules_section_names_the_one_exception(self):
        rules = section(SKILL, "Rules")
        self.assertIn("The one exception is the commit the `update-branch` "
                      "hook itself makes", rules)
        s = sentence(rules, "exception")
        self.assertIn("`update-branch` hook", s)
        self.assertIn("Phase 3 step 3", s)


class TestTheTrainRoutineFollowsPhaseThree(unittest.TestCase):
    def test_section_four_compares_heads_and_pins_the_merge(self):
        text = section_by_regex(ROUTINE, r"4 Phase 3: the train")
        self.assertIn("gated head", text)
        self.assertIn("gh pr merge <N> --disable-auto", text)
        self.assertIn("`<sha>` is the gated head", text)


def section_by_regex(path, heading):
    return section(path, heading)


class TestTheOneHeadRule(unittest.TestCase):
    def test_the_rules_section_states_it_once(self):
        text = flat(SKILL)
        rule = ("A review covers one head. A push after it voids the "
                "review, whichever way the verdict pointed.")
        self.assertEqual(text.count(rule), 1)
        self.assertIn(rule, section(SKILL, "Rules"))

    def test_the_consent_covers_only_the_gated_head(self):
        policy = section(SKILL, "Merge policy")
        self.assertIn("gated head", policy)


if __name__ == "__main__":
    unittest.main()
