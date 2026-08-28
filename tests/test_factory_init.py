"""factory_init.py (manifest stamping) — fixture-tree tests.

Same discipline as test_gates: every function is exercised through
its public interface against a temp fixture tree, and tests assert the
exact problem strings callers will print. One deliberate exception: stamp's
defense-in-depth refusals are unreachable through an honest tree (the
manifest walk cannot emit a malformed key), so those tests patch the
checksum gate or INSTALL_MAP to reach the branch — stamp itself is still
driven through its public interface.
"""
import collections
import hashlib
import json
import re
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
    "templates/.github/workflows/toolsmith-mine.yml",
    "templates/Makefile",
    "templates/factory.json",
    "templates/tools/factory/gates.py",
    "templates/tools/factory/work_queue.py",
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
    "templates/tools/factory/human_gates.py",
    "templates/tools/factory/gate_digest.py",
    "templates/tools/factory/rejection_mining.py",
}

SEEDED_ADRS = REPO_ROOT / "factory" / "templates" / "docs" / "adr"

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


class TestPayloadToolsImport(unittest.TestCase):
    """Every mirrored tool must IMPORT inside the payload tree (#305).

    TestRealTreeMirrors pins that each mirrored file matches its root
    twin, and the acceptance stamp drives `make check` — but `check`
    names only some of the targets, so a mirrored tool reached by any
    other target (`toolsmith-mine`) had nothing importing it. That is
    exactly how rejection_mining.py shipped for days importing
    `sweeps`, a module MIRRORS does not carry: the root import resolved,
    the payload import could not, and the failure waited for a
    scheduled run to surface.

    Each import runs in its own interpreter with the payload directory
    as sys.path[0], so a root module of the same name can never satisfy
    it.
    """

    REPO = Path(__file__).resolve().parents[1]

    def payload_modules(self):
        for _, rel, _ in factory_init.MIRRORS:
            path = Path(rel)
            if path.suffix == ".py":
                yield path

    def test_every_mirrored_tool_imports_from_the_payload_tree(self):
        modules = list(self.payload_modules())
        self.assertTrue(modules, "MIRRORS carries no python tools")
        for rel in modules:
            with self.subTest(module=rel.as_posix()):
                directory = self.REPO / "factory" / "templates" / rel.parent
                # -B: importing inside the payload would otherwise drop
                # __pycache__/*.pyc into the mirrored tree, and the next
                # update-manifest would checksum them in as payload.
                done = subprocess.run(
                    [sys.executable, "-B", "-c", f"import {rel.stem}"],
                    cwd=directory, capture_output=True, text=True)
                self.assertEqual(
                    done.returncode, 0,
                    f"factory/templates/{rel.as_posix()} does not import"
                    f" inside the payload:\n{done.stderr}")


class TestProductForm(unittest.TestCase):
    """The per-command root->product respelling. Public on purpose:
    product_makefile generates the payload Makefile through it, and
    TestLockstep (tests/test_gates.py) asserts both Makefiles'
    command sets against it — never a test-private copy."""

    def test_the_named_factory_tools_move_under_tools_factory(self):
        """The tools a Makefile target actually invokes today. The rule
        itself — every root file MIRRORS moves — is asserted over MIRRORS
        in TestTheRespellingHasOneOwner; this stays as the readable
        statement of what the respelling looks like."""
        for tool in ("gates.py", "validator.py", "assembler.py",
                     "budget_guard.py", "cost_report.py", "gate_digest.py",
                     "rejection_mining.py"):
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


