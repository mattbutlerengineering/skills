"""Factory gate detectors (gates.py) — fixture-tree tests.

Same discipline as test_lint_checkers: every checker is exercised through
its public interface against a temp fixture tree, and tests assert the
exact problem strings callers will print.
"""
import contextlib
import hashlib
import io
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

    def test_closes_link_is_case_insensitive(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = self.pr_env(tmp, "WO-0003: detector B",
                              "WO-0003 per breakdown; closes #7")
            self.assertEqual(
                gates.check_pr_traceability(Path(tmp), env=env), [])

    def test_exempt_title_is_clean_but_logged(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = self.pr_env(tmp, "[factory-exempt] bump deps", "")
            log = io.StringIO()
            with contextlib.redirect_stdout(log):
                problems = gates.check_pr_traceability(Path(tmp), env=env)
            self.assertEqual(problems, [])
            self.assertEqual(log.getvalue(),
                             "B: factory-exempt PR (logged)\n")


class TestLockstep(unittest.TestCase):
    """Makefile <-> CI lockstep (origin: WO-0003): the canonical check set
    in .github/workflows/checks.yml and the stamped product-repo Makefile
    template must not drift apart silently."""

    REPO = Path(__file__).resolve().parents[1]

    def test_ci_workflow_runs_the_canonical_check_set(self):
        text = (self.REPO / ".github" / "workflows"
                / "checks.yml").read_text(encoding="utf-8")
        for command in ("python3 lint.py",
                        "python3 gates.py",
                        "python3 gates.py --selftest",
                        "python3 -m unittest discover tests"):
            self.assertIn(command, text)

    def test_template_makefile_check_target_matches_ci(self):
        text = (self.REPO / "factory" / "templates"
                / "Makefile").read_text(encoding="utf-8")
        for command in ("python3 tools/factory/gates.py",
                        "python3 tools/factory/gates.py --selftest",
                        "python3 -m unittest discover"):
            self.assertIn(command, text)


class TestSelftest(unittest.TestCase):
    def test_selftest_passes(self):
        self.assertEqual(gates.selftest(), 0)


if __name__ == "__main__":
    unittest.main()
