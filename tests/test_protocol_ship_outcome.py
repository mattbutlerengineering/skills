"""The Ship outcome (issue #942, ADR-0101): Ship completes on the outcome
release.md records, not on the file existing.

Under prepare-and-stop a release.md said "prepared, not released" for
days after its pull request merged, nothing wrote the merge back, and
"complete when: file exists" let Operate write a retro over a release
artifact that disagreed with production. Now release.md records the
outcome Ship actually reached in frontmatter — `outcome: released |
rolled-back | prepared`, with `pending-merge: <PR url>` while prepared —
and only a reached outcome completes the stage.

Two halves. The predicate, pinned through next_stage and stage_states
on temp run directories (the fixture trees under tests/fixtures/ pin
the prepared row of both tables the way every other row is pinned).
And the recitals: the protocol doc owns the vocabulary and the
write-back once; ship, operate, next and autorun point at it.
"""
import tempfile
import unittest
from pathlib import Path

import protocol
from protocol import SHIP_OUTCOMES, next_stage, stage_states

REPO_ROOT = Path(__file__).resolve().parent.parent
PROTOCOL_DOC = REPO_ROOT / "docs" / "pipeline-protocol.md"

HEADING = "The Ship outcome"
PR_URL = "https://github.com/acme/widgets/pull/42"
# The artifacts of a feature run that has reached Ship.
UPSTREAM = ("idea.md", "prd.md", "architecture.md", "verification.md",
            "review.md")


def feature_run(tmp, release_frontmatter):
    """A feature run directory with every artifact through Review, a
    fully checked breakdown, and a release.md carrying the given extra
    frontmatter lines (None for no release.md at all)."""
    run = Path(tmp)
    for name in UPSTREAM:
        (run / name).write_text(
            f"---\nstage: x\nrun: feature:t\ndate: 2026-07-01\n"
            f"{'ux: not-applicable' if name == 'prd.md' else ''}\n---\n",
            encoding="utf-8")
    (run / "breakdown.md").write_text("- [x] one\n", encoding="utf-8")
    if release_frontmatter is not None:
        (run / "release.md").write_text(
            "---\nstage: ship\nrun: feature:t\ndate: 2026-07-02\n"
            + release_frontmatter + "---\n\n# Release\n", encoding="utf-8")
    return run


