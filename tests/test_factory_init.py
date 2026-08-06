"""factory_init.py (manifest stamping) — fixture-tree tests.

Same discipline as test_gates: every function is exercised through
its public interface against a temp fixture tree, and tests assert the
exact problem strings callers will print. One deliberate exception: stamp's
defense-in-depth refusals are unreachable through an honest tree (the
manifest walk cannot emit a malformed key), so those tests patch the
checksum gate or INSTALL_MAP to reach the branch — stamp itself is still
driven through its public interface.
"""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import factory_init
import gates

# discover puts tests/ on sys.path; selective package-style runs need it
# added for the sibling fixture_tree import
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cli_contract  # noqa: E402
from fixture_tree import FixtureTree  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent

# Every rel key update_manifest must record for the minimal fixture repo.
EXPECTED_RELS = {
    "templates/.github/CODEOWNERS",
    "templates/.github/workflows/validator.yml",
    "templates/.github/workflows/assembler.yml",
    "templates/.github/workflows/design.yml",
    "templates/.github/workflows/cost-report.yml",
    "templates/.github/workflows/gate-digest.yml",
    "templates/Makefile",
    "templates/factory.json",
    "templates/tools/factory/gates.py",
    "templates/tools/factory/knowledge_plane.py",
    "templates/tools/factory/cli.py",
    "templates/tools/factory/factory_config.py",
    "templates/tools/factory/cost_ledger.py",
    "templates/tools/factory/label_sync.py",
    "templates/tools/factory/protocol.py",
    "templates/tools/factory/validator.py",
    "templates/tools/factory/assembler.py",
    "templates/tools/factory/budget_guard.py",
    "templates/tools/factory/handoff.py",
    "templates/tools/factory/orientation_pack.py",
    "templates/tools/factory/cost_report.py",
    "templates/tools/factory/gate_digest.py",
}

# Hand-maintained map: the expected install destination for every
# manifested rel, in target-relative form.
EXPECTED_INSTALLS = {
    "templates/.github/CODEOWNERS": ".github/CODEOWNERS",
    "templates/.github/workflows/validator.yml":
        ".github/workflows/validator.yml",
    "templates/.github/workflows/assembler.yml":
        ".github/workflows/assembler.yml",
    "templates/.github/workflows/design.yml":
        ".github/workflows/design.yml",
    "templates/.github/workflows/cost-report.yml":
        ".github/workflows/cost-report.yml",
    "templates/Makefile": "Makefile",
    "templates/factory.json": ".github/factory.json",
    "templates/tools/factory/gates.py": "tools/factory/gates.py",
    "templates/tools/factory/knowledge_plane.py":
        "tools/factory/knowledge_plane.py",
    "templates/tools/factory/cli.py": "tools/factory/cli.py",
    "templates/tools/factory/factory_config.py":
        "tools/factory/factory_config.py",
    "templates/tools/factory/cost_ledger.py":
        "tools/factory/cost_ledger.py",
    "templates/tools/factory/label_sync.py": "tools/factory/label_sync.py",
    "templates/tools/factory/protocol.py": "tools/factory/protocol.py",
    "templates/tools/factory/validator.py": "tools/factory/validator.py",
    "templates/tools/factory/assembler.py": "tools/factory/assembler.py",
    "templates/tools/factory/budget_guard.py":
        "tools/factory/budget_guard.py",
    "templates/tools/factory/handoff.py": "tools/factory/handoff.py",
    "templates/tools/factory/orientation_pack.py":
        "tools/factory/orientation_pack.py",
    "templates/tools/factory/cost_report.py": "tools/factory/cost_report.py",
    "templates/tools/factory/gate_digest.py": "tools/factory/gate_digest.py",
}

TAMPER_PROBLEM = (
    "E: factory/templates/Makefile does not match its manifest checksum"
    " (re-run manifest update, never hand-edit)")


