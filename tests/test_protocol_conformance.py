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


if __name__ == "__main__":
    unittest.main()
