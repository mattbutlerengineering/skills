"""Factory gate detectors (gates.py) — fixture-tree tests.

Same discipline as test_lint_checkers: every checker is exercised through
its public interface against a temp fixture tree, and tests assert the
exact problem strings callers will print.
"""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import gates


class FixtureTree:
    def __init__(self, root):
        self.root = Path(root)

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path


class TestWoCitation(unittest.TestCase):
    def test_uncited_row_is_flagged_and_cited_row_is_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("docs/features/demo/breakdown.md",
                       "- [ ] WO-0001 slice one (PRD-0001 §Solution)\n"
                       "- [ ] WO-0002 uncited\n")
            problems = gates.check_wo_citation(tree.root)
            self.assertEqual(problems, [
                "A: docs/features/demo/breakdown.md:2 work-order row"
                " WO-0002 cites no PRD id"])


class TestLinkIntegrity(unittest.TestCase):
    def build(self, tmp):
        tree = FixtureTree(tmp)
        tree.write("docs/features/demo/prd.md",
                   "---\nstage: prd\nid: PRD-0001\n---\n# PRD\n")
        tree.write("docs/adr/0001-real.md", "# Real\n")
        return tree

    def test_resolving_tokens_are_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.build(tmp)
            tree.write("docs/features/demo/breakdown.md",
                       "- [ ] WO-0001 slice (PRD-0001 §Solution)\n")
            tree.write("CONTEXT.md", "PRD-0001 per ADR-0001, see WO-0001.\n")
            self.assertEqual(gates.check_link_integrity(tree.root), [])

    def test_dangling_tokens_are_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.build(tmp)
            tree.write("CONTEXT.md", "PRD-0099 and ADR-0042 and WO-0003.\n")
            self.assertEqual(gates.check_link_integrity(tree.root), [
                "C: CONTEXT.md:1 dangling PRD-0099"
                " (no prd.md declares this id)",
                "C: CONTEXT.md:1 dangling ADR-0042 (no docs/adr file)",
                "C: CONTEXT.md:1 dangling WO-0003 (no breakdown row)"])

    def test_duplicate_prd_id_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.build(tmp)
            tree.write("docs/features/other/prd.md",
                       "---\nstage: prd\nid: PRD-0001\n---\n# PRD\n")
            problems = gates.check_link_integrity(tree.root)
            self.assertEqual(problems, [
                "C: duplicate PRD id PRD-0001 in"
                " docs/features/demo/prd.md, docs/features/other/prd.md"])


class TestScaffoldSync(unittest.TestCase):
    def manifested_tree(self, tmp, payload="check:\n"):
        tree = FixtureTree(tmp)
        path = tree.write("factory/templates/Makefile", payload)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        tree.write("factory/manifest.json",
                   json.dumps({"files": {"templates/Makefile": digest}}))
        return tree

    def test_matching_payload_is_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.manifested_tree(tmp)
            self.assertEqual(gates.check_scaffold_sync(tree.root), [])

    def test_tampered_payload_and_unmanifested_file_are_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.manifested_tree(tmp)
            tree.write("factory/templates/Makefile", "check: tampered\n")
            tree.write("factory/templates/extra.txt", "orphan\n")
            self.assertEqual(gates.check_scaffold_sync(tree.root), [
                "E: factory/templates/Makefile does not match its manifest"
                " checksum (re-run manifest update, never hand-edit)",
                "E: factory/templates/extra.txt is not in the manifest"])

    def test_missing_manifest_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(gates.check_scaffold_sync(Path(tmp)),
                             ["E: missing factory/manifest.json"])


class TestConfigShape(unittest.TestCase):
    GOOD = {"budgets_usd": {"S": 5, "M": 15, "L": 40},
            "routing": {"mechanical": "m", "implementation": "i",
                        "architecture_review": "a"},
            "wip_cap": 3, "monthly_cap_usd": 300}

    def test_valid_config_is_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("factory/templates/factory.json", json.dumps(self.GOOD))
            self.assertEqual(gates.check_config_shape(tree.root), [])

    def test_invalid_fields_are_each_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("factory/templates/factory.json", json.dumps(
                {"budgets_usd": {"S": 5}, "routing": {"mechanical": "m"},
                 "wip_cap": 0, "monthly_cap_usd": -1}))
            rel = "factory/templates/factory.json"
            self.assertEqual(gates.check_config_shape(tree.root), [
                f"F: {rel} budgets_usd must map exactly S, M, L",
                f"F: {rel} routing must map exactly mechanical,"
                " implementation, architecture_review",
                f"F: {rel} wip_cap must be a positive integer",
                f"F: {rel} monthly_cap_usd must be a positive number"])


