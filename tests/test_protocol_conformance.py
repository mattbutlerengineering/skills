"""docs/pipeline-protocol.md's orientation tables, bound to protocol.py.

The spec's two "Artifacts are the state" tables and protocol.py's
STAGE_ARTIFACTS / MAINTENANCE_STAGE_ARTIFACTS are a split contract:
the prose is what stage skills (vended into target repos, where this
repo's scripts don't exist) actually follow, and protocol.next_stage is
what this repo's tooling executes. Nothing else pins the two — a row
added or renamed in one place would silently diverge the other.

Making the router itself shell out to protocol.py was considered and
rejected: the skills ship as a plugin, so a target repo has the spec
prose but not this repo's modules — the prose IS the runtime interface
there. A conformance test is therefore the strongest available bridge:
it parses the spec tables and asserts they match the protocol rows,
stage for stage, artifact for artifact, in order.
"""
import re
import unittest
from pathlib import Path

import protocol

REPO_ROOT = Path(__file__).resolve().parent.parent
SPEC = REPO_ROOT / "docs" / "pipeline-protocol.md"
TABLE_HEADER = "| Stage | Artifact | Complete when |"


def spec_tables():
    """[(stage cell, artifact cell), ...] per orientation table, in order."""
    lines = SPEC.read_text(encoding="utf-8").splitlines()
    tables, i = [], 0
    while i < len(lines):
        if lines[i].strip() == TABLE_HEADER:
            rows, i = [], i + 2  # skip the header and separator rows
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                rows.append((cells[0], cells[1]))
                i += 1
            tables.append(rows)
        else:
            i += 1
    return tables


def as_protocol_rows(rows):
    """Map spec table rows onto protocol.py's (stage, artifact) shape.

    Stage display names map by lowercasing and hyphenating ("UX Design"
    -> "ux-design"). The Implement row's artifact column says "code" —
    its completion criterion counts breakdown checkboxes, and protocol.py
    encodes that substrate as breakdown.md (_all_boxes_checked).
    """
    out = []
    for stage_cell, artifact_cell in rows:
        stage = stage_cell.lower().replace(" ", "-")
        backticked = re.fullmatch(r"`([^`]+)`", artifact_cell)
        artifact = backticked.group(1) if backticked else "breakdown.md"
        out.append((stage, artifact))
    return out


class TestBacklogConsumersMatchProtocol(unittest.TestCase):
    """The seed-backlog section names its consumers: "`idea` (or `capture`),
    when starting a run from a seed, claims it in place". Same split
    contract as the tables above — the prose is the runtime interface in a
    target repo, so a consumer the spec names must actually carry the step.

    Capture parks deferred defects in that backlog. Until this was pinned,
    only `idea` carried the claim step and the router offered every seed as
    an idea, so a parked defect re-entered as a feature run — losing the
    defect brief, the re-entry depth, and the mandatory-Verify rule that is
    the whole point of the maintenance scale (issue #202).
    """

    def unwrapped(self, path):
        """Prose with its hard line wrapping collapsed to single spaces.

        Every file here is hand-wrapped at ~72 columns, so a sentence-long
        assertion would otherwise be pinned to today's wrap points and fail
        on a reflow that changed nothing.
        """
        return " ".join(path.read_text(encoding="utf-8").split())

    def skill(self, slug):
        return self.unwrapped(REPO_ROOT / "skills" / slug / "SKILL.md")

    def test_the_spec_still_names_both_consumers(self):
        self.assertIn("`idea` (or `capture`), when starting a run from a"
                      " seed, claims it in place", self.unwrapped(SPEC))

    def test_both_named_consumers_carry_the_claim_step(self):
        for slug in ("idea", "capture"):
            text = self.skill(slug)
            self.assertIn("docs/backlog.md", text, slug)
            self.assertIn("(claimed:", text,
                          f"{slug} is named as a backlog consumer but has no"
                          " claim step")

    def test_the_router_routes_a_seed_by_what_it_describes(self):
        text = self.skill("next")
        self.assertIn("starts a maintenance run through `capture`", text)
        self.assertIn("backlog", text)


class TestOrientationTablesMatchProtocol(unittest.TestCase):
    def setUp(self):
        self.tables = spec_tables()

    def test_spec_holds_exactly_the_two_orientation_tables(self):
        # a doc restructure that drops or duplicates a table must fail
        # here, not make the row comparisons vacuously pass
        self.assertEqual(len(self.tables), 2)

    def test_product_table_matches_stage_artifacts(self):
        self.assertEqual(as_protocol_rows(self.tables[0]),
                         list(protocol.STAGE_ARTIFACTS))

    def test_maintenance_table_matches_maintenance_stage_artifacts(self):
        self.assertEqual(as_protocol_rows(self.tables[1]),
                         list(protocol.MAINTENANCE_STAGE_ARTIFACTS))

    def test_spec_states_the_first_incomplete_stage_rule(self):
        # the sentence protocol.next_stage implements, pinned so the rule
        # can't be reworded away while the code keeps enforcing it
        self.assertIn(
            "Next stage = the first stage in order that is not complete.",
            SPEC.read_text(encoding="utf-8"))


class TestIntakeBoundIsStated(unittest.TestCase):
    """Issue #218. The bound follows from ADR-0026 and ADR-0032, but it
    was written nowhere a reader would find it, so it got re-derived from
    the ADRs every time someone asked how a bug becomes a run. Pinning
    the sentence keeps a future edit from quietly dropping it."""

    def unwrapped(self, path):
        """Prose with its hard line wrapping collapsed to single spaces —
        the spec is hand-wrapped, so a sentence-long assertion would
        otherwise break on a reflow that changed nothing."""
        return " ".join(path.read_text(encoding="utf-8").split())

    def test_the_spec_says_the_tracker_starts_nothing(self):
        text = self.unwrapped(SPEC)
        self.assertIn("The mirror is one-way **out**: nothing in the"
                      " tracker starts a run.", text)
        self.assertIn("intake is never a work order", text)

    def test_the_spec_names_the_bound_as_currently_unconditional(self):
        # ADR-0030's inbound leg is provisional; the spec must say the
        # bound holds *today* without implying the door is shut for good,
        # or accepting that ADR later reads as contradicting the spec.
        text = self.unwrapped(SPEC)
        self.assertIn("provisional and unimplemented", text)
        self.assertIn("holds without exception", text)


class TestRouterRoutesOnlyStageSkills(unittest.TestCase):
    """lint.check_router pins the floor — every stage skill is named — but
    nothing pinned the ceiling, and the ceiling is the ADR-0023 rule: the
    router never routes to a utility skill. A utility skill added to the
    hand-off list would route silently and nothing would object, so the
    absence is asserted here rather than assumed.
    """

    def test_the_router_names_no_utility_skill(self):
        text = (REPO_ROOT / "skills" / "next" / "SKILL.md").read_text(
            encoding="utf-8")
        named = [slug for slug in protocol.UTILITY_SKILLS if slug in text]
        self.assertEqual(named, [],
                         "the router never routes to utility skills"
                         " (ADR-0023)")


if __name__ == "__main__":
    unittest.main()
