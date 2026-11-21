"""board.py (WO-0047, feature:pipeline-board): the board-model CLI —
every active run placed on its own ladder, as one JSON document. Facts
only, per ADR-0062: the pipeline-board skill renders this verbatim.

Pinned against tempfile fixture trees (the orientation_pack/assembler
seam discipline: functions take root and read real files under it).
"""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import board  # noqa: E402


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def frontmatter(**fields):
    lines = "\n".join(f"{key}: {value}" for key, value in fields.items())
    return f"---\n{lines}\n---\n"


class TestGather(unittest.TestCase):
    def test_no_docs_tree_is_the_one_repo_level_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            model, problems = board.gather(tmp)
            self.assertIsNone(model)
            self.assertEqual(len(problems), 1)
            self.assertTrue(problems[0].startswith("board: "))

    def test_empty_board_is_a_model_not_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "docs").mkdir()
            model, problems = board.gather(tmp)
            self.assertEqual(problems, [])
            self.assertEqual(model["runs"], [])
            self.assertEqual(model["attention"], [])
            self.assertTrue(model["generated"])
            self.assertTrue(model["repo"])

    def build_mixed_tree(self, tmp):
        root = Path(tmp)
        # A feature run at prd (idea.md only).
        write(root / "docs" / "features" / "young" / "idea.md",
              frontmatter(stage="idea", run="feature:young"))
        # A maintenance run at implement, boxes inline in defect.md
        # (re-entry: implement), one of two checked.
        write(root / "docs" / "fixes" / "deep" / "defect.md",
              frontmatter(stage="capture", **{"re-entry": "implement"})
              + "- [x] first\n- [ ] second\n")
        # A completed run — never on the board.
        write(root / "docs" / "features" / "shipped" / "idea.md", "x")
        write(root / "docs" / "features" / "shipped" / "retro.md", "x")
        # An unorientable run: implement must read bytes that do not
        # decode, so orientation fails for this run and this run only.
        bad = root / "docs" / "fixes" / "bad"
        write(bad / "defect.md",
              frontmatter(stage="capture", **{"re-entry": "implement"}))
        (bad / "defect.md").write_bytes(
            (bad / "defect.md").read_bytes() + b"- [ ] broken \xff\xfe\n")
        return root

    def test_mixed_tree_partitions_and_sorts(self):
        with tempfile.TemporaryDirectory() as tmp:
            model, problems = board.gather(self.build_mixed_tree(tmp))
            self.assertEqual(problems, [])
            # Partition: active runs in runs, the undecodable one in
            # attention, the completed one nowhere.
            self.assertEqual([run["slug"] for run in model["runs"]],
                             ["deep", "young"])  # furthest-along first
            self.assertEqual([entry["dir"] for entry in model["attention"]],
                             ["docs/fixes/bad"])
            self.assertTrue(model["attention"][0]["reason"])
            self.assertNotIn("\n", model["attention"][0]["reason"])

    def test_run_entries_carry_the_contract_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            model, _ = board.gather(self.build_mixed_tree(tmp))
            deep, young = model["runs"]
            self.assertEqual(deep["ref"], "maintenance:deep")
            self.assertEqual(deep["kind"], "maintenance")
            self.assertEqual(deep["dir"], "docs/fixes/deep")
            self.assertEqual(deep["progress"], {"done": 1, "total": 2})
            self.assertEqual(young["ref"], "feature:young")
            self.assertEqual(young["kind"], "feature")
            self.assertIsNone(young["progress"])
            ladder = dict((row["stage"], row["state"])
                          for row in deep["ladder"])
            self.assertEqual(ladder["implement"], "current")
            self.assertEqual(ladder["architect"], "skipped")
            young_states = [row["state"] for row in young["ladder"]]
            self.assertEqual(young_states.count("current"), 1)


class TestBoardEdges(unittest.TestCase):
    """Found by the 2026-11-20 board audit."""

    def test_a_feature_run_holding_defect_md_is_kind_maintenance(self):
        # It walks the maintenance ladder; a renderer keyed on kind would
        # map its 8 rungs onto the feature columns.
        with tempfile.TemporaryDirectory() as tmp:
            write(Path(tmp) / "docs" / "features" / "f" / "defect.md",
                  frontmatter(stage="capture", **{"re-entry": "implement"})
                  + "- [ ] a\n")
            model, _ = board.gather(tmp)
            (run,) = model["runs"]
            self.assertEqual((run["ref"], run["kind"], run["ladder"][0]),
                             ("feature:f", "maintenance",
                              {"stage": "capture", "state": "done"}))

    def gather_unreadable(self, tmp, path):
        path.chmod(0)
        try:
            return board.gather(tmp)
        finally:
            path.chmod(0o755)

    def test_an_unreadable_run_directory_is_in_attention(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / "docs" / "features" / "locked"
            write(run / "idea.md", "x")
            model, problems = self.gather_unreadable(tmp, run)
            self.assertEqual(problems, [])
            self.assertEqual([a["dir"] for a in model["attention"]],
                             ["docs/features/locked"])

    def test_an_unreadable_features_directory_does_not_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            features = Path(tmp) / "docs" / "features"
            write(features / "f" / "idea.md", "x")
            model, problems = self.gather_unreadable(tmp, features)
            self.assertEqual(problems, [])
            (entry,) = model["attention"]
            self.assertIn("features", entry["reason"])

    def test_a_long_reason_is_cut_to_one_row(self):
        text = board.reason(OSError("x" * 500))
        self.assertEqual(len(text), board.REASON_MAX)
        self.assertTrue(text.endswith("…"))


class TestMain(unittest.TestCase):
    def test_success_prints_the_model_as_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "docs").mkdir()
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = board.main([tmp])
            self.assertEqual(code, 0)
            model = json.loads(out.getvalue())
            self.assertEqual(model["runs"], [])

    def test_help_flag_prints_usage_and_exits_zero(self):
        for flag in ("-h", "--help"):
            with self.subTest(flag=flag):
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    code = board.main([flag])
                self.assertEqual(code, 0)
                self.assertEqual(out.getvalue().strip(), board.USAGE)

    def test_failure_prints_problems_and_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = board.main([tmp])
            self.assertEqual(code, 1)
            self.assertIn("board: 1 problem(s)", out.getvalue())


if __name__ == "__main__":
    unittest.main()
