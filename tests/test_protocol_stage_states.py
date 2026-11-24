"""The full-ladder accessor (WO-0045, feature:pipeline-board): the
protocol seam exposes what its next_stage walk already knows — every
stage of a run's own ladder with a state — so surfaces that draw the
whole ladder (board.py) never re-derive orientation.

Pinned against the same fixture trees that pin next_stage, in both
families: the invariant is that the first "current" row IS next_stage,
a complete run has no current row, and "skipped" marks completion
excused by rule (the ux: conditional, re-entry depth) rather than by
artifact.
"""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from protocol import (MAINTENANCE_STAGE_ARTIFACTS, STAGE_ARTIFACTS,  # noqa: E402
                      STAGE_STATES, next_stage, stage_states)

ORIENTATION = ROOT / "tests" / "fixtures" / "orientation"
MAINTENANCE = ROOT / "tests" / "fixtures" / "maintenance-orientation"


def orientation_cases():
    return sorted(p for p in ORIENTATION.iterdir() if p.is_dir())


def maintenance_cases():
    return sorted(p for p in MAINTENANCE.iterdir() if p.is_dir())


def maintenance_run_dir(case):
    """The case's single run directory under docs/fixes/ (the protocol's
    run-discovery rule for maintenance runs)."""
    fixes = case / "docs" / "fixes"
    runs = sorted(p for p in fixes.iterdir() if p.is_dir())
    assert len(runs) == 1, f"expected one run dir in {fixes}, got {runs}"
    return runs[0]


def all_cases():
    for case in orientation_cases():
        yield case.name, case / "run"
    for case in maintenance_cases():
        yield case.name, maintenance_run_dir(case)


class TestNextStageInvariant(unittest.TestCase):
    """stage_states agrees with next_stage on every fixture of both
    families — the placement-parity contract (PRD-0004)."""

    def test_fixtures_exist(self):
        self.assertTrue(orientation_cases())
        self.assertTrue(maintenance_cases())

    def test_first_current_is_next_stage(self):
        for name, run in all_cases():
            with self.subTest(fixture=name):
                expected = next_stage(run)
                currents = [stage for stage, state in stage_states(run)
                            if state == "current"]
                if expected == "complete":
                    self.assertEqual(currents, [])
                else:
                    self.assertEqual(currents, [expected])

    def test_every_state_is_from_the_roster(self):
        for name, run in all_cases():
            with self.subTest(fixture=name):
                for stage, state in stage_states(run):
                    self.assertIn(state, STAGE_STATES)

    def test_the_roster_is_the_five_states(self):
        self.assertEqual(STAGE_STATES, ("done", "current", "ahead",
                                        "missing", "skipped"))


class TestLadderShape(unittest.TestCase):
    """Each run's ladder is its own table's stage sequence, in order."""

    def test_feature_ladder_matches_the_table(self):
        run = orientation_cases()[0] / "run"
        self.assertEqual([stage for stage, _ in stage_states(run)],
                         [stage for stage, _ in STAGE_ARTIFACTS])

    def test_maintenance_ladder_matches_the_table(self):
        run = maintenance_run_dir(maintenance_cases()[0])
        self.assertEqual([stage for stage, _ in stage_states(run)],
                         [stage for stage, _ in MAINTENANCE_STAGE_ARTIFACTS])


class TestSkipIsNotDone(unittest.TestCase):
    """Rule-excused stages read "skipped", artifact-completed read
    "done" — the board must never imply a stage a run doesn't have
    (PRD-0004 story 2)."""

    def states(self, run):
        return dict(stage_states(run))

    def test_ux_not_applicable_is_skipped(self):
        run = ORIENTATION / "prd-ux-not-applicable" / "run"
        self.assertEqual(self.states(run)["ux-design"], "skipped")

    def test_ux_artifact_is_done(self):
        run = ORIENTATION / "ux-done" / "run"
        self.assertEqual(self.states(run)["ux-design"], "done")

    def test_implement_re_entry_skips_architect_and_decompose(self):
        run = maintenance_run_dir(MAINTENANCE / "defect-implement-unchecked")
        states = self.states(run)
        self.assertEqual(states["architect"], "skipped")
        self.assertEqual(states["decompose"], "skipped")
        self.assertEqual(states["implement"], "current")

    def test_architect_re_entry_keeps_the_chain(self):
        run = maintenance_run_dir(
            MAINTENANCE / "defect-architect-no-architecture")
        states = self.states(run)
        self.assertEqual(states["architect"], "current")
        self.assertEqual(states["decompose"], "ahead")


