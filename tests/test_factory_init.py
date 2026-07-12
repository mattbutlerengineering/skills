"""factory_init.py (manifest stamping) — fixture-tree tests.

Same discipline as test_factory_gates: every function is exercised through
its public interface against a temp fixture tree, and tests assert the
exact problem strings callers will print.
"""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import factory_init
import gates

REPO_ROOT = Path(__file__).resolve().parent.parent

# Every rel key update_manifest must record for the minimal fixture repo.
EXPECTED_RELS = {
    "templates/.github/workflows/validator.yml",
    "templates/.github/workflows/assembler.yml",
    "templates/Makefile",
    "templates/factory.json",
    "templates/tools/factory/gates.py",
    "templates/tools/factory/label_sync.py",
    "templates/tools/factory/protocol.py",
    "templates/tools/factory/validator.py",
    "templates/tools/factory/assembler.py",
}

# install_path(rel) for every manifested rel, in target-relative form.
EXPECTED_INSTALLS = {
    "templates/.github/workflows/validator.yml":
        ".github/workflows/validator.yml",
    "templates/.github/workflows/assembler.yml":
        ".github/workflows/assembler.yml",
    "templates/Makefile": "Makefile",
    "templates/factory.json": ".github/factory.json",
    "templates/tools/factory/gates.py": "tools/factory/gates.py",
    "templates/tools/factory/label_sync.py": "tools/factory/label_sync.py",
    "templates/tools/factory/protocol.py": "tools/factory/protocol.py",
    "templates/tools/factory/validator.py": "tools/factory/validator.py",
    "templates/tools/factory/assembler.py": "tools/factory/assembler.py",
}

TAMPER_PROBLEM = (
    "E: factory/templates/Makefile does not match its manifest checksum"
    " (re-run manifest update, never hand-edit)")


class FixtureTree:
    def __init__(self, root):
        self.root = Path(root)

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path


def make_factory_repo(root):
    """Minimal factory repo: a stub per mirrored root file, plugin.json, and
    two templates that are authored in place (not mirrored)."""
    tree = FixtureTree(root)
    tree.write("gates.py", "# gates stub\nGATE = 1\n")
    tree.write("protocol.py", "# protocol stub\nPROTOCOL = 1\n")
    tree.write("label_sync.py", "# label_sync stub\nLABEL_SYNC = 1\n")
    tree.write("validator.py", "# validator stub\nVALIDATOR = 1\n")
    tree.write("assembler.py", "# assembler stub\nASSEMBLER = 1\n")
    tree.write(".github/workflows/validator.yml",
               "name: validator\njobs: {}\n")
    tree.write(".github/workflows/assembler.yml",
               "name: assembler\njobs: {}\n")
    tree.write(".claude-plugin/plugin.json",
               json.dumps({"name": "software-factory", "version": "1.2.3"}))
    tree.write("factory/templates/Makefile",
               "check:\n\tpython3 tools/factory/gates.py\n")
    tree.write("factory/templates/factory.json",
               json.dumps({"wip_cap": 3}))
    return tree


def all_files(root):
    """Every file under root, as sorted forward-slash relative paths."""
    return sorted(str(p.relative_to(root)).replace("\\", "/")
                  for p in Path(root).rglob("*") if p.is_file())