class TestShipCompletesOnTheOutcome(unittest.TestCase):
    def test_the_vocabulary_is_the_three_outcomes(self):
        self.assertEqual(SHIP_OUTCOMES, ("released", "rolled-back",
                                         "prepared"))

    def test_released_completes_ship(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = feature_run(tmp, "outcome: released\n"
                                   "released-at: 2026-07-03\n")
            self.assertEqual(next_stage(run), "operate")

    def test_rolled_back_is_a_reached_outcome_and_completes_ship(self):
        # The ship skill's own rule: a failed ship whose rollback plan
        # ran is a valid, complete release.md.
        with tempfile.TemporaryDirectory() as tmp:
            run = feature_run(tmp, "outcome: rolled-back\n")
            self.assertEqual(next_stage(run), "operate")

    def test_prepared_leaves_ship_pending(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = feature_run(tmp, f"outcome: prepared\n"
                                   f"pending-merge: {PR_URL}\n")
            self.assertEqual(next_stage(run), "ship")

    def test_prepared_without_a_pull_request_is_still_prepared(self):
        # pending-merge: names what to check; its absence is not a
        # release.
        with tempfile.TemporaryDirectory() as tmp:
            run = feature_run(tmp, "outcome: prepared\n")
            self.assertEqual(next_stage(run), "ship")

    def test_an_unknown_outcome_leaves_ship_pending(self):
        # Fail closed: a value outside the vocabulary is not a reached
        # outcome, and the router says so rather than routing past it.
        with tempfile.TemporaryDirectory() as tmp:
            run = feature_run(tmp, "outcome: pending\n")
            self.assertEqual(next_stage(run), "ship")

    def test_a_release_md_with_no_outcome_field_still_completes_ship(self):
        # Every release.md written before the field existed — dozens in
        # this repo alone — records no outcome because none was asked
        # for, not because the release is waiting. ADR-0101 keeps those
        # complete; strictness here would move every one of them back
        # to Ship on the board and the dashboard.
        with tempfile.TemporaryDirectory() as tmp:
            run = feature_run(tmp, "")
            self.assertEqual(next_stage(run), "operate")

    def test_no_release_md_is_still_ship(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = feature_run(tmp, None)
            self.assertEqual(next_stage(run), "ship")

    def test_a_retro_still_short_circuits_a_prepared_release(self):
        # The run-complete rule keys on retro.md alone; a retro written
        # over a prepared release is the defect the operate skill now
        # refuses, not something orientation undoes after the fact.
        with tempfile.TemporaryDirectory() as tmp:
            run = feature_run(tmp, f"outcome: prepared\n"
                                   f"pending-merge: {PR_URL}\n")
            (run / "retro.md").write_text("---\nstage: operate\n---\n",
                                          encoding="utf-8")
            self.assertEqual(next_stage(run), "complete")

    def test_stage_states_shows_a_prepared_release_as_current(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = feature_run(tmp, f"outcome: prepared\n"
                                   f"pending-merge: {PR_URL}\n")
            states = dict(stage_states(run))
            self.assertEqual(states["ship"], "current")
            self.assertEqual(states["operate"], "ahead")


class TestMaintenanceShipCompletesOnTheOutcome(unittest.TestCase):
    def maintenance_run(self, tmp, release_frontmatter):
        run = Path(tmp) / "docs" / "fixes" / "login-timeout"
        run.mkdir(parents=True)
        (run / "defect.md").write_text(
            "---\nstage: capture\nrun: maintenance:login-timeout\n"
            "date: 2026-07-01\nre-entry: implement\n---\n\n- [x] fix\n",
            encoding="utf-8")
        for name in ("verification.md", "review.md"):
            (run / name).write_text("---\nstage: x\n---\n", encoding="utf-8")
        (run / "release.md").write_text(
            "---\nstage: ship\nrun: maintenance:login-timeout\n"
            "date: 2026-07-02\n" + release_frontmatter + "---\n",
            encoding="utf-8")
        return run

    def test_prepared_leaves_a_maintenance_run_at_ship(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = self.maintenance_run(tmp, f"outcome: prepared\n"
                                            f"pending-merge: {PR_URL}\n")
            self.assertEqual(next_stage(run), "ship")

    def test_released_moves_a_maintenance_run_to_operate(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = self.maintenance_run(tmp, "outcome: released\n")
            self.assertEqual(next_stage(run), "operate")


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


class TestProtocolStatesTheOutcome(unittest.TestCase):
    def setUp(self):
        self.body = flat(section(PROTOCOL_DOC.read_text(encoding="utf-8"),
                                 HEADING))

    def test_it_states_the_vocabulary(self):
        for outcome in SHIP_OUTCOMES:
            with self.subTest(outcome=outcome):
                self.assertIn(f"`{outcome}`", self.body)
        self.assertIn("`pending-merge: <pr url>`", self.body)
        self.assertIn("`released-at:`", self.body)

    def test_a_reached_outcome_completes_and_prepared_does_not(self):
        self.assertIn("only a reached outcome completes the stage",
                      self.body)
        self.assertIn("`prepared` leaves ship pending", self.body)

    def test_the_write_back_names_both_forge_cli_forms(self):
        # The GraphQL-backed form, and the REST form that works in a
        # cloud session (issue #945).
        self.assertIn("`gh pr view <n> --json state,mergedat`", self.body)
        self.assertIn("`gh api repos/{owner}/{repo}/pulls/<n> "
                      "--jq '{merged,merged_at}'`", self.body)

    def test_it_names_its_three_reciters(self):
        for slug in ("ship", "operate", "next"):
            with self.subTest(skill=slug):
                self.assertIn(f"`{slug}`", self.body)

    def test_the_both_tables_ship_rows_point_here(self):
        text = PROTOCOL_DOC.read_text(encoding="utf-8")
        rows = [line for line in text.splitlines()
                if line.startswith("| Ship |")]
        self.assertEqual(len(rows), 2)
        for row in rows:
            self.assertIn("`outcome:`", row)
            self.assertIn("`prepared`", row)


class TestSkillsRecite(unittest.TestCase):
    def test_each_reciter_names_the_section(self):
        for slug in ("ship", "operate", "next", "autorun"):
            with self.subTest(skill=slug):
                self.assertIn(HEADING.lower(), flat(skill_text(slug)))

    def test_ship_records_the_pending_merge_under_prepare_and_stop(self):
        text = flat(skill_text("ship"))
        self.assertIn("`outcome: prepared`", text)
        self.assertIn("`pending-merge: <pr url>`", text)

    def test_operate_never_writes_a_retro_over_a_prepared_release(self):
        text = flat(skill_text("operate"))
        gate = text[text.index("soft gate"):text.index("let it breathe")]
        self.assertIn("`outcome: prepared`", gate)
        self.assertIn("never written over a release that is still waiting",
                      gate)

    def test_autorun_says_what_a_prepared_release_records(self):
        text = flat(skill_text("autorun"))
        self.assertIn("`outcome: prepared`", text)


if __name__ == "__main__":
    unittest.main()
