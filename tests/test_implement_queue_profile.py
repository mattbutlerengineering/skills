"""implement-queue's profile-migration table (#1697).

Phase 0 tells a consumer which hooks its queue profile lacks, and what
each absence costs, from references/profile-migration.md. That file is a
second list of the skill's keys and hooks, so it can silently fall behind
the one place a hook is added (the skill's tables): a new hook with no
row would be exactly the stale-profile case the check exists to report.
These tests hold the two lists equal, by name and order, against the real
files. The skill's sentences are not pinned here or anywhere (#1747): a
substring assertion executes nothing.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "implement-queue" / "SKILL.md"
MIGRATION = (ROOT / "skills" / "implement-queue" / "references"
             / "profile-migration.md")

ROW = re.compile(r"^\|\s*`([a-z][a-z-_]*)`\s*\|", re.M)
SKILL_DIR = SKILL.parent
LINK = re.compile(r"\]\(([^)#\s]*)#([^)\s]+)\)")
HEADING = re.compile(r"^#{1,6} (.+)$", re.M)


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



def slug(heading):
    """GitHub's heading anchor: lower case, punctuation other than
    hyphens and spaces dropped, spaces to hyphens."""
    kept = re.sub(r"[^\w\- ]", "", heading.strip().lower())
    return kept.replace(" ", "-")


class TestOutcomeTable(unittest.TestCase):
    """#1796: a worker outcome with no row left issues open and
    stateless, out of the queue for good. Every outcome lands in a
    state the queue reads, or closes the issue."""

    def outcomes(self):
        skill = SKILL.read_text(encoding="utf-8")
        body = skill.split("| Outcome", 1)[1].split("\n\n", 1)[0]
        rows = [line.split("|")[1:3] for line in body.splitlines()[2:]]
        return {outcome.strip(): state.strip() for outcome, state in rows}

    def test_every_outcome_is_a_label_or_closed(self):
        skill = SKILL.read_text(encoding="utf-8")
        labels = names(skill, "| Label", "## Rules")
        self.assertIn("ready", labels)
        for outcome, state in self.outcomes().items():
            with self.subTest(outcome=outcome):
                self.assertTrue(state.startswith("closed")
                                or state.strip("`") in labels, state)

    def test_an_already_resolved_issue_is_closed(self):
        resolved = [state for outcome, state in self.outcomes().items()
                    if outcome.startswith("Already resolved")]
        self.assertEqual(len(resolved), 1)
        self.assertTrue(resolved[0].startswith("closed"))


class TestSkillAnchorsResolve(unittest.TestCase):
    """Detector I checks that a linked file exists and ignores the
    fragment, so a renamed heading breaks a pointer silently. Every
    `file.md#anchor` link inside the skill names a real heading."""

    def test_every_fragment_names_a_heading(self):
        checked = 0
        for doc in sorted(SKILL_DIR.rglob("*.md")):
            for target, anchor in LINK.findall(doc.read_text("utf-8")):
                if target.startswith(("http:", "https:")):
                    continue
                path = (doc.parent / target).resolve() if target else doc
                if not path.is_relative_to(SKILL_DIR.resolve()):
                    continue
                checked += 1
                with self.subTest(doc=doc.name, link=f"{target}#{anchor}"):
                    slugs = {slug(h) for h in HEADING.findall(
                        path.read_text(encoding="utf-8"))}
                    self.assertIn(anchor, slugs)
        self.assertGreater(checked, 10)


class TestPhase4SectionsAreLinked(unittest.TestCase):
    """#1833: references/loop-and-cleanup.md is Phase 4's overflow, and
    a section SKILL.md never links is one no session reads. Every `##`
    section in it has a `loop-and-cleanup.md#anchor` link in SKILL.md."""

    def test_every_section_is_linked_from_the_skill(self):
        cleanup = SKILL_DIR / "references" / "loop-and-cleanup.md"
        sections = {slug(h) for h in re.findall(
            r"^## (.+)$", cleanup.read_text(encoding="utf-8"), re.M)}
        self.assertGreater(len(sections), 3)
        linked = {anchor for target, anchor in LINK.findall(
            SKILL.read_text(encoding="utf-8"))
            if target == "references/loop-and-cleanup.md"}
        self.assertEqual(sections - linked, set())


class TestBlockMarkerAgrees(unittest.TestCase):
    """#1833: the reviewer contract's Retry policy counts a specialist
    block by a marker line that gate step 5 writes. A marker the gate
    never names is one no session writes, so the count misses every
    block. The two files name the same `specialist-verdict:` markers."""

    MARKER = re.compile(r"`(specialist-verdict: [^`]+)`")

    def markers(self, name):
        text = (SKILL_DIR / "references" / name).read_text(encoding="utf-8")
        return set(self.MARKER.findall(" ".join(text.split())))

    def test_gate_writes_every_marker_the_contract_counts(self):
        counted = self.markers("reviewer-contract.md")
        self.assertTrue(counted)
        self.assertEqual(self.markers("gate.md"), counted)


if __name__ == "__main__":
    unittest.main()
