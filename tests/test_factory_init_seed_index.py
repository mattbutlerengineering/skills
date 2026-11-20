"""factory_init.py's seed ADRs and the ADR index detector D checks.

factory-init decided which seed ADRs (docs/adr/NNNN-*.md) to land without
looking at docs/adr/README.md, so four stamps and updates that reported
`0 problem(s)` left the stamped repo's own gates red. Each test stamps or
updates the real payload into a temp repo, runs that repo's gates, and
pins the exact line factory-init prints.
"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import factory_init
import gates

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cli_contract  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
SEED_INDEX = REPO_ROOT / "factory/templates/docs/adr/README.md"
CLEAN = "gates: 0 problem(s)"


def adr(title, status="accepted"):
    return f"# {title}\n\n- Status: {status}\n\nBody.\n"


class SeedIndexCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        self.target = self.tmp / "product"
        (self.target / ".git").mkdir(parents=True)

    def write(self, rel, text):
        path = self.target / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def cli(self, *argv):
        code, out = cli_contract.capture(factory_init.main, list(argv))
        self.assertEqual(code, 0, out)
        return out.splitlines()

    def assert_gates_clean(self):
        result = subprocess.run(
            [sys.executable, "tools/factory/gates.py"], cwd=self.target,
            capture_output=True, text=True)
        self.assertEqual(result.stdout.splitlines()[-1:], [CLEAN],
                         result.stdout + result.stderr)


class TestStampOverTheRepoOwnADRs(SeedIndexCase):
    def test_the_seed_index_indexes_the_repo_adrs_not_the_skipped_seed(self):
        # case 1: the clashing seed was skipped (#1998) but the seed index
        # still linked it — D "links to missing file" and I "stale link"
        self.write("docs/adr/0001-use-postgres.md", adr("Use Postgres"))
        self.write("docs/adr/0007-use-redis.md",
                   adr("Use Redis", "provisional"))
        self.assertEqual(self.cli("stamp", str(self.target)), [
            "factory-init: skipped docs/adr/0001-decisions-are-recorded-"
            "here.md (its number is already 0001-use-postgres.md in this"
            " repo)",
            "factory-init: 0 problem(s)"])
        index = (self.target / "docs/adr/README.md").read_text(
            encoding="utf-8").splitlines()
        self.assertIn("| [0001](0001-use-postgres.md) | Use Postgres"
                      " | accepted |", index)
        self.assertIn("| [0007](0007-use-redis.md) | Use Redis"
                      " | provisional |", index)
        self.assertNotIn("0001-decisions-are-recorded-here.md",
                         "\n".join(index))
        self.assertTrue((self.target / "docs/adr/0002-artifacts-are-the-"
                         "state.md").is_file())
        self.assert_gates_clean()
        # update reports the same skip and keeps the fitted index
        out = self.cli("update", str(self.target))
        self.assertIn("factory-init: skipped docs/adr/0001-decisions-are-"
                      "recorded-here.md (its number is already 0001-use-"
                      "postgres.md in this repo)", out)
        self.assert_gates_clean()

    def test_with_no_adr_of_its_own_the_seed_index_lands_verbatim(self):
        self.cli("stamp", str(self.target))
        self.assertEqual((self.target / "docs/adr/README.md").read_bytes(),
                         SEED_INDEX.read_bytes())


class TestUpdateLeavesARemovedSeedRemoved(SeedIndexCase):
    def test_a_seed_adr_the_repo_deleted_is_not_recreated(self):
        # case 2: update recreated it, and the index no longer had its row
        self.cli("stamp", str(self.target))
        (self.target / "docs/adr/0003-soft-gating.md").unlink()
        index = self.target / "docs/adr/README.md"
        index.write_text("".join(
            line for line in index.read_text(encoding="utf-8").splitlines(
                keepends=True) if "[0003]" not in line), encoding="utf-8")
        self.assert_gates_clean()
        out = self.cli("update", str(self.target))
        self.assertIn("factory-init: skipped docs/adr/0003-soft-gating.md"
                      " (the kept docs/adr/README.md has no index row for"
                      " ADR-0003)", out)
        self.assertFalse(
            (self.target / "docs/adr/0003-soft-gating.md").exists())
        self.assert_gates_clean()


class TestKeptIndexDecidesTheSeeds(SeedIndexCase):
    def test_keep_existing_skips_the_seeds_a_kept_index_does_not_list(self):
        # case 4: a kept index listing the repo's own 0001-0002 left seeds
        # 0003-0006 landed and unindexed
        self.write("docs/adr/0001-use-postgres.md", adr("Use Postgres"))
        self.write("docs/adr/0002-use-redis.md", adr("Use Redis"))
        self.write("docs/adr/README.md", "# Decisions\n\n"
                   "| ADR | Decision | Status |\n|---|---|---|\n"
                   "| [0001](0001-use-postgres.md) | Use Postgres | accepted |\n"
                   "| [0002](0002-use-redis.md) | Use Redis | accepted |\n")
        held = ["factory-init: skipped docs/adr/0001-decisions-are-recorded-"
                "here.md (its number is already 0001-use-postgres.md in this"
                " repo)",
                "factory-init: skipped docs/adr/0002-artifacts-are-the-"
                "state.md (its number is already 0002-use-redis.md in this"
                " repo)"]
        unindexed = ["0003-soft-gating.md", "0004-tracker-is-a-one-way-"
                     "mirror.md", "0005-three-human-gates.md",
                     "0006-work-orders-dispatch-from-breakdown-rows.md"]
        self.assertEqual(
            self.cli("stamp", "--keep-existing", str(self.target)),
            held + [f"factory-init: skipped docs/adr/{name} (the kept"
                    f" docs/adr/README.md has no index row for"
                    f" ADR-{name[:4]})" for name in unindexed]
            + ["factory-init: kept docs/adr/README.md (yours — the stamp"
               " did not write it)",
               "factory-init: 0 problem(s)"])
        for name in unindexed:
            self.assertFalse((self.target / "docs/adr" / name).exists())
        self.assert_gates_clean()

    def test_keep_existing_lands_the_seeds_a_kept_index_lists(self):
        self.write("docs/adr/README.md", SEED_INDEX.read_text(
            encoding="utf-8"))
        self.assertEqual(
            self.cli("stamp", "--keep-existing", str(self.target)),
            ["factory-init: kept docs/adr/README.md (yours — the stamp"
             " did not write it)", "factory-init: 0 problem(s)"])
        self.assertTrue((self.target / "docs/adr/0006-work-orders-"
                         "dispatch-from-breakdown-rows.md").is_file())
        self.assert_gates_clean()

    def test_update_skips_a_new_seed_the_kept_index_does_not_list(self):
        # case 3's symptom: a release adds a seed ADR and its index row; the
        # repo's untouched index is kept, so the seed would land unindexed
        self.cli("stamp", str(self.target))
        source = self.tmp / "release"
        shutil.copytree(REPO_ROOT / "factory", source / "factory")
        seeds = source / "factory/templates/docs/adr"
        (seeds / "0007-a-new-seed.md").write_text(adr("A new seed"),
                                                   encoding="utf-8")
        (seeds / "README.md").write_text(
            SEED_INDEX.read_text(encoding="utf-8")
            + "| [0007](0007-a-new-seed.md) | A new seed | accepted |\n",
            encoding="utf-8")
        manifest = source / "factory/manifest.json"
        data = json.loads(manifest.read_text(encoding="utf-8"))
        data["files"] = gates.manifest_files(source)
        manifest.write_text(json.dumps(data, indent=2) + "\n",
                            encoding="utf-8")
        self.assertEqual(factory_init.seed_skips(source, self.target), {
            "docs/adr/0007-a-new-seed.md": "the kept docs/adr/README.md has"
            " no index row for ADR-0007"})
        written, kept, problems = factory_init.update(source, self.target)
        self.assertEqual((kept, problems), (["docs/adr/README.md"], []))
        self.assertNotIn("docs/adr/0007-a-new-seed.md", written)
        self.assertFalse((self.target / "docs/adr/0007-a-new-seed.md")
                         .exists())
        self.assert_gates_clean()


if __name__ == "__main__":
    unittest.main()
