"""factory_init.py stamp --keep-existing (issue #701) — fixture-tree tests.

A consumer repo with its own CODEOWNERS or ADR index could not adopt the
factory: stamp refuses every existing destination. The opt-in keeps the
target's own copies of the curated, non-executable seeds and reports each
one, while still refusing any collision in the executable payload and
never overwriting anything. Tests assert the exact strings callers print.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

import factory_init
import gates

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cli_contract  # noqa: E402
from fixture_tree import FixtureTree  # noqa: E402
from test_factory_init import all_files, make_factory_repo  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
MINE = "mine\n"
SEEDS = {"factory/templates/docs/adr/README.md": "seed index\n",
         "factory/templates/docs/design/system.md": "seed design\n",
         "factory/templates/.github/labels.json": "[]\n"}


class KeepCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        tree = make_factory_repo(Path(self.tmp.name) / "source")
        for rel, text in SEEDS.items():
            tree.write(rel, text)
        assert factory_init.update_manifest(tree.root) == []
        self.source = tree.root
        self.target = Path(self.tmp.name) / "target"
        self.target.mkdir()

    def have(self, *rels):
        tree = FixtureTree(self.target)
        for rel in rels:
            tree.write(rel, MINE)

    def keep(self):
        return factory_init.stamp_keeping(self.source, self.target)


class TestKeepExisting(KeepCase):
    CURATED = (".github/CODEOWNERS", ".github/factory.json",
               ".github/labels.json", "docs/adr/README.md",
               "docs/design/system.md")

    def test_curated_seeds_are_kept_and_reported(self):
        self.have(*self.CURATED)
        self.assertEqual(self.keep(), (sorted(self.CURATED), []))
        for rel in self.CURATED:
            self.assertEqual((self.target / rel).read_text(), MINE, rel)
        self.assertTrue((self.target / "Makefile").is_file())
        self.assertTrue((self.target / "tools/factory/gates.py").is_file())
        self.assertEqual(gates.check_scaffold_sync(self.target), [])

    def test_with_nothing_in_the_way_nothing_is_kept(self):
        self.assertEqual(self.keep(), ([], []))
        self.assertEqual(factory_init.stamp(self.source, Path(
            self.tmp.name) / "plain"), [])

    def test_an_executable_collision_is_still_refused_and_nothing_lands(
            self):
        executable = ("Makefile", "tools/factory/gates.py",
                      ".github/workflows/validator.yml",
                      "factory/manifest.json")
        self.have(".github/CODEOWNERS", *executable)
        self.assertEqual(self.keep(), ([], [
            f"factory-init: target already has {rel}"
            for rel in ("factory/manifest.json",
                        ".github/workflows/validator.yml", "Makefile",
                        "tools/factory/gates.py")]))
        self.assertEqual(all_files(self.target),
                         sorted((".github/CODEOWNERS",) + executable))
        for rel in all_files(self.target):
            self.assertEqual((self.target / rel).read_text(), MINE, rel)

    def test_the_default_stamp_still_refuses_a_curated_seed(self):
        self.have(".github/CODEOWNERS")
        self.assertEqual(factory_init.stamp(self.source, self.target), [
            "factory-init: target already has .github/CODEOWNERS"])
        self.assertEqual(all_files(self.target), [".github/CODEOWNERS"])


class TestKeepableIsDerived(unittest.TestCase):
    def test_only_github_config_and_doc_seeds_are_keepable(self):
        files = json.loads((REPO_ROOT / "factory/manifest.json").read_text(
            encoding="utf-8"))["files"]
        dests = [Path(factory_init.install_path(rel)[0]) for rel in files]
        keepable = sorted(d.as_posix() for d in dests
                          if factory_init.is_keepable(d))
        self.assertIn(".github/CODEOWNERS", keepable)
        self.assertIn(".github/factory.json", keepable)
        self.assertIn("docs/adr/README.md", keepable)
        self.assertNotIn("Makefile", keepable)
        self.assertEqual([d for d in keepable if not (
            d.startswith("docs/") or (d.startswith(".github/")
                                      and "/workflows/" not in d))], [])
        self.assertFalse(factory_init.is_keepable(Path("factory/x.md")))


class TestKeepCli(unittest.TestCase):
    def test_each_kept_file_is_a_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "product"
            FixtureTree(target).write(".github/CODEOWNERS", MINE)
            code, out = cli_contract.capture(
                factory_init.main, ["stamp", "--keep-existing", str(target)])
            self.assertEqual(code, 0, out)
            self.assertEqual(out.splitlines(), [
                "factory-init: kept .github/CODEOWNERS (yours — the stamp"
                " did not write it)",
                "factory-init: 0 problem(s)"])
            self.assertEqual((target / ".github/CODEOWNERS").read_text(),
                             MINE)


if __name__ == "__main__":
    unittest.main()
