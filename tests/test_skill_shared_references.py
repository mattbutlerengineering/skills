"""Skill prose that two skills share has one owner file.

Each passage below was once copied into two skills and kept in step only
by memory (docs/fixes/one-owner-for-copied-skill-text). The owner holds
the text; every consumer cites the owner's path and keeps only what
differs for it. A copy pasted back passes any `assertIn` on either file,
so these tests COUNT occurrences across the owner and its consumers:
exactly one, and that one in the owner.
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# (passage, owner, {consumer: path it must cite}, distinctive sentences)
SHARED = [
    ("recon",
     "skills/audit/references/recon.md",
     {"skills/audit/SKILL.md": "references/recon.md",
      "skills/automate/SKILL.md": "../audit/references/recon.md"},
     ["dropping every entry that carries a `pull_request` key",
      "is a duplicate of work in flight",
      "gh issue list --state open --limit 1000"]),
    ("routing ladder",
     "skills/audit/references/routing.md",
     {"skills/audit/SKILL.md": "references/routing.md",
      "skills/automate/SKILL.md": "../audit/references/routing.md"},
     ["the default for anything worth remembering and not worth a run "
      "today",
      "the dedupe happens before the write, not after"]),
]

DARK_DESIGN_SYSTEMS = [
    "skills/animated-diagram/references/design-system.md",
]


def normalized(rel):
    """Lower-cased, whitespace-collapsed text, so a sentence hard-wrapped
    at a different column, or capitalised at a sentence start, still
    counts as the same sentence. A missing file reads as empty, so the
    test reports the missing owner as a count rather than erroring."""
    path = ROOT / rel
    if not path.is_file():
        return ""
    return " ".join(path.read_text(encoding="utf-8").split()).lower()


class SharedPassageHasOneOwner(unittest.TestCase):

    def test_each_sentence_occurs_once_and_in_its_owner(self):
        for passage, owner, consumers, sentences in SHARED:
            files = [owner, *consumers]
            for sentence in sentences:
                needle = " ".join(sentence.split()).lower()
                counts = {rel: normalized(rel).count(needle)
                          for rel in files}
                with self.subTest(passage=passage, sentence=sentence):
                    self.assertEqual(
                        (sum(counts.values()), counts[owner]), (1, 1),
                        f"{passage}: {sentence!r} counted {counts}")

    def test_each_consumer_cites_its_owner(self):
        for passage, _owner, consumers, _sentences in SHARED:
            for consumer, cited in consumers.items():
                with self.subTest(passage=passage, consumer=consumer):
                    self.assertTrue(cited.lower() in normalized(consumer),
                                    f"{consumer} never cites {cited}")

    def test_each_cited_owner_ships(self):
        """A citation to a file that is not there is the drift this
        replaces, moved one step along."""
        for passage, owner, _consumers, _sentences in SHARED:
            with self.subTest(passage=passage):
                self.assertTrue((ROOT / owner).is_file(), owner)

    def test_no_keep_in_step_instruction_survives(self):
        """With one owner there is no second copy to match."""
        for rel in DARK_DESIGN_SYSTEMS:
            with self.subTest(file=rel):
                self.assertFalse("match it in the other" in normalized(rel),
                                 f"{rel} still says to match the copy")


class WorkOrderBriefListIsNumberedInOrder(unittest.TestCase):

    def test_worker_brief_items_number_one_to_n(self):
        text = (ROOT / "skills/implement-queue/references/work-orders.md"
                ).read_text(encoding="utf-8")
        section = text.split("## Worker brief", 1)[1].split("\n## ", 1)[0]
        numbers = [int(n) for n in
                   re.findall(r"^(\d+)\. ", section, flags=re.MULTILINE)]
        self.assertEqual(numbers, list(range(1, len(numbers) + 1)))

    def _brief(self):
        text = (ROOT / "skills/implement-queue/references/work-orders.md"
                ).read_text(encoding="utf-8")
        return " ".join(text.split("## Worker brief", 1)[1]
                        .split("\n## ", 1)[0].split())

    def test_brief_carries_the_time_bound_and_stall_abort(self):
        brief = self._brief()
        for needle in ("foreground under a time bound",
                       "Never start a background or watch process",
                       "Stall-abort: after two resumes"):
            with self.subTest(needle=needle):
                self.assertIn(needle, brief)

    def test_brief_carries_the_45_minute_bound_and_check_in(self):
        brief = self._brief()
        self.assertIn("within 45 minutes", brief)
        self.assertIn("answer the orchestrator's check-in", brief)

    def test_brief_carries_evidence_outcomes_mapped_to_wo_failed(self):
        brief = self._brief()
        self.assertIn("evidence outcome", brief)
        self.assertIn("already-resolved outcome", brief)
        self.assertIn("make wo-failed ISSUE=<n>", brief)

    def test_brief_carries_the_catch_classes_inline(self):
        brief = self._brief()
        for needle in ("hallucination", "regression", "gate bypass",
                       "criteria gap", "each acceptance criterion"):
            with self.subTest(needle=needle):
                self.assertIn(needle, brief)


class WorkOrderReconcileAndOwnershipRules(unittest.TestCase):
    """#1831: the work-orders Reconcile section and the which-PRs rule."""

    def _section(self, heading):
        text = (ROOT / "skills/implement-queue/references/work-orders.md"
                ).read_text(encoding="utf-8")
        return " ".join(text.split(heading, 1)[1]
                        .split("\n## ", 1)[0].split("\n### ", 1)[0]
                        .split())

    def test_reconcile_states_outcomes_leave_breaker_count_unchanged(self):
        section = self._section("## Reconcile in this mode")
        self.assertIn("leaves the three-failure circuit-breaker count "
                      "unchanged", section)

    def test_reconcile_says_skill_outcomes_apply_in_this_mode(self):
        section = self._section("## Reconcile in this mode")
        self.assertIn("SKILL.md's evidence and already-resolved outcomes "
                      "apply in this mode", section)

    def test_reconcile_drift_case_names_the_dispatch_shim(self):
        section = self._section("## Reconcile in this mode")
        self.assertIn("gh workflow run validator.yml -f pr=N", section)
        self.assertIn("for a human to run", section)
        self.assertIn("re-runs the whole validator for that PR", section)

    def test_reconcile_points_to_the_phase_0_rule(self):
        section = self._section("## Reconcile in this mode")
        self.assertIn("(#which-open-prs-are-this-queues)", section)

    def test_ownership_rule_points_to_reconcile(self):
        section = self._section("### Which open PRs are this queue's")
        self.assertIn("(#reconcile-in-this-mode)", section)

    def test_ownership_rule_reads_carries_not_ends_with(self):
        section = self._section("### Which open PRs are this queue's")
        self.assertIn("carries the line `Driver: implement-queue`", section)
        self.assertNotIn("ends with the line", section)

    def test_ownership_rule_says_a_red_pr_is_released_not_fixed(self):
        section = self._section("### Which open PRs are this queue's")
        self.assertIn("is not given a second worker to make it green",
                      section)
        self.assertIn("goes straight to `make wo-failed`", section)
        self.assertIn("a second attempt at a work order is a human's call",
                      section)
        self.assertIn("The only worker a PR of this queue gets after its "
                      "first is the reviewer gate's one same-branch fix",
                      section)
        self.assertNotIn("is not fixed by a new worker", section)

    def test_ownership_cross_reference_names_both_reconcile_states(self):
        section = self._section("### Which open PRs are this queue's")
        self.assertIn("still on `wo:in-progress` or with no `wo:*` label",
                      section)


if __name__ == "__main__":
    unittest.main()