def write_run(tmp, files):
    """A temp feature run holding the named artifacts; retro.md, when
    named, carries the population line only if `populated`."""
    run = Path(tmp)
    for name, frontmatter in files.items():
        (run / name).write_text(
            f"---\nstage: x\nrun: feature:t\ndate: 2026-07-01\n{frontmatter}"
            "---\n", encoding="utf-8")
    return run


class TestGapBeforeCurrentIsMissing(unittest.TestCase):
    """A stage before current that is not complete was passed over, not
    yet reached: it reads "missing", never "ahead" (issue #2281). A
    retro-first run places on Operate while idea.md is its only other
    artifact; the eight stages between are its gap."""

    def test_retro_first_run_shows_its_gap_as_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = write_run(tmp, {"idea.md": "",
                                  "retro.md": "users-observed: <N>\n"})
            states = stage_states(run)
            self.assertEqual(next_stage(run), "operate")
            self.assertEqual(
                states,
                [("idea", "done"), ("prd", "missing"),
                 ("ux-design", "missing"), ("architect", "missing"),
                 ("decompose", "missing"), ("implement", "missing"),
                 ("verify", "missing"), ("review", "missing"),
                 ("ship", "missing"), ("operate", "current")])

    def test_a_complete_run_shows_its_gap_as_missing(self):
        # A populated retro completes the run whatever lies before it;
        # nothing is ahead of a complete run, so its gap is missing.
        with tempfile.TemporaryDirectory() as tmp:
            run = write_run(tmp, {
                "idea.md": "",
                "retro.md": "users-observed: 0\nsignal-source: us\n"})
            states = dict(stage_states(run))
            self.assertEqual(next_stage(run), "complete")
            self.assertEqual(states["prd"], "missing")
            self.assertNotIn("ahead", states.values())

    def test_stages_after_current_stay_ahead(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = write_run(tmp, {"idea.md": ""})
            states = dict(stage_states(run))
            self.assertEqual(states["prd"], "current")
            self.assertEqual(states["architect"], "ahead")
            self.assertNotIn("missing", states.values())

    def test_no_fixture_run_without_a_retro_has_a_missing_stage(self):
        # Without retro.md, current is the first incomplete stage, so
        # nothing before it can be incomplete.
        for name, run in all_cases():
            if (run / "retro.md").is_file():
                continue
            with self.subTest(fixture=name):
                self.assertNotIn("missing", dict(stage_states(run)).values())


class TestEveryRendererDrawsEveryState(unittest.TestCase):
    """The state set is a contract its renderers read: the board
    grammar's glyph roster, the board boilerplate's legend, and the
    assembly line's crate card. A new state nobody draws is a board
    that lies by omission."""

    GRAMMAR = ROOT / "skills" / "pipeline-board" / "references" / "board-grammar.md"
    BOILERPLATE = ROOT / "skills" / "pipeline-board" / "assets" / "boilerplate.svg"
    ASSEMBLY = ROOT / "tools" / "assembly_line.html"

    def test_the_glyph_roster_has_a_row_per_state(self):
        text = self.GRAMMAR.read_text(encoding="utf-8")
        for state in STAGE_STATES:
            with self.subTest(state=state):
                self.assertIn(f"| `{state}` |", text)

    def test_the_board_legend_names_every_state(self):
        text = self.BOILERPLATE.read_text(encoding="utf-8")
        for state in STAGE_STATES:
            with self.subTest(state=state):
                self.assertIn(f">{state}</text>", text)

    def test_the_crate_card_names_a_missing_stage(self):
        text = self.ASSEMBLY.read_text(encoding="utf-8")
        self.assertIn('row.state === "missing"', text)


if __name__ == "__main__":
    unittest.main()