class TestTheRespellingHasOneOwner(unittest.TestCase):
    """MIRRORS says where a root file lives in a stamped repo, and
    product_form is the only thing that rewrites a command to match. The
    two must not be able to disagree — a command product_form does not
    respell names a root-level file the stamped repo does not have, and
    the target fails in someone else's repo.

    MIRRORS' own comment states the invariant as a claim about the root
    Makefile ("no target invokes it"). These are its enforcement.
    TestLockstep cannot be: it asserts the payload Makefile against
    `product_form(...)` of the same commands, so the expectation is
    computed by the function under test.
    """

    ROOT_MAKEFILE = REPO_ROOT / "Makefile"
    PAYLOAD_MAKEFILE = REPO_ROOT / "factory" / "templates" / "Makefile"

    # The one root command deliberately absent from the payload: the
    # plugin's structural lint has no product-repo counterpart, so
    # product_makefile drops the line rather than respelling it.
    DROPPED = ("lint.py",)

    @staticmethod
    def payload_tools():
        """(root name, payload path) for every root file MIRRORS moves —
        derived here the same way product_form derives it, so the test
        states the rule rather than re-typing its output."""
        return [(name, rel) for name, rel, _ in factory_init.MIRRORS
                if "/" not in name and rel != name]

    @staticmethod
    def recipe_commands(text):
        """Every tab-indented recipe line in a Makefile, target-agnostic."""
        return [line.strip() for line in text.splitlines()
                if line.startswith("\t")]

    def test_every_root_tool_mirrors_moves_is_respelled(self):
        tools = self.payload_tools()
        self.assertIn(("work_queue.py", "tools/factory/work_queue.py"),
                      tools, "the derivation must cover the whole payload,"
                             " not the subset a hand-typed list happened"
                             " to carry")
        for name, rel in tools:
            with self.subTest(tool=name):
                self.assertEqual(
                    factory_init.product_form(f"python3 {name} --flag"),
                    f"python3 {rel} --flag")

    def test_a_file_mirrors_does_not_move_is_left_alone(self):
        """The Makefile mirrors to its own name, and the workflows carry a
        path in theirs — neither is a command to respell."""
        for command in ("make -f Makefile check",
                        "python3 .github/workflows/validator.yml"):
            with self.subTest(command=command):
                self.assertEqual(factory_init.product_form(command), command)

    def test_every_root_makefile_command_is_respelled_or_dropped(self):
        """The claim MIRRORS' comment makes, asserted against the real
        root Makefile: a target naming a tool product_form does not know
        would be copied into the payload verbatim."""
        text = self.ROOT_MAKEFILE.read_text(encoding="utf-8")
        for command in self.recipe_commands(text):
            for name in re.findall(r"python3 (\S+\.py)", command):
                if name in self.DROPPED or "/" in name:
                    continue
                with self.subTest(command=command):
                    self.assertNotIn(
                        f"python3 {name}", factory_init.product_form(command),
                        f"{name} is invoked by the root Makefile but"
                        " product_form leaves it at the root; the stamped"
                        " repo has it under tools/factory/")

    def test_the_payload_makefile_names_no_root_level_tool(self):
        """The same claim from the other end, over the generated file that
        actually ships."""
        text = self.PAYLOAD_MAKEFILE.read_text(encoding="utf-8")
        bare = [command for command in self.recipe_commands(text)
                if re.search(r"python3 [^/\s]+\.py", command)]
        self.assertEqual(bare, [])


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


class TestInstallDestinationLockstep(unittest.TestCase):
    """gates.install_destination must agree with factory_init.install_path.

    Detector E's stamped half compares each pristine payload file to where
    it installs — and it runs inside stamped repos, which have no
    factory_init.py to import (it is not in MIRRORS, so the stamp never
    lands it). The mapping is therefore stated twice, and only a test can
    keep the two statements from drifting.

    Scoped to the keys E actually compares (gates.PRISTINE_PREFIXES): a
    future INSTALL_MAP entry redirecting a tool or a workflow still fails
    here, while gates stays free of a mapping it has no use for.
    """

    def pristine_keys(self):
        manifest = json.loads(
            (REPO_ROOT / "factory" / "manifest.json").read_text(
                encoding="utf-8"))
        keys = [rel for rel in sorted(manifest["files"])
                if rel.startswith(gates.PRISTINE_PREFIXES)]
        assert keys, "no pristine payload keys — the scoping is wrong"
        return keys

    def test_both_agree_on_every_pristine_payload_key(self):
        for rel in self.pristine_keys():
            with self.subTest(rel=rel):
                self.assertEqual(gates.install_destination(rel),
                                 factory_init.install_path(rel)[0])

    def test_the_pristine_set_is_the_tools_and_the_workflows(self):
        # the scoping decision itself: seeds and config are the repo's to
        # edit, so E must not compare them (docs/adr, docs/design,
        # factory.json, CODEOWNERS, labels.json, Makefile)
        installed = {gates.install_destination(rel)
                     for rel in self.pristine_keys()}
        self.assertTrue(
            all(d.startswith(("tools/factory/", ".github/workflows/"))
                for d in installed), sorted(installed))
        self.assertEqual(
            [rel for rel in ("templates/Makefile", "templates/factory.json",
                             "templates/.github/CODEOWNERS",
                             "templates/.github/labels.json")
             if rel.startswith(gates.PRISTINE_PREFIXES)], [])

    def test_both_refuse_the_same_malformed_keys(self):
        for rel in ("../../evil.sh", "/tmp/evil", "templates/../../etc/evil",
                    "templates//x", "templates/", "templates/a/../b",
                    "templates/.", "templates/./x", "templates/x\x00y"):
            with self.subTest(rel=rel):
                self.assertIsNone(gates.install_destination(rel))
                self.assertIsNone(factory_init.install_path(rel)[0])


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