def make_factory_repo(root):
    """Minimal factory repo: a stub per mirrored root file (driven by
    factory_init.MIRRORS, so a newly mirrored tool is covered here without
    another hand-written stub; the Makefile and CODEOWNERS get bespoke
    stubs shaped for their transforms), plugin.json, and one template that
    is authored in place (not mirrored)."""
    tree = FixtureTree(root)
    for src, _, _ in factory_init.MIRRORS:
        stem = Path(src).stem
        if src.endswith(".py"):
            tree.write(src, f"# {stem} stub\n{stem.upper()} = 1\n")
        elif src.endswith(".yml"):
            tree.write(src, f"name: {stem}\njobs: {{}}\n")
    tree.write("Makefile",
               "# root stub header\n"
               "\n"
               "check:\n"
               "\tpython3 lint.py\n"
               "\tpython3 gates.py\n"
               "\tpython3 -m unittest discover tests\n")
    tree.write(".github/CODEOWNERS", "* @owner\n")
    tree.write(".claude-plugin/plugin.json",
               json.dumps({"name": "software-factory", "version": "1.2.3"}))
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

    def test_every_mirror_lands_as_its_transform_of_the_root_file(self):
        """The payload is machine-generated from the repo root — verbatim
        for identity entries, through product_makefile for the Makefile —
        so a stamped product repo runs the same tools and the same CI as
        this one."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = make_factory_repo(tmp)
            self.assertEqual(factory_init.update_manifest(tree.root), [])
            for name, rel, transform in factory_init.MIRRORS:
                self.assertEqual(
                    (tree.root / "factory" / "templates" / rel).read_text(
                        encoding="utf-8"),
                    transform((tree.root / name).read_text(encoding="utf-8")),
                    f"{name} does not land in templates/{rel} as its"
                    " transform of the root file")

    def test_codeowners_lands_verbatim_and_the_makefile_in_product_form(self):
        """The two twins that used to be hand-authored: CODEOWNERS is a
        byte-for-byte mirror, the Makefile is generated in product form
        (header swapped, plugin lint dropped, commands respelled)."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = make_factory_repo(tmp)
            self.assertEqual(factory_init.update_manifest(tree.root), [])
            templates = tree.root / "factory" / "templates"
            self.assertEqual(
                (templates / ".github" / "CODEOWNERS").read_bytes(),
                (tree.root / ".github" / "CODEOWNERS").read_bytes())
            self.assertEqual(
                (templates / "Makefile").read_text(encoding="utf-8"),
                factory_init.PRODUCT_MAKEFILE_HEADER + "\n"
                "check:\n"
                "\tpython3 tools/factory/gates.py\n"
                "\tpython3 -m unittest discover -q tests\n")

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


class TestRealTreeMirrors(unittest.TestCase):
    """Detector E diffs the manifest against the PAYLOAD only, so a root
    tool edited without `python3 factory_init.py update-manifest` leaves
    a stale payload self-consistent with its stale checksum: build green,
    stamped repos run old code. This pins payload <-> ROOT in this
    checkout, closing that direction in CI."""

    REPO = Path(__file__).resolve().parents[1]

    def test_every_mirrored_root_file_matches_its_payload_copy(self):
        for name, rel, transform in factory_init.MIRRORS:
            with self.subTest(mirror=name):
                self.assertEqual(
                    transform((self.REPO / name).read_text(encoding="utf-8")),
                    (self.REPO / "factory" / "templates" / rel).read_text(
                        encoding="utf-8"),
                    f"{name} differs from factory/templates/{rel} — run"
                    " python3 factory_init.py update-manifest")


class TestProductForm(unittest.TestCase):
    """The per-command root->product respelling. Public on purpose:
    product_makefile generates the payload Makefile through it, and
    TestLockstep (tests/test_gates.py) asserts both Makefiles'
    command sets against it — never a test-private copy."""

    def test_each_factory_tool_moves_under_tools_factory(self):
        for tool in ("gates.py", "validator.py", "assembler.py",
                     "cost_report.py", "gate_digest.py"):
            with self.subTest(tool=tool):
                self.assertEqual(
                    factory_init.product_form(f"python3 {tool} --flag"),
                    f"python3 tools/factory/{tool} --flag")

    def test_the_stamped_test_run_is_quiet(self):
        self.assertEqual(
            factory_init.product_form("python3 -m unittest discover tests"),
            "python3 -m unittest discover -q tests")

    def test_a_path_agnostic_command_is_untouched(self):
        command = "npx --yes playwright@1.62.1 test"
        self.assertEqual(factory_init.product_form(command), command)


class TestProductMakefile(unittest.TestCase):
    """The Makefile's MIRRORS transform — the one production statement of
    the root->product translation. Swap the root header comment for the
    product one, drop the plugin-only lint line, respell every command."""

    ROOT_TEXT = ("# The factory's canonical command set.\n"
                 "# A second header line.\n"
                 "\n"
                 ".PHONY: check\n"
                 "\n"
                 "check:\n"
                 "\tpython3 lint.py\n"
                 "\tpython3 gates.py\n"
                 "\tpython3 -m unittest discover tests\n")

    def test_swaps_the_header_drops_lint_and_respells_commands(self):
        self.assertEqual(
            factory_init.product_makefile(self.ROOT_TEXT),
            factory_init.PRODUCT_MAKEFILE_HEADER + "\n"
            ".PHONY: check\n"
            "\n"
            "check:\n"
            "\tpython3 tools/factory/gates.py\n"
            "\tpython3 -m unittest discover -q tests\n")

    def test_identity_returns_its_input_unchanged(self):
        text = "* @owner\n"
        self.assertEqual(factory_init.identity(text), text)


