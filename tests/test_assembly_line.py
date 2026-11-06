"""assembly_line.py (feature:assembly-line): the factory model and page
writer — every run in a repo exactly once (active, completed or
attention), its dated station history, its work orders, and the
self-contained page that draws them.

Pinned against tempfile fixture trees, the board.py seam discipline:
functions take root and read real files under it.
"""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import assembly_line  # noqa: E402
import board  # noqa: E402
from protocol import breakdown_path, checkbox_progress  # noqa: E402


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def frontmatter(**fields):
    lines = "\n".join(f"{key}: {value}" for key, value in fields.items())
    return f"---\n{lines}\n---\n"


def artifact(stage, day, extra="", **fields):
    return frontmatter(stage=stage, date=day, **fields) + extra


def build_snapshot_tree(tmp):
    """One run of every shape the floor must place."""
    root = Path(tmp)
    features = root / "docs" / "features"
    fixes = root / "docs" / "fixes"
    # Feature at Implement, one of two rows done.
    building = features / "building"
    write(building / "idea.md", artifact("idea", "2026-10-01"))
    write(building / "prd.md", artifact("prd", "2026-10-02",
                                        ux="required"))
    write(building / "ux.md", artifact("ux-design", "2026-10-03"))
    write(building / "architecture.md", artifact("architect", "2026-10-04"))
    write(building / "breakdown.md", artifact(
        "decompose", "2026-10-05",
        "- [x] **WO-0001** First part — size:S\n"
        "- [ ] **WO-0002** Second part — size:S\n"))
    # Feature whose PRD skipped UX, at Architect.
    lean = features / "lean"
    write(lean / "idea.md", artifact("idea", "2026-10-01"))
    write(lean / "prd.md", artifact("prd", "2026-10-01",
                                    ux="not-applicable",
                                    **{"ux-reason": "no surface"}))
    # Maintenance, re-entry implement: boxes inline in defect.md.
    inline = fixes / "inline"
    write(inline / "defect.md", artifact(
        "capture", "2026-10-06", "- [ ] fix the thing\n- [x] add a test\n",
        **{"re-entry": "implement"}))
    # Maintenance, re-entry architect, at Architect.
    deep = fixes / "deep"
    write(deep / "defect.md", artifact("capture", "2026-10-07",
                                       **{"re-entry": "architect"}))
    # Completed with the population line.
    done = features / "done"
    for stage, name, day in [
            ("idea", "idea.md", "2026-09-01"), ("prd", "prd.md", "2026-09-01"),
            ("architect", "architecture.md", "2026-09-02"),
            ("verify", "verification.md", "2026-09-04"),
            ("review", "review.md", "2026-09-04"),
            ("ship", "release.md", "2026-09-05")]:
        write(done / name, artifact(stage, day))
    write(done / "prd.md", artifact("prd", "2026-09-01",
                                    ux="not-applicable",
                                    **{"ux-reason": "none"}))
    write(done / "breakdown.md", artifact("decompose", "2026-09-03",
                                          "- [x] **WO-0003** Only part\n"))
    write(done / "retro.md", artifact("operate", "2026-09-06",
                                      **{"users-observed": "0",
                                         "signal-source": "none yet"}))
    # Completed before ADR-0102: retro with neither population field.
    old = features / "old"
    write(old / "idea.md", artifact("idea", "2026-08-01"))
    write(old / "retro.md", artifact("operate", "2026-08-09"))
    # Unreadable: implement must decode bytes that do not decode.
    bad = fixes / "bad"
    write(bad / "defect.md", artifact("capture", "2026-10-08",
                                      **{"re-entry": "implement"}))
    (bad / "defect.md").write_bytes(
        (bad / "defect.md").read_bytes() + b"- [ ] broken \xff\xfe\n")
    # Gapped ladder: at PRD, but an architecture already written.
    gap = features / "gap"
    write(gap / "idea.md", artifact("idea", "2026-10-09"))
    write(gap / "architecture.md", artifact("architect", "2026-10-10"))
    # The docs/ root holding only architecture.md: the product run.
    write(root / "docs" / "architecture.md", "# Architecture\n")
    # A directory holding no run artifact is not a run.
    write(features / "notes" / "scratch.md", "nothing\n")
    return root