class TestUpdateManifest(unittest.TestCase):
    def test_happy_path_writes_manifest_and_syncs(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = make_factory_repo(tmp)
            self.assertEqual(factory_init.update_manifest(tree.root), [])
            manifest = json.loads(
                (tree.root / "factory/manifest.json").read_text(
                    encoding="utf-8"))
            self.assertEqual(manifest["plugin"], "software-factory")
            self.assertEqual(manifest["version"], "1.2.3")
            self.assertEqual(set(manifest["files"]), EXPECTED_RELS)
            for rel, digest in manifest["files"].items():
                path = tree.root / "factory" / rel
                self.assertEqual(
                    digest, hashlib.sha256(path.read_bytes()).hexdigest(),
                    f"stale sha256 for {rel}")
            self.assertEqual(gates.check_scaffold_sync(tree.root), [])

    def test_every_mirrored_root_file_lands_verbatim_in_the_payload(self):
        """The payload is machine-copied from the repo root, so a stamped
        product repo runs the same tools and the same CI as this one."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = make_factory_repo(tmp)
            self.assertEqual(factory_init.update_manifest(tree.root), [])
            for name, rel in factory_init.MIRRORS.items():
                self.assertEqual(
                    (tree.root / "factory" / "templates" / rel).read_bytes(),
                    (tree.root / name).read_bytes(),
                    f"{name} is not mirrored verbatim to templates/{rel}")

    def test_recomputes_after_template_edit(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = make_factory_repo(tmp)
            self.assertEqual(factory_init.update_manifest(tree.root), [])
            tree.write("factory/templates/Makefile", "check: tampered\n")
            self.assertEqual(gates.check_scaffold_sync(tree.root),
                             [TAMPER_PROBLEM])
            self.assertEqual(factory_init.update_manifest(tree.root), [])
            self.assertEqual(gates.check_scaffold_sync(tree.root), [])

    def test_missing_plugin_json_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = make_factory_repo(tmp)
            (tree.root / ".claude-plugin/plugin.json").unlink()
            self.assertEqual(
                factory_init.update_manifest(tree.root),
                ["factory-init: missing .claude-plugin/plugin.json"])
            self.assertFalse((tree.root / "factory/manifest.json").exists())

    def test_missing_root_tool_file_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = make_factory_repo(tmp)
            (tree.root / "protocol.py").unlink()
            self.assertEqual(
                factory_init.update_manifest(tree.root),
                ["factory-init: missing protocol.py at repo root"])
            self.assertFalse((tree.root / "factory/manifest.json").exists())
            self.assertFalse(
                (tree.root / "factory/templates/tools").exists())


class TestInstallPath(unittest.TestCase):
    def test_factory_json_installs_under_dot_github(self):
        self.assertEqual(factory_init.install_path("templates/factory.json"),
                         ".github/factory.json")

    def test_makefile_installs_at_root(self):
        self.assertEqual(factory_init.install_path("templates/Makefile"),
                         "Makefile")

    def test_nested_tool_strips_templates_prefix(self):
        self.assertEqual(
            factory_init.install_path("templates/tools/factory/gates.py"),
            "tools/factory/gates.py")


class TestStamp(unittest.TestCase):
    def manifested_source(self, tmp):
        source = Path(tmp) / "source"
        tree = make_factory_repo(source)
        assert factory_init.update_manifest(tree.root) == []
        return tree.root

    def test_happy_path_installs_copies_and_pristine_mirror(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = self.manifested_source(tmp)
            target = Path(tmp) / "target"
            target.mkdir()
            self.assertEqual(factory_init.stamp(source, target), [])
            for rel, dest in EXPECTED_INSTALLS.items():
                self.assertTrue((target / dest).is_file(),
                                f"missing installed copy {dest}")
                self.assertEqual((target / dest).read_bytes(),
                                 (source / "factory" / rel).read_bytes(),
                                 f"installed copy {dest} is not verbatim")
                self.assertTrue((target / "factory" / rel).is_file(),
                                f"missing pristine mirror factory/{rel}")
            self.assertTrue((target / "factory/manifest.json").is_file())
            self.assertEqual((target / "factory/manifest.json").read_bytes(),
                             (source / "factory/manifest.json").read_bytes())
            self.assertEqual(gates.check_scaffold_sync(target), [])

    def test_refuses_drifted_source_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = self.manifested_source(tmp)
            (source / "factory/templates/Makefile").write_text(
                "check: tampered\n", encoding="utf-8")
            self.assertEqual(gates.check_scaffold_sync(source),
                             [TAMPER_PROBLEM])
            target = Path(tmp) / "target"
            target.mkdir()
            self.assertEqual(factory_init.stamp(source, target),
                             [TAMPER_PROBLEM])
            self.assertEqual(all_files(target), [])

    def test_refuses_existing_destination_without_partial_stamp(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = self.manifested_source(tmp)
            target = Path(tmp) / "target"
            tree = FixtureTree(target)
            tree.write("Makefile", "pre-existing\n")
            self.assertEqual(
                factory_init.stamp(source, target),
                ["factory-init: target already has Makefile"])
            self.assertEqual((target / "Makefile").read_text(
                encoding="utf-8"), "pre-existing\n")
            self.assertEqual(all_files(target), ["Makefile"])


class TestAcceptanceStampRealRepo(unittest.TestCase):
    def test_stamped_repo_passes_its_own_gates(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "product"
            (target / ".git").mkdir(parents=True)
            self.assertEqual(factory_init.stamp(REPO_ROOT, target), [])
            result = subprocess.run(
                [sys.executable, "tools/factory/gates.py"],
                cwd=target, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0,
                             f"gates failed in stamped repo:\n"
                             f"{result.stdout}\n{result.stderr}")
            self.assertIn("gates: 0 problem(s)", result.stdout)


if __name__ == "__main__":
    unittest.main()
