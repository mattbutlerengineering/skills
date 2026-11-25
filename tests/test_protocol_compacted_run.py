"""A compacted run is complete (#2058).

The operate skill offers, once retro.md is committed, to collapse a
feature or fix run directory into one summary.md (keeping prd.md when
it declares a typed id and breakdown.md when a row carries a work
order, since detector C resolves those ids only there). Without a rule
for it, a directory holding summary.md alone orients as a fresh run
(idea / capture) and one that kept prd.md orients mid-ladder. The
protocol reads summary.md in a feature or fix run as complete; the
product run at docs/ is not covered, since docs/ holds the project's
own docs too.

Pinned through the public interfaces: protocol.next_stage and
stage_states, knowledge_plane.active_runs, and board.gather.
"""
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import board  # noqa: E402
from knowledge_plane import active_runs  # noqa: E402
from protocol import (MAINTENANCE_STAGE_ARTIFACTS, STAGE_ARTIFACTS,  # noqa: E402
                      next_stage, stage_states)

SUMMARY = ("---\nstage: summary\nrun: feature:dark-mode\n"
           "date: 2026-11-24\n---\n\n# Summary\n")
PRD = ("---\nstage: prd\nrun: feature:dark-mode\ndate: 2026-11-01\n"
       "id: PRD-0007\nux: not-applicable\nux-reason: CLI only\n---\n")


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class TestCompactedOrientation(unittest.TestCase):
    def test_feature_run_holding_only_summary_is_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / "docs" / "features" / "dark-mode"
            write(run / "summary.md", SUMMARY)
            self.assertEqual(next_stage(run), "complete")

    def test_fix_run_holding_only_summary_is_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / "docs" / "fixes" / "login-crash"
            write(run / "summary.md", SUMMARY)
            self.assertEqual(next_stage(run), "complete")

    def test_summary_beside_a_kept_prd_is_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / "docs" / "features" / "dark-mode"
            write(run / "summary.md", SUMMARY)
            write(run / "prd.md", PRD)
            self.assertEqual(next_stage(run), "complete")

    def test_an_unpopulated_retro_still_settles_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / "docs" / "features" / "dark-mode"
            write(run / "summary.md", SUMMARY)
            write(run / "retro.md",
                  "---\nstage: operate\nusers-observed: 3\n---\n")
            self.assertEqual(next_stage(run), "operate")

    def test_product_run_summary_is_not_a_compaction(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            write(docs / "summary.md", SUMMARY)
            write(docs / "idea.md", "---\nstage: idea\n---\n")
            self.assertEqual(next_stage(docs), "prd")

    def test_compacted_feature_ladder_is_all_done(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / "docs" / "features" / "dark-mode"
            write(run / "summary.md", SUMMARY)
            write(run / "prd.md", PRD)
            self.assertEqual(stage_states(run),
                             [(stage, "done") for stage, _ in STAGE_ARTIFACTS])

    def test_compacted_fix_ladder_is_all_done(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / "docs" / "fixes" / "login-crash"
            write(run / "summary.md", SUMMARY)
            self.assertEqual(stage_states(run),
                             [(stage, "done")
                              for stage, _ in MAINTENANCE_STAGE_ARTIFACTS])


class TestCompactedRunsAreNotActive(unittest.TestCase):
    def test_active_runs_skips_a_compacted_run_that_kept_its_prd(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run = root / "docs" / "features" / "dark-mode"
            write(run / "summary.md", SUMMARY)
            write(run / "prd.md", PRD)
            self.assertEqual(active_runs(root), [])

    def test_board_places_a_compacted_run_nowhere(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run = root / "docs" / "features" / "dark-mode"
            write(run / "summary.md", SUMMARY)
            write(run / "prd.md", PRD)
            when = datetime(2026, 11, 24, 12, 0, tzinfo=timezone.utc)
            model, problems = board.gather(root, clock=lambda: when)
            self.assertEqual(problems, [])
            self.assertEqual((model["runs"], model["attention"]), ([], []))


if __name__ == "__main__":
    unittest.main()