class TestSnapshot(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = build_snapshot_tree(self.tmp.name)
        self.model, self.problems = assembly_line.gather(self.root)
        self.runs = {run["dir"]: run for run in self.model["runs"]}

    def tearDown(self):
        self.tmp.cleanup()

    def test_every_run_directory_appears_exactly_once(self):
        self.assertEqual(self.problems, [])
        dirs = [run["dir"] for run in self.model["runs"]]
        self.assertEqual(len(dirs), len(set(dirs)))
        self.assertEqual(sorted(dirs), sorted([
            "docs", "docs/features/building", "docs/features/done",
            "docs/features/gap", "docs/features/lean", "docs/features/old",
            "docs/fixes/bad", "docs/fixes/deep", "docs/fixes/inline"]))

    def test_active_runs_are_placed_exactly_as_board_places_them(self):
        placed, _ = board.gather(self.root)
        self.assertTrue(placed["runs"])
        for entry in placed["runs"]:
            run = self.runs[entry["dir"]]
            current = next(row["stage"] for row in entry["ladder"]
                           if row["state"] == "current")
            self.assertEqual(run["status"], "active")
            self.assertEqual(run["station"], current)
            self.assertEqual(run["ladder"], entry["ladder"])
            self.assertEqual((run["ref"], run["kind"], run["slug"]),
                             (entry["ref"], entry["kind"], entry["slug"]))

    def test_stations_cover_both_ladders_and_completed(self):
        self.assertEqual(self.model["stations"], [
            "capture", "idea", "prd", "ux-design", "architect", "decompose",
            "implement", "verify", "review", "ship", "operate", "completed"])

    def test_completed_runs_sit_only_in_completed(self):
        for rel in ("docs/features/done", "docs/features/old"):
            run = self.runs[rel]
            self.assertEqual(run["status"], "completed")
            self.assertEqual(run["station"], "completed")
            # Complete is orientation's word: a populated retro closes
            # the run whatever lies before it, so no row is current.
            self.assertNotIn("current",
                             [row["state"] for row in run["ladder"]])

    def test_unreadable_run_is_attention_with_boards_reason(self):
        placed, _ = board.gather(self.root)
        reason = next(entry["reason"] for entry in placed["attention"]
                      if entry["dir"] == "docs/fixes/bad")
        run = self.runs["docs/fixes/bad"]
        self.assertEqual(run["status"], "attention")
        self.assertIsNone(run["station"])
        self.assertEqual(run["reason"], reason)
        self.assertEqual(run["history"], [])
        self.assertEqual(run["ref"], "maintenance:bad")

    def test_gapped_ladder_keeps_its_done_ahead_stage(self):
        run = self.runs["docs/features/gap"]
        self.assertEqual(run["station"], "prd")
        states = {row["stage"]: row["state"] for row in run["ladder"]}
        self.assertEqual(states["architect"], "done")

    def test_product_run_is_placed_as_board_places_it(self):
        run = self.runs["docs"]
        self.assertEqual((run["ref"], run["kind"]), ("product", "product"))
        self.assertEqual(run["station"], "idea")

    def test_work_orders_list_each_row_for_runs_at_or_past_implement(self):
        expected = {
            "docs/features/building": [
                {"title": "First part", "done": True},
                {"title": "Second part", "done": False}],
            "docs/fixes/inline": [
                {"title": "fix the thing", "done": False},
                {"title": "add a test", "done": True}],
            "docs/features/done": [{"title": "Only part", "done": True}],
        }
        for rel, rows in expected.items():
            run = self.runs[rel]
            self.assertEqual(run["work_orders"], rows, rel)
            _, total = checkbox_progress(breakdown_path(self.root / rel))
            self.assertEqual(len(run["work_orders"]), total, rel)
        for rel in ("docs/features/lean", "docs/fixes/deep",
                    "docs/features/gap", "docs/fixes/bad"):
            self.assertEqual(self.runs[rel]["work_orders"], [], rel)

    def test_no_docs_tree_is_boards_problem_and_no_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            model, problems = assembly_line.gather(tmp)
            placed, board_problems = board.gather(tmp)
            self.assertIsNone(model)
            self.assertEqual(problems, board_problems)

    def test_empty_docs_tree_is_an_empty_floor(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "docs").mkdir()
            model, problems = assembly_line.gather(tmp)
            self.assertEqual(problems, [])
            self.assertEqual(model["runs"], [])
            self.assertTrue(model["repo"])
            self.assertTrue(model["generated"])


if __name__ == "__main__":
    unittest.main()
