"""Design pipeline (origin: WO-0012): design.yml + the web-quality make
target + the docs/design seed shipped in the template payload.

Same discipline as test_factory_gates::TestLockstep and test_sweeps'
workflow tests: the workflow names no command of its own (every step goes
through `make`), the payload copy is a byte mirror of the root one, and the
web-quality target is identical in both Makefiles. The design-system seed the
pipeline ships is checked for presence and for where factory-init stamps it.
"""
import json
import sys
import unittest
from pathlib import Path

import factory_init

# discover puts tests/ on sys.path; selective package-style runs need it
# added for the sibling make_parse import
sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_parse import make_recipe  # noqa: E402

REPO = Path(__file__).resolve().parents[1]


def on_block(text):
    """The lines of the workflow's top-level `on:` block, dedented one level.
    Enough to assert the trigger shape without a YAML parser (stdlib only,
    like every script here)."""
    out, collecting = [], False
    for line in text.splitlines():
        if line.rstrip() == "on:":
            collecting = True
            continue
        if collecting:
            # A new top-level key (column 0, non-blank) ends the block.
            if line and not line[0].isspace():
                break
            out.append(line)
    return out


class TestDesignWorkflow(unittest.TestCase):
    WORKFLOW = REPO / ".github" / "workflows" / "design.yml"

    def setUp(self):
        self.assertTrue(self.WORKFLOW.is_file(),
                        "the design pipeline workflow must exist at the root")
        self.text = self.WORKFLOW.read_text(encoding="utf-8")

    def test_it_is_named_design(self):
        self.assertIn("name: design", self.text)

    def test_a_pr_touching_design_docs_triggers_it(self):
        # Acceptance 1: a PR touching design docs triggers the job. The
        # trigger is a pull_request path filter on docs/design/**.
        block = on_block(self.text)
        self.assertIn("  pull_request:", block)
        self.assertIn("    paths:", block)
        self.assertIn("      - docs/design/**", block)

    def test_it_only_reads_code(self):
        self.assertIn("contents: read", self.text)

    def test_the_job_runs_the_web_quality_make_target(self):
        self.assertIn("make web-quality", self.text)

    def test_the_workflow_names_no_command_of_its_own(self):
        # Every `run:` step goes through `make`, exactly like validator.yml —
        # which is what lets one workflow file serve this repo and every
        # stamped product repo. A tool invoked directly in a run step would
        # drift the two. (The header comment may describe playwright; only the
        # commands the workflow actually runs are constrained.)
        runs = [line.split("run:", 1)[1].strip()
                for line in self.text.splitlines()
                if line.strip().startswith("run:")]
        self.assertTrue(runs, "the workflow runs nothing")
        for command in runs:
            self.assertTrue(
                command.startswith("make "),
                f"run step {command!r} does not go through make")
        for token in ("python3", "npx", "npm", "playwright"):
            for command in runs:
                self.assertNotIn(
                    token, command,
                    f"{token!r} is invoked directly in a run step; it belongs"
                    " in the make target")


class TestWorkflowMirror(unittest.TestCase):
    """One workflow, two repos: the payload copy is a machine mirror
    (factory_init update-manifest), never a hand-maintained fork."""

    ROOT = REPO / ".github" / "workflows" / "design.yml"
    PAYLOAD = (REPO / "factory" / "templates" / ".github" / "workflows"
               / "design.yml")

    def test_design_yml_is_a_registered_mirror(self):
        self.assertEqual(
            factory_init.MIRRORS.get(".github/workflows/design.yml"),
            ".github/workflows/design.yml")

    def test_the_payload_workflow_is_the_byte_mirror_of_the_root_one(self):
        self.assertTrue(self.PAYLOAD.is_file(),
                        "run factory_init.py update-manifest")
        self.assertEqual(self.PAYLOAD.read_bytes(), self.ROOT.read_bytes())


class TestWebQualityTarget(unittest.TestCase):
    """The web-quality target is the design pipeline's job body. It drives
    playwright and SKIPS GRACEFULLY when the repo has no web app to test —
    the same skip-when-absent shape sweeps.yml uses for its Sentry job, so
    it never reddens CI in a repo with no web UI (this one)."""

    ROOT_MAKEFILE = REPO / "Makefile"
    TEMPLATE_MAKEFILE = REPO / "factory" / "templates" / "Makefile"

    def recipe(self, path):
        return make_recipe(path.read_text(encoding="utf-8"), "web-quality")

    def test_both_makefiles_define_web_quality(self):
        self.assertTrue(self.recipe(self.ROOT_MAKEFILE),
                        "root Makefile has no web-quality target")
        self.assertTrue(self.recipe(self.TEMPLATE_MAKEFILE),
                        "template Makefile has no web-quality target")

    def test_the_target_is_identical_in_both_makefiles(self):
        # The tools it runs (playwright, node) are path-agnostic, so unlike
        # the python targets the two copies are byte-for-byte the same.
        self.assertEqual(self.recipe(self.ROOT_MAKEFILE),
                         self.recipe(self.TEMPLATE_MAKEFILE))

    def test_the_target_drives_playwright(self):
        recipe = " ".join(self.recipe(self.ROOT_MAKEFILE))
        self.assertIn("playwright", recipe)

    def test_the_target_skips_when_there_is_no_web_app(self):
        # The guard: absent a playwright.config.*, the target prints why it is
        # skipping and exits 0 rather than failing.
        recipe = " ".join(self.recipe(self.ROOT_MAKEFILE))
        self.assertIn("playwright.config", recipe)
        self.assertIn("skip", recipe.lower())

    def test_both_makefiles_declare_the_target_phony(self):
        for path in (self.ROOT_MAKEFILE, self.TEMPLATE_MAKEFILE):
            phony = [line for line in path.read_text(encoding="utf-8")
                     .splitlines() if line.startswith(".PHONY:")]
            self.assertTrue(any("web-quality" in line for line in phony),
                            f"{path} does not mark web-quality .PHONY")


class TestDesignSeed(unittest.TestCase):
    """Acceptance 2: the design-system seed ships in the template payload, so
    a stamped repo receives docs/design/. factory-init stamps a manifest
    entry templates/X to X (INSTALL_MAP default strips the templates/
    prefix), so a seed under factory/templates/docs/design/ lands at
    docs/design/ in the product repo."""

    SEED_DIR = REPO / "factory" / "templates" / "docs" / "design"
    TEMPLATE = SEED_DIR / "TEMPLATE.md"
    DESIGN_SYSTEM = SEED_DIR / "design-system.md"

    def test_the_design_doc_template_ships_in_the_payload(self):
        self.assertTrue(self.TEMPLATE.is_file(),
                        "no design-doc template in the payload")

    def test_the_design_system_seed_ships_in_the_payload(self):
        self.assertTrue(self.DESIGN_SYSTEM.is_file(),
                        "no design-system seed in the payload")

    def test_the_seed_is_pinned_by_the_manifest(self):
        manifest = json.loads(
            (REPO / "factory" / "manifest.json").read_text(encoding="utf-8"))
        files = manifest.get("files", {})
        self.assertIn("templates/docs/design/TEMPLATE.md", files)
        self.assertIn("templates/docs/design/design-system.md", files)

    def test_the_seed_stamps_into_docs_design(self):
        self.assertEqual(
            factory_init.install_path("templates/docs/design/TEMPLATE.md"),
            "docs/design/TEMPLATE.md")
        self.assertEqual(
            factory_init.install_path(
                "templates/docs/design/design-system.md"),
            "docs/design/design-system.md")


if __name__ == "__main__":
    unittest.main()
