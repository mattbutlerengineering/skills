"""The open-PR pre-flight (issue #845) — one statement, five reciters.

docs/pipeline-protocol.md's "Open pull requests first" section is the
one owner of the rule that open pull requests are drained before new
work starts. Every skill that can start new work names that section
rather than restating the rule in its own words: the two queue skills
that already stated it, and the three that never looked (`next`,
`conduct`, `autorun`).

Pins the section name, the rule's sentence, and the two clauses a
reciter could not safely lose: no merge without the Owner's answer, and
the optional chain-simulate step's pointer at the cross-PR hazard page.
Whether an agent actually listed the open PRs is not a thing a test can
know; these pin what the prose promises, against the real files.
"""
import unittest
from pathlib import Path

import protocol

REPO_ROOT = Path(__file__).resolve().parent.parent
PROTOCOL_DOC = REPO_ROOT / "docs" / "pipeline-protocol.md"

PREFLIGHT_HEADING = "Open pull requests first"
RULE = "Open PRs come before new work"
HAZARD_PAGE = "docs/kb/cross-pr-merge-hazards.md"

# Every skill that can start new work: a run (next), a run's stages
# (autorun), a batch (conduct), or a batch of queued items (the two
# queue skills, which stated the rule before it had one home).
WORK_STARTING = ("next", "conduct", "autorun", "work-queue",
                 "implement-queue")


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


class TestProtocolStatesThePreflight(unittest.TestCase):
    def setUp(self):
        self.body = flat(section(PROTOCOL_DOC.read_text(encoding="utf-8"),
                                 PREFLIGHT_HEADING))

    def test_it_states_the_queue_skills_rule(self):
        self.assertIn(RULE.lower(), self.body)

    def test_it_lists_open_prs_oldest_first(self):
        self.assertIn("oldest first", self.body)

    def test_it_never_merges_without_the_owners_answer(self):
        self.assertIn("never merges on its own", self.body)
        self.assertIn("owner's explicit answer", self.body)

    def test_a_pr_waiting_on_the_owner_does_not_block_new_work(self):
        self.assertIn("does not block new work", self.body)

    def test_the_optional_chain_simulate_step_points_at_the_hazard(self):
        self.assertIn("chain-merge", self.body)
        self.assertIn(HAZARD_PAGE, self.body)
        self.assertTrue((REPO_ROOT / HAZARD_PAGE).is_file())

    def test_it_names_every_skill_that_recites_it(self):
        for slug in WORK_STARTING:
            with self.subTest(skill=slug):
                self.assertIn(f"`{slug}`", self.body)


class TestWorkStartingSkillsRecite(unittest.TestCase):
    def test_each_names_the_protocol_section(self):
        for slug in WORK_STARTING:
            with self.subTest(skill=slug):
                self.assertIn(PREFLIGHT_HEADING.lower(),
                              flat(skill_text(slug)))

    def test_next_runs_it_before_the_hand_off(self):
        text = flat(skill_text("next"))
        self.assertLess(text.index(PREFLIGHT_HEADING.lower()),
                        text.index("load the matching stage skill"))

    def test_autorun_runs_it_before_its_first_stage(self):
        text = flat(skill_text("autorun"))
        self.assertLess(text.index(PREFLIGHT_HEADING.lower()),
                        text.index("dispatch one subagent"))

    def test_conduct_reports_it_before_the_spend_ask(self):
        text = flat(skill_text("conduct"))
        self.assertLess(text.index(PREFLIGHT_HEADING.lower()),
                        text.index("queues the spend ask"))


if __name__ == "__main__":
    unittest.main()