class TestInstallPath(unittest.TestCase):
    def test_factory_json_installs_under_dot_github(self):
        self.assertEqual(factory_init.install_path("templates/factory.json"),
                         (".github/factory.json", None))

    def test_makefile_installs_at_root(self):
        self.assertEqual(factory_init.install_path("templates/Makefile"),
                         ("Makefile", None))

    def test_nested_tool_strips_templates_prefix(self):
        self.assertEqual(
            factory_init.install_path("templates/tools/factory/gates.py"),
            ("tools/factory/gates.py", None))

    def test_a_key_outside_templates_is_refused(self):
        # The old blind slice turned '../../evil.sh' into 'vil.sh' and
        # '/tmp/evil' into 'evil' — mangled, never refused.
        for rel in ("../../evil.sh", "/tmp/evil"):
            with self.subTest(rel=rel):
                self.assertEqual(
                    factory_init.install_path(rel),
                    (None, f"factory-init: manifest key {rel!r} is not"
                           " under templates/"))

    def test_a_key_that_escapes_or_degenerates_is_refused(self):
        for rel in ("templates/../../etc/evil", "templates//x",
                    "templates/", "templates/a/../b", "templates/.",
                    "templates/./x", "templates/x\x00y"):
            with self.subTest(rel=rel):
                self.assertEqual(
                    factory_init.install_path(rel),
                    (None, f"factory-init: manifest key {rel!r} does not"
                           " resolve to a plain relative path"))


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

    def test_refuses_a_malformed_manifest_key_and_writes_nothing(self):
        # Destinations are constrained by construction, not by upstream
        # luck: even with the checksum gate out of the way, a malformed
        # key is refused before any copy.
        with tempfile.TemporaryDirectory() as tmp:
            source = self.manifested_source(tmp)
            manifest_path = source / "factory/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["files"]["templates/../../etc/evil"] = "0" * 64
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            target = Path(tmp) / "target"
            target.mkdir()
            with mock.patch.object(gates, "check_scaffold_sync",
                                   return_value=[]):
                problems = factory_init.stamp(source, target)
            self.assertEqual(problems, [
                "factory-init: manifest key 'templates/../../etc/evil'"
                " does not resolve to a plain relative path"])
            # iterdir, not just all_files: no directories either.
            self.assertEqual(list(target.iterdir()), [])

    def test_refuses_an_escaping_install_map_destination(self):
        # The source tree here is honest — only the map is poisoned — so
        # the checksum gate passes and the containment layer is what
        # refuses (install_path returns INSTALL_MAP values unvalidated).
        with tempfile.TemporaryDirectory() as tmp:
            source = self.manifested_source(tmp)
            target = Path(tmp) / "target"
            target.mkdir()
            with mock.patch.dict(factory_init.INSTALL_MAP,
                                 {"templates/factory.json": "../escape"}):
                problems = factory_init.stamp(source, target)
            self.assertEqual(problems, [
                "factory-init: destination ../escape escapes the stamp"
                " target"])
            self.assertEqual(list(target.iterdir()), [])
            # The harm this prevents is a write OUTSIDE the target.
            self.assertFalse((Path(tmp) / "escape").exists())

    def test_stamps_through_a_symlinked_target(self):
        # The containment pass resolves both sides, so a target reached
        # through a symlink compares real paths and still stamps.
        with tempfile.TemporaryDirectory() as tmp:
            source = self.manifested_source(tmp)
            real = Path(tmp) / "real"
            real.mkdir()
            link = Path(tmp) / "link"
            link.symlink_to(real, target_is_directory=True)
            self.assertEqual(factory_init.stamp(source, link), [])
            self.assertTrue((real / "Makefile").is_file())

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


class TestMain(cli_contract.CliContract, cli_contract.ReportContract,
               unittest.TestCase):
    usage_fragment = "update-manifest"
    summary_line = "factory-init: 0 problem(s)"

    def run_cli(self, argv):
        return cli_contract.capture(factory_init.main, argv)

    def clean_cli(self):
        # Stamping the real payload into an empty target is the
        # problem-free run (live-tree, like the acceptance test below).
        with tempfile.TemporaryDirectory() as tmp:
            return self.run_cli(["stamp", str(Path(tmp) / "product")])


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
