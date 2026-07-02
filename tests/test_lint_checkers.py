"""Lint-checker seam: every checker takes the repo root as a parameter,
so seeded temp trees are a second adapter beside the real repo.

Trees are built programmatically (not committed like the orientation
fixtures) because the clean tree must track protocol.py's taxonomy —
committed copies would duplicate those constants and rot. Each defect
test seeds the clean tree, breaks one aspect, and asserts the checker's
exact problem strings through its public interface.
"""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import lint  # noqa: E402
from protocol import ALL_SKILLS, STAGES, TEMPLATED_STAGES  # noqa: E402


def make_clean_tree(root):
    """Seed the smallest tree on which every checker reports zero problems."""
    plugin_dir = root / ".claude-plugin"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "plugin.json").write_text(json.dumps(
        {"name": "t", "description": "t", "version": "0"}), encoding="utf-8")

    for slug in ALL_SKILLS:
        skill_dir = root / "skills" / slug
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {slug}\ndescription: d\n---\n\nbody\n",
            encoding="utf-8")
    for slug in TEMPLATED_STAGES:
        (root / "skills" / slug / "TEMPLATE.md").write_text(
            "t\n", encoding="utf-8")
    (root / "skills" / "next" / "SKILL.md").write_text(
        "---\nname: next\ndescription: d\n---\n\n" + " ".join(STAGES) + "\n",
        encoding="utf-8")

    (root / "docs").mkdir()
    (root / "docs" / "pipeline-protocol.md").write_text("spec\n",
                                                        encoding="utf-8")

    cases = [{"id": f"{slug}-{n}", "kind": "direct",
              "expected": slug, "query": "q"}
             for slug in ALL_SKILLS for n in range(3)]
    cases += [{"id": f"none-{n}", "kind": "distractor",
               "expected": None, "query": "q"} for n in range(3)]
    (root / "evals").mkdir()
    (root / "evals" / "routing.json").write_text(
        json.dumps({"version": 1, "cases": cases}), encoding="utf-8")

    fixture = root / "evals" / "fixtures" / "seeded-run"
    fixture.mkdir(parents=True)
    (root / "evals" / "output").mkdir()
    (root / "evals" / "output" / "idea.json").write_text(json.dumps({
        "skill_name": "idea",
        "evals": [{"id": 1, "expectations": ["x"],
                   "run_fixture": "evals/fixtures/seeded-run"}],
    }), encoding="utf-8")

    (root / "LEDGER.md").write_text(
        "".join(f"| {slug} |\n" for slug in ALL_SKILLS), encoding="utf-8")


class CheckerTreeTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="lint-tree-"))
        self.addCleanup(shutil.rmtree, self.root)
        make_clean_tree(self.root)


class TestCleanTree(CheckerTreeTest):
    def test_every_checker_reports_zero_problems(self):
        for checker in lint.CHECKERS:
            with self.subTest(checker=checker.__name__):
                self.assertEqual(checker(self.root), [])


class TestManifest(CheckerTreeTest):
    def test_missing_field(self):
        path = self.root / ".claude-plugin" / "plugin.json"
        path.write_text(json.dumps({"name": "t", "version": "0"}),
                        encoding="utf-8")
        self.assertEqual(lint.check_manifest(self.root),
                         ["plugin.json missing field: description"])


class TestSkills(CheckerTreeTest):
    def test_name_mismatch(self):
        (self.root / "skills" / "idea" / "SKILL.md").write_text(
            "---\nname: notidea\ndescription: d\n---\n\nbody\n",
            encoding="utf-8")
        self.assertEqual(
            lint.check_skills(self.root),
            ["skills/idea/SKILL.md frontmatter name is 'notidea', "
             "expected 'idea'"])

    def test_no_frontmatter_and_no_description_are_distinct(self):
        (self.root / "skills" / "idea" / "SKILL.md").write_text(
            "body only\n", encoding="utf-8")
        (self.root / "skills" / "prd" / "SKILL.md").write_text(
            "---\nname: prd\n---\n\nbody\n", encoding="utf-8")
        self.assertEqual(
            lint.check_skills(self.root),
            ["skills/idea/SKILL.md has no frontmatter block",
             "skills/prd/SKILL.md frontmatter has no description"])


class TestTemplates(CheckerTreeTest):
    def test_missing_template(self):
        (self.root / "skills" / "verify" / "TEMPLATE.md").unlink()
        self.assertEqual(lint.check_templates(self.root),
                         ["missing skills/verify/TEMPLATE.md"])


class TestRouter(CheckerTreeTest):
    def test_omitted_stage(self):
        mentions = " ".join(s for s in STAGES if s != "ship")
        (self.root / "skills" / "next" / "SKILL.md").write_text(
            "---\nname: next\ndescription: d\n---\n\n" + mentions + "\n",
            encoding="utf-8")
        self.assertEqual(lint.check_router(self.root),
                         ["router never mentions stage skill 'ship'"])


class TestProtocol(CheckerTreeTest):
    def test_missing_spec(self):
        (self.root / "docs" / "pipeline-protocol.md").unlink()
        self.assertEqual(lint.check_protocol(self.root),
                         ["missing docs/pipeline-protocol.md"])


class TestEvals(CheckerTreeTest):
    def test_invalid_expected_and_thin_coverage(self):
        data = json.loads(
            (self.root / "evals" / "routing.json").read_text(encoding="utf-8"))
        case = next(c for c in data["cases"] if c["id"] == "idea-0")
        case["expected"] = "bogus"
        (self.root / "evals" / "routing.json").write_text(
            json.dumps(data), encoding="utf-8")
        problems = lint.check_evals(self.root)
        self.assertIn("evals/routing.json case 'idea-0' has invalid "
                      "expected 'bogus'", problems)
        self.assertIn("evals/routing.json covers skill 'idea' in only "
                      "2 case(s), need >= 3", problems)


class TestOutputEvals(CheckerTreeTest):
    def test_skill_name_mismatch_and_missing_fixture(self):
        output_dir = self.root / "evals" / "output"
        (output_dir / "idea.json").write_text(json.dumps({
            "skill_name": "prd",
            "evals": [{"id": 1, "expectations": ["x"],
                       "run_fixture": "evals/fixtures/absent"}],
        }), encoding="utf-8")
        self.assertEqual(
            lint.check_output_evals(self.root),
            ["evals/output/idea.json skill_name is 'prd', expected 'idea'",
             "evals/output/idea.json eval 1 run_fixture "
             "'evals/fixtures/absent' does not exist"])


class TestLedger(CheckerTreeTest):
    def test_missing_row(self):
        (self.root / "LEDGER.md").write_text(
            "".join(f"| {slug} |\n" for slug in ALL_SKILLS
                    if slug != "operate"), encoding="utf-8")
        self.assertEqual(lint.check_ledger(self.root),
                         ["LEDGER.md has no row for skill 'operate'"])


if __name__ == "__main__":
    unittest.main()