class TestPrTraceability(unittest.TestCase):
    def event_env(self, tmp, event):
        path = Path(tmp) / "event.json"
        path.write_text(json.dumps(event), encoding="utf-8")
        return {"GITHUB_EVENT_PATH": str(path)}

    def pr_env(self, tmp, title, body):
        return self.event_env(tmp, {"pull_request":
                                    {"title": title, "body": body}})

    def test_no_event_path_skips_silently(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(
                gates.check_pr_traceability(Path(tmp), env={}), [])

    def test_non_pr_event_skips_silently(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = self.event_env(tmp, {"ref": "refs/heads/main"})
            self.assertEqual(
                gates.check_pr_traceability(Path(tmp), env=env), [])

    def test_uncited_body_fires_both_problems(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = self.pr_env(tmp, "fix: something", "no tokens here")
            self.assertEqual(
                gates.check_pr_traceability(Path(tmp), env=env), [
                    "B: PR body cites no work-order id",
                    "B: PR body has no Closes #N link"])

    def test_null_body_fires_both_problems(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = self.pr_env(tmp, "fix: something", None)
            self.assertEqual(
                gates.check_pr_traceability(Path(tmp), env=env), [
                    "B: PR body cites no work-order id",
                    "B: PR body has no Closes #N link"])

    def test_well_formed_body_is_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = self.pr_env(tmp, "WO-0003: detector B",
                              "WO-0003 (PRD-0001 §X) — Closes #108")
            self.assertEqual(
                gates.check_pr_traceability(Path(tmp), env=env), [])

    def test_every_github_closing_keyword_is_accepted(self):
        forms = ("close #7", "closes #7", "closed #7", "Closes: #7",
                 "fix #7", "fixes #7", "fixed #7", "Fixes: #7",
                 "resolve #7", "resolves #7", "resolved #7", "Resolves: #7",
                 "CLOSES  #7")
        with tempfile.TemporaryDirectory() as tmp:
            for form in forms:
                env = self.pr_env(tmp, "WO-0003: detector B",
                                  f"WO-0003 per breakdown; {form}")
                self.assertEqual(
                    gates.check_pr_traceability(Path(tmp), env=env), [],
                    f"{form!r} should be accepted as a closing keyword")

    def test_non_closing_keyword_reference_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            for form in ("see #7", "closes issue 7", "refs #7"):
                env = self.pr_env(tmp, "WO-0003: detector B",
                                  f"WO-0003 per breakdown; {form}")
                self.assertEqual(
                    gates.check_pr_traceability(Path(tmp), env=env),
                    ["B: PR body has no Closes #N link"],
                    f"{form!r} is not a closing keyword link")

    def test_unreadable_event_file_is_a_problem_not_a_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = str(Path(tmp) / "nope" / "event.json")
            problems = gates.check_pr_traceability(
                Path(tmp), env={"GITHUB_EVENT_PATH": missing})
            self.assertEqual(len(problems), 1)
            self.assertTrue(problems[0].startswith(
                f"B: cannot read GITHUB_EVENT_PATH {missing}:"), problems)

    def test_malformed_event_file_is_a_problem_not_a_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "event.json"
            path.write_text("{not json", encoding="utf-8")
            problems = gates.check_pr_traceability(
                Path(tmp), env={"GITHUB_EVENT_PATH": str(path)})
            self.assertEqual(len(problems), 1)
            self.assertTrue(problems[0].startswith(
                f"B: cannot read GITHUB_EVENT_PATH {path}:"), problems)


class TestRunAll(unittest.TestCase):
    def test_run_all_threads_env_to_the_pr_detector(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            event = tree.write("event.json", json.dumps(
                {"pull_request": {"title": "x", "body": "nothing"}}))
            problems = gates.run_all(
                tree.root, env={"GITHUB_EVENT_PATH": str(event)})
            self.assertIn("B: PR body cites no work-order id", problems)

    def test_run_all_with_empty_env_skips_the_pr_detector(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            self.assertEqual(
                [p for p in gates.run_all(tree.root, env={})
                 if p.startswith("B:")], [])


def make_recipe(text, target):
    """The command lines of one make target (tab-indented recipe lines)."""
    lines, capturing = [], False
    for line in text.splitlines():
        if line.startswith(f"{target}:"):
            capturing = True
        elif capturing:
            if line.startswith("\t"):
                lines.append(line.strip())
            elif line.strip():
                break
    return lines


def product_form(command):
    """A root command as its product-repo twin spells it: the factory tools
    live under tools/factory/ there, and the stamped test run is quiet."""
    return (command.replace("python3 gates.py", "python3 tools/factory/gates.py")
            .replace("python3 validator.py", "python3 tools/factory/validator.py")
            .replace("unittest discover tests", "unittest discover -q tests"))


class TestLockstep(unittest.TestCase):
    """Makefile <-> CI lockstep (origin: WO-0003, tightened by WO-0004).

    The old version asserted *membership* — every canonical command appears
    somewhere — so drift by ADDITION was invisible: a step added to CI and
    not to the Makefile passed. These assert exact, ordered equality of the
    command sets, and that the workflow names no command of its own (it goes
    through `make`), which is what lets one workflow file serve both this
    repo and every stamped product repo."""

    REPO = Path(__file__).resolve().parents[1]
    WORKFLOW = REPO / ".github" / "workflows" / "validator.yml"
    PAYLOAD_WORKFLOW = (REPO / "factory" / "templates" / ".github"
                        / "workflows" / "validator.yml")
    MAKEFILE = REPO / "Makefile"
    TEMPLATE_MAKEFILE = REPO / "factory" / "templates" / "Makefile"

    # The one canonical check set. `lint.py` is the plugin's structural lint
    # and has no product-repo counterpart, so only the root Makefile runs it.
    CANONICAL_CHECK = ["python3 gates.py",
                       "python3 gates.py --selftest",
                       "python3 -m unittest discover tests"]
    ROOT_ONLY_CHECK = ["python3 lint.py"]
    VALIDATOR_TARGETS = {
        "review": ["python3 validator.py review --findings $(FINDINGS)"
                   " --status $(STATUS)"],
        "wo-merged": ["python3 validator.py lifecycle --label wo:merged"],
    }

    def recipes(self, path, target):
        return make_recipe(path.read_text(encoding="utf-8"), target)

    def test_root_makefile_check_is_exactly_the_canonical_set(self):
        self.assertEqual(self.recipes(self.MAKEFILE, "check"),
                         self.ROOT_ONLY_CHECK + self.CANONICAL_CHECK)

    def test_template_makefile_check_is_exactly_the_canonical_set(self):
        self.assertEqual(self.recipes(self.TEMPLATE_MAKEFILE, "check"),
                         [product_form(c) for c in self.CANONICAL_CHECK])

    def test_both_makefiles_expose_the_same_validator_targets(self):
        for target, commands in self.VALIDATOR_TARGETS.items():
            self.assertEqual(self.recipes(self.MAKEFILE, target), commands,
                             f"root Makefile target {target}")
            self.assertEqual(
                self.recipes(self.TEMPLATE_MAKEFILE, target),
                [product_form(c) for c in commands],
                f"template Makefile target {target}")

    def test_the_workflow_names_no_command_of_its_own(self):
        """Every check runs through `make`, so CI cannot drift from the local
        gate by adding a step — there is nowhere to add one."""
        text = self.WORKFLOW.read_text(encoding="utf-8")
        for command in ("make check", "make review", "make wo-merged"):
            self.assertIn(command, text)
        for tool in ("lint.py", "gates.py", "validator.py", "unittest"):
            self.assertNotIn(
                f"python3 {tool}", text,
                f"{tool} is invoked directly in CI; it belongs in a make"
                " target, or the two repos' CI will diverge")

    def test_the_payload_workflow_is_the_mirror_of_this_repo_s(self):
        """One workflow, two repos: the payload copy is a machine mirror
        (factory_init update-manifest), never a hand-maintained fork."""
        self.assertEqual(self.PAYLOAD_WORKFLOW.read_bytes(),
                         self.WORKFLOW.read_bytes())

    def test_the_merged_label_job_fires_only_on_a_merged_pull_request(self):
        text = self.WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("github.event.action == 'closed'", text)
        self.assertIn("github.event.pull_request.merged == true", text)


class TestSelftest(unittest.TestCase):
    def test_selftest_passes(self):
        self.assertEqual(gates.selftest(), 0)


if __name__ == "__main__":
    unittest.main()