class TestUpdate(unittest.TestCase):
    """update refreshes an already-stamped repo (issue #212).

    stamp refuses every existing destination, which left a stamped repo
    unable to take any factory change — including a fix to the integrity
    gate itself. update splits the payload where detector E does: the
    executable half is the factory's and gets overwritten, the rest is the
    repo's and is never written over.
    """

    def stamped(self, tmp):
        """(source, target) with target already stamped from source."""
        source = Path(tmp) / "source"
        tree = make_factory_repo(source)
        assert factory_init.update_manifest(tree.root) == []
        target = Path(tmp) / "target"
        target.mkdir()
        assert factory_init.stamp(tree.root, target) == []
        return tree.root, target

    def test_the_executable_payload_is_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, target = self.stamped(tmp)
            (target / "tools/factory/gates.py").write_text(
                "# hand-edited\n", encoding="utf-8")
            written, kept, problems = factory_init.update(source, target)
            self.assertEqual(problems, [])
            self.assertEqual(kept, [])
            self.assertIn("tools/factory/gates.py", written)
            self.assertEqual(
                (target / "tools/factory/gates.py").read_bytes(),
                (source / "factory/templates/tools/factory/gates.py"
                 ).read_bytes())

    def test_an_edited_config_file_is_kept_and_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, target = self.stamped(tmp)
            mine = json.dumps({"wip_cap": 7})
            (target / ".github/factory.json").write_text(
                mine, encoding="utf-8")
            written, kept, _ = factory_init.update(source, target)
            self.assertEqual(kept, [".github/factory.json"])
            self.assertNotIn(".github/factory.json", written)
            self.assertEqual(
                (target / ".github/factory.json").read_text(encoding="utf-8"),
                mine)

    def test_an_unchanged_config_file_is_neither_written_nor_reported(self):
        # cry-wolf guard: the normal case is a repo whose config still
        # matches, and it must not show up in either list
        with tempfile.TemporaryDirectory() as tmp:
            source, target = self.stamped(tmp)
            written, kept, _ = factory_init.update(source, target)
            self.assertEqual(kept, [])
            self.assertNotIn(".github/factory.json", written)

    def test_a_payload_file_the_target_lacks_is_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, target = self.stamped(tmp)
            (source / "factory/templates/docs/adr").mkdir(parents=True)
            (source / "factory/templates/docs/adr/0001-seed.md").write_text(
                "seed\n", encoding="utf-8")
            self.assertEqual(factory_init.update_manifest(source), [])
            written, kept, _ = factory_init.update(source, target)
            self.assertIn("docs/adr/0001-seed.md", written)
            self.assertEqual(kept, [])
            self.assertTrue((target / "docs/adr/0001-seed.md").is_file())

    def test_a_never_stamped_tree_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, _ = self.stamped(tmp)
            fresh = Path(tmp) / "fresh"
            fresh.mkdir()
            written, kept, problems = factory_init.update(source, fresh)
            self.assertEqual(
                problems, ["factory-init: target has no factory/manifest.json"
                           " — it was never stamped; run stamp, not update"])
            self.assertEqual((written, kept), ([], []))
            self.assertEqual(all_files(fresh), [])

    def test_a_drifted_source_is_refused_and_nothing_is_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, target = self.stamped(tmp)
            before = {rel: (target / rel).read_bytes()
                      for rel in all_files(target)}
            (source / "factory/templates/Makefile").write_text(
                "check: tampered\n", encoding="utf-8")
            written, kept, problems = factory_init.update(source, target)
            self.assertEqual(problems, [TAMPER_PROBLEM])
            self.assertEqual((written, kept), ([], []))
            self.assertEqual({rel: (target / rel).read_bytes()
                              for rel in all_files(target)}, before)

    def test_running_it_twice_changes_nothing_the_second_time(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, target = self.stamped(tmp)
            factory_init.update(source, target)
            after_first = {rel: (target / rel).read_bytes()
                           for rel in all_files(target)}
            written, kept, problems = factory_init.update(source, target)
            self.assertEqual((kept, problems), ([], []))
            self.assertEqual({rel: (target / rel).read_bytes()
                              for rel in all_files(target)}, after_first)

    def test_a_make_target_the_refreshed_workflows_call_must_exist(self):
        # the coupling update creates: workflows are overwritten and name no
        # commands of their own, so a factory change that adds a target
        # leaves a repo calling one its Makefile never heard of
        with tempfile.TemporaryDirectory() as tmp:
            source, target = self.stamped(tmp)
            # the root file, not the mirror: update_manifest re-copies
            # root -> factory/templates, so editing the mirror is undone
            (source / ".github/workflows/assembler.yml").write_text(
                "jobs:\n  x:\n    steps:\n      - run: make wo-failed\n",
                encoding="utf-8")
            self.assertEqual(factory_init.update_manifest(source), [])
            _, _, problems = factory_init.update(source, target)
            self.assertEqual(
                problems,
                ["factory-init: workflows call `make wo-failed` but the"
                 " Makefile has no wo-failed target (add it, or re-stamp"
                 " the Makefile)"])

    def test_a_make_target_named_only_in_a_comment_is_not_a_call(self):
        # validator.yml's header explains the convention ("every step goes
        # through a `make` target"); reading that as a call would report a
        # phantom target on every update
        with tempfile.TemporaryDirectory() as tmp:
            source, target = self.stamped(tmp)
            (source / ".github/workflows/design.yml").write_text(
                "# every step goes through a make target\njobs: {}\n",
                encoding="utf-8")
            self.assertEqual(factory_init.update_manifest(source), [])
            self.assertEqual(factory_init.update(source, target)[2], [])

    def test_factory_owned_agrees_with_detector_e_s_pristine_set(self):
        # the same split stated twice — in destination terms here, in
        # manifest-key terms in gates — so they must not drift apart
        for rel in gates.PRISTINE_PREFIXES:
            with self.subTest(rel=rel):
                dest = factory_init.install_path(rel + "x.py")[0]
                self.assertTrue(factory_init.is_factory_owned(Path(dest)),
                                dest)
        for rel in ("templates/Makefile", "templates/factory.json",
                    "templates/.github/CODEOWNERS",
                    "templates/docs/adr/0001-x.md"):
            with self.subTest(rel=rel):
                dest = Path(factory_init.install_path(rel)[0])
                self.assertFalse(factory_init.is_factory_owned(dest), dest)
                self.assertFalse(rel.startswith(gates.PRISTINE_PREFIXES), rel)


class TestSeededADRs(unittest.TestCase):
    """The ADR seed a stamped repo inherits (issue #199). The acceptance
    test below proves the whole payload passes the stamped detectors; these
    name the specific rules, so a broken seed fails by its own reason rather
    than as an opaque "gates failed in stamped repo"."""

    def numbered(self):
        return sorted(SEEDED_ADRS.glob("[0-9][0-9][0-9][0-9]-*.md"))

    def test_the_seed_ships(self):
        # Deleting the seed would leave the acceptance test green — an empty
        # docs/adr passes every detector.
        self.assertTrue((SEEDED_ADRS / "README.md").is_file())
        self.assertTrue((SEEDED_ADRS / "TEMPLATE.md").is_file())
        self.assertTrue(self.numbered(), "no seeded ADRs")

    def test_every_seeded_adr_has_a_valid_status(self):
        for path in self.numbered():
            _, text = gates._adr_status(path)
            self.assertIsNotNone(text, f"{path.name} has no Status line")
            self.assertRegex(text, gates.ADR_STATUS,
                             f"{path.name} status {text!r}")

    def test_every_seeded_adr_is_indexed(self):
        index = (SEEDED_ADRS / "README.md").read_text(encoding="utf-8")
        rows = {match.group("num") for match in
                (gates.ADR_INDEX_ROW.match(line)
                 for line in index.splitlines()) if match}
        self.assertEqual({path.name[:4] for path in self.numbered()}, rows)

    def test_no_seeded_token_points_outside_the_seed(self):
        # The trap this seed is most likely to fall into: citing an upstream
        # idea-to-prod ADR by bare token. In a stamped repo that file does
        # not exist, so detector C reads it as a dangling local citation and
        # the repo's first `make check` fails on documentation it was handed.
        local = {path.name[:4] for path in self.numbered()}
        for path in [*self.numbered(), SEEDED_ADRS / "README.md",
                     SEEDED_ADRS / "TEMPLATE.md"]:
            for number in gates.ADR_TOKEN.findall(
                    path.read_text(encoding="utf-8")):
                self.assertIn(number, local,
                              f"{path.name} cites ADR-{number}, which is not"
                              " in the seed — cite upstream decisions by name"
                              " or link, never by bare token")


class TestSetupDocCounts(unittest.TestCase):
    """docs/setup.md tells a reader exactly how many files a stamp lands
    and how they group. Nothing kept those numbers true: adding
    work_queue.py to the payload meant hand-editing three of them, and a
    missed one is invisible — the doc still reads authoritative and the
    stamp still works, so the reader is the only thing that breaks.

    Every number is derivable from the manifest through the real
    install_path resolver, so this derives them and compares. Same
    direction as detector J: a documented fact about the payload with
    nothing pinning it to the payload is a fact with a shelf life.
    """

    SETUP = REPO_ROOT / "docs" / "setup.md"
    TABLE_ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*(\d+)\s*\|")
    TOTALS = re.compile(r"(\d+) files land: the (\d+)-file payload")

    def derived(self):
        """(group -> count, payload total, stamp total) from the manifest."""
        files = json.loads(
            (REPO_ROOT / "factory" / "manifest.json").read_text(
                encoding="utf-8"))["files"]
        groups = collections.Counter()
        for rel in files:
            dest, problem = factory_init.install_path(rel)
            self.assertIsNone(problem, f"{rel}: {problem}")
            parts = dest.split("/")
            if len(parts) == 1:
                groups[dest] += 1
            else:
                groups["/".join(parts[:-1]) + "/"] += 1
        payload = sum(groups.values())
        # factory/ holds the pristine mirror plus manifest.json itself.
        groups["factory/"] = len(files) + 1
        return groups, payload, payload + len(files) + 1

    LABEL_COUNT = re.compile(r"(\d+)-label taxonomy")

    def test_the_label_count_matches_the_shipped_taxonomy(self):
        """setup.md states the taxonomy's size twice, and it is the same
        kind of hand-maintained number as the payload counts: adding a
        label means remembering the doc, and forgetting leaves a doc that
        still reads authoritative. The taxonomy is what the lifecycle
        machine, the digest and the sweeps key on, so the number is one a
        reader acts on."""
        shipped = json.loads(
            (REPO_ROOT / "factory" / "templates" / ".github"
             / "labels.json").read_text(encoding="utf-8"))
        text = self.SETUP.read_text(encoding="utf-8")
        stated = self.LABEL_COUNT.findall(text)
        self.assertTrue(stated, "docs/setup.md states no label count")
        self.assertEqual(
            sorted(set(stated)), [str(len(shipped))],
            f"docs/setup.md says {sorted(set(stated))}-label taxonomy; "
            f"factory/templates/.github/labels.json ships {len(shipped)}"
            " — run the numbers or fix the doc")

    def test_the_group_table_matches_the_manifest(self):
        groups, _, _ = self.derived()
        text = self.SETUP.read_text(encoding="utf-8")
        stated = {}
        for line in text.splitlines():
            match = self.TABLE_ROW.match(line)
            if match:
                stated[match.group(1)] = int(match.group(2))
        self.assertTrue(stated, "no count table found in docs/setup.md")
        self.assertEqual(
            stated, dict(groups),
            "docs/setup.md's group table has drifted from"
            " factory/manifest.json — update the table, or the reader is"
            " told a stamp lands files it does not")

    def test_the_totals_sentence_matches_the_manifest(self):
        _, payload, stamp = self.derived()
        text = self.SETUP.read_text(encoding="utf-8")
        match = self.TOTALS.search(text)
        self.assertIsNotNone(
            match, "docs/setup.md no longer states 'N files land: the M-file"
            " payload' — this test pins that sentence")
        self.assertEqual(
            (int(match.group(1)), int(match.group(2))), (stamp, payload),
            "docs/setup.md's totals sentence has drifted from"
            " factory/manifest.json")

    def test_the_table_sums_to_the_stated_stamp_total(self):
        """Internal consistency, independent of the manifest: a table that
        matches the manifest but does not sum to the headline number still
        misleads."""
        text = self.SETUP.read_text(encoding="utf-8")
        rows = [int(match.group(2)) for match
                in (self.TABLE_ROW.match(line)
                    for line in text.splitlines()) if match]
        match = self.TOTALS.search(text)
        self.assertEqual(sum(rows), int(match.group(1)))


class TestDoctorChecklistMatchesThePayload(unittest.TestCase):
    """skills/doctor/SKILL.md recites the Makefile target set and the
    workflow list a stamp lands, and a reader takes those as the complete
    checklist. Nothing pinned them — there is not one reference to doctor
    anywhere in tests/.

    That matters more than ordinary doc drift because doctor is the
    DIAGNOSTIC. A stale checklist does not read as stale; it reads as a
    clean bill of health with a hole in it. #204 adding `wo-failed` to the
    Makefile is precisely the edit that would have done it — without the
    target in its list, doctor would report a complete target set on a repo
    whose work-order state machine has no terminal state.

    Both directions are checked. A target the payload gained and doctor
    never learned is the silent case; a target doctor still names after the
    payload dropped it sends a reader chasing a hole that is not there.
    """

    DOCTOR = REPO_ROOT / "skills" / "doctor" / "SKILL.md"
    TEMPLATES = REPO_ROOT / "factory" / "templates"
    ITEM = re.compile(r"^(\d+)\. ", re.MULTILINE)
    BACKTICKED = re.compile(r"`([^`]+)`")

    def numbered_item(self, needle):
        """The text of doctor's numbered step containing `needle`, bounded
        by the next numbered step so a later paragraph cannot leak tokens
        into the comparison."""
        text = self.DOCTOR.read_text(encoding="utf-8")
        bounds = [match.start() for match in self.ITEM.finditer(text)]
        bounds.append(len(text))
        for start, stop in zip(bounds, bounds[1:]):
            item = text[start:stop]
            if needle in item:
                return item
        self.fail(f"skills/doctor/SKILL.md has no numbered step mentioning"
                  f" {needle!r} — this test pins that step")

    def payload_targets(self):
        makefile = (self.TEMPLATES / "Makefile").read_text(encoding="utf-8")
        return {line.split(":", 1)[0]
                for line in makefile.splitlines()
                if re.match(r"^[a-z][a-z-]*:", line)}

    def test_it_names_every_make_target_the_payload_ships(self):
        item = self.numbered_item("full target set")
        named = set(self.BACKTICKED.findall(item))
        missing = sorted(self.payload_targets() - named)
        self.assertEqual(
            missing, [],
            "skills/doctor/SKILL.md does not name make target(s) the"
            " stamped Makefile ships — doctor would report a complete"
            " target set on a repo missing one")

    def test_it_names_no_make_target_the_payload_lacks(self):
        item = self.numbered_item("full target set")
        targets = self.payload_targets()
        # Only tokens shaped like a target are candidates; the step's prose
        # backticks other things (`make`, a command) that are not claims.
        claimed = {token for token in self.BACKTICKED.findall(item)
                   if re.fullmatch(r"[a-z][a-z-]*", token)
                   and token != "make"}
        self.assertEqual(
            sorted(claimed - targets), [],
            "skills/doctor/SKILL.md names make target(s) the stamped"
            " Makefile does not ship — a reader chases a hole that is not"
            " there")

    def test_it_names_exactly_the_workflows_the_payload_ships(self):
        item = self.numbered_item("workflows are present")
        named = {token for token in self.BACKTICKED.findall(item)
                 if token.endswith(".yml")}
        shipped = {path.name for path
                   in (self.TEMPLATES / ".github" / "workflows").iterdir()
                   if path.suffix == ".yml"}
        self.assertEqual(
            named, shipped,
            "skills/doctor/SKILL.md's workflow list has drifted from the"
            " stamped payload")

    def test_the_stated_workflow_count_matches(self):
        """The step leads with a number ("The five workflows"), which goes
        stale independently of the list beside it."""
        item = self.numbered_item("workflows are present")
        shipped = len([path for path
                       in (self.TEMPLATES / ".github" / "workflows").iterdir()
                       if path.suffix == ".yml"])
        words = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five",
                 6: "six", 7: "seven", 8: "eight"}
        self.assertIn(
            f"{words[shipped]} workflows", item.lower(),
            f"doctor says something other than {words[shipped]!r} workflows"
            f" while the payload ships {shipped}")


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
