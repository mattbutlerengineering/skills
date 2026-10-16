"""The stage-boundary commit (issue #943) — one statement, twelve reciters.

docs/pipeline-protocol.md's "Commit at the stage boundary" section is
the one owner of the rule that a stage ends by committing its own
artifact on the run's branch, and that an unattended run never advances
past an uncommitted one. Every stage skill's last step carries one
identical sentence that names the section rather than restating the
rule; `autorun` names it at its between-stage gate and refuses with the
artifact named.

Pins the section name, the rule's sentence, the commit subject, the
check command, the orientation carve-out, and the recitals, against the
real files. Whether an agent actually committed is not a thing a test
can know; these pin what the prose promises.
"""
import re
import unittest
from pathlib import Path

import protocol

REPO_ROOT = Path(__file__).resolve().parent.parent
PROTOCOL_DOC = REPO_ROOT / "docs" / "pipeline-protocol.md"

HEADING = "Commit at the stage boundary"
RULE = "A stage ends by committing its own artifact"
SUBJECT = "`docs(<slug>): <stage> — <one line>`"
CHECK = "`git status --porcelain -- <artifact>` prints nothing"
CARVE_OUT = "not the completion predicate"
# The one sentence every stage skill's last step carries, verbatim.
RECITAL = ("Commit the artifact on the run's branch — the protocol's "
           f'"{HEADING}" section owns the rule and the commit subject.')
# Every stage skill: the spine and the maintenance entry, protocol.py's
# to name — derived, never a second list.
STAGE_SKILLS = (*protocol.STAGES, *protocol.MAINTENANCE_STAGES)
# A numbered process step's opening (`N. **Title.**`) as it reads in
# whitespace-normalized text, where line starts are gone.
STEP_MARK = re.compile(r"(?:^|\s)\d+\. \*\*")


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


class TestProtocolStatesTheRule(unittest.TestCase):
    def setUp(self):
        self.body = flat(section(PROTOCOL_DOC.read_text(encoding="utf-8"),
                                 HEADING))

    def test_it_states_the_rule(self):
        self.assertIn(RULE.lower(), self.body)

    def test_it_fixes_the_commit_subject(self):
        self.assertIn(SUBJECT.lower(), self.body)

    def test_it_fixes_the_check(self):
        self.assertIn(CHECK.lower(), self.body)

    def test_the_commit_is_not_the_completion_predicate(self):
        # Orientation still reads the working tree (ADR-0021); the
        # commit gates autorun, not `next`.
        self.assertIn(CARVE_OUT, self.body)
        self.assertIn("`next`", self.body)

    def test_it_names_autorun_and_the_refusal(self):
        self.assertIn("`autorun`", self.body)
        self.assertIn("naming the artifact", self.body)


class TestStageSkillsRecite(unittest.TestCase):
    def test_each_carries_the_one_sentence(self):
        for slug in STAGE_SKILLS:
            with self.subTest(skill=slug):
                self.assertIn(flat(RECITAL), flat(skill_text(slug)))

    def test_each_carries_it_once_in_its_last_step(self):
        # One owner: the sentence points at the rule and never restates
        # it, so it appears exactly once, and in the step that ends the
        # stage — after the last numbered step begins.
        for slug in STAGE_SKILLS:
            with self.subTest(skill=slug):
                text = flat(skill_text(slug))
                recital = flat(RECITAL)
                self.assertEqual(text.count(recital), 1)
                last_step = max(m.start() for m in STEP_MARK.finditer(text))
                self.assertGreater(text.index(recital), last_step)


class TestAutorunGatesOnTheCommit(unittest.TestCase):
    def setUp(self):
        self.text = flat(skill_text("autorun"))

    def test_the_gate_names_the_section_and_the_check(self):
        gate = self.text[self.text.index("gate between stages"):
                         self.text.index("repeat 2–4")]
        self.assertIn(HEADING.lower(), gate)
        self.assertIn(CHECK.lower(), gate)

    def test_an_uncommitted_artifact_is_a_failed_stage_named_by_file(self):
        gate = self.text[self.text.index("gate between stages"):
                         self.text.index("repeat 2–4")]
        self.assertIn("uncommitted artifact", gate)
        self.assertIn("never advance past it", gate)
        self.assertIn("name the artifact (`<run directory>/<file>`)", gate)

    def test_the_brief_is_committed_too(self):
        # A resume in a fresh checkout has nothing else to read.
        self.assertIn("`docs(<slug>): autorun — brief`", self.text)


if __name__ == "__main__":
    unittest.main()
